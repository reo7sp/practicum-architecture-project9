from datetime import datetime
import os

import clickhouse_connect
import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator


CRM_DSN = os.getenv("CRM_DSN", "dbname=crm_db user=crm_user password=crm_password host=crm_db port=5432")
TELEMETRY_DSN = os.getenv(
    "TELEMETRY_DSN",
    "dbname=telemetry_db user=telemetry_user password=telemetry_password host=telemetry_db port=5432",
)
OLAP_CLICKHOUSE_HOST = os.getenv("OLAP_CLICKHOUSE_HOST", "olap_db")
OLAP_CLICKHOUSE_PORT = int(os.getenv("OLAP_CLICKHOUSE_PORT", "8123"))
OLAP_CLICKHOUSE_USER = os.getenv("OLAP_CLICKHOUSE_USER", "default")
OLAP_CLICKHOUSE_PASSWORD = os.getenv("OLAP_CLICKHOUSE_PASSWORD", "clickhouse_password")
OLAP_CLICKHOUSE_DATABASE = os.getenv("OLAP_CLICKHOUSE_DATABASE", "olap_db")


def sync_report_mart() -> None:
    with psycopg2.connect(CRM_DSN) as crm_conn, psycopg2.connect(TELEMETRY_DSN) as telemetry_conn:
        clickhouse = clickhouse_connect.get_client(
            host=OLAP_CLICKHOUSE_HOST,
            port=OLAP_CLICKHOUSE_PORT,
            username=OLAP_CLICKHOUSE_USER,
            password=OLAP_CLICKHOUSE_PASSWORD,
            database=OLAP_CLICKHOUSE_DATABASE,
        )
        with crm_conn.cursor() as crm_cursor, telemetry_conn.cursor() as telemetry_cursor:
            crm_cursor.execute(
                """
                SELECT username, email, full_name, country, segment
                FROM crm_clients
                """
            )
            clients = {
                row[0]: {
                    "email": row[1],
                    "full_name": row[2],
                    "country": row[3],
                    "segment": row[4],
                }
                for row in crm_cursor.fetchall()
            }

            telemetry_cursor.execute(
                """
                SELECT
                    DATE(event_at) AS report_date,
                    username,
                    COUNT(*) AS telemetry_events,
                    SUM(steps) AS total_steps,
                    SUM(active_minutes) AS total_active_minutes,
                    AVG(battery_level) AS avg_battery_level,
                    MAX(event_at) AS last_event_at
                FROM telemetry_events
                GROUP BY DATE(event_at), username
                ORDER BY DATE(event_at), username
                """
            )
            rows = telemetry_cursor.fetchall()

            available_from = None
            available_to = None
            mart_rows = []

            for row in rows:
                report_date, username, events, steps, active_minutes, avg_battery, last_event_at = row
                client = clients.get(username)
                if client is None:
                    continue

                available_from = report_date if available_from is None else min(available_from, report_date)
                available_to = report_date if available_to is None else max(available_to, report_date)
                mart_rows.append(
                    [
                        report_date,
                        username,
                        client["email"],
                        client["full_name"],
                        client["country"],
                        client["segment"],
                        events,
                        steps,
                        active_minutes,
                        float(avg_battery),
                        last_event_at,
                    ]
                )

            clickhouse.command("TRUNCATE TABLE report_mart_view")
            clickhouse.command("TRUNCATE TABLE report_mart_daily")
            clickhouse.command("TRUNCATE TABLE etl_metadata")
            if mart_rows:
                clickhouse.insert(
                    "report_mart_daily",
                    mart_rows,
                    column_names=[
                        "report_date",
                        "username",
                        "email",
                        "full_name",
                        "country",
                        "segment",
                        "telemetry_events",
                        "total_steps",
                        "total_active_minutes",
                        "avg_battery_level",
                        "last_event_at",
                    ],
                )
            clickhouse.insert(
                "etl_metadata",
                [["reports_mart", available_from, available_to]],
                column_names=["pipeline_name", "available_from", "available_to"],
            )


with DAG(
    dag_id="reports_etl",
    start_date=datetime(2026, 4, 1),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["reports", "etl", "olap"],
) as dag:
    PythonOperator(
        task_id="sync_report_mart",
        python_callable=sync_report_mart,
    )
