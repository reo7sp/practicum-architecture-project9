from datetime import date

import clickhouse_connect

from config import (
    OLAP_CLICKHOUSE_DATABASE,
    OLAP_CLICKHOUSE_HOST,
    OLAP_CLICKHOUSE_PASSWORD,
    OLAP_CLICKHOUSE_PORT,
    OLAP_CLICKHOUSE_USER,
)


def get_report_context(date_from: date | None, date_to: date | None) -> dict | None:
    client = clickhouse_connect.get_client(
        host=OLAP_CLICKHOUSE_HOST,
        port=OLAP_CLICKHOUSE_PORT,
        username=OLAP_CLICKHOUSE_USER,
        password=OLAP_CLICKHOUSE_PASSWORD,
        database=OLAP_CLICKHOUSE_DATABASE,
    )

    metadata = client.query(
        """
        SELECT available_from, available_to, updated_at
        FROM etl_metadata
        WHERE pipeline_name = 'reports_mart'
        ORDER BY updated_at DESC
        LIMIT 1
        """
    ).result_rows
    if not metadata:
        return None

    available_from, available_to, updated_at = metadata[0]
    if available_from is None or available_to is None:
        return None

    requested_from = date_from or available_from
    requested_to = date_to or available_to

    if requested_from < available_from or requested_to > available_to:
        return {
            "error": "period_not_available",
            "available_from": available_from.isoformat(),
            "available_to": available_to.isoformat(),
        }

    return {
        "available_from": available_from,
        "available_to": available_to,
        "requested_from": requested_from,
        "requested_to": requested_to,
        "cache_version": updated_at.strftime("%Y%m%d%H%M%S"),
    }


def get_report_for_user(
    username: str,
    requested_from: date,
    requested_to: date,
    available_from: date,
    available_to: date,
) -> dict:
    client = clickhouse_connect.get_client(
        host=OLAP_CLICKHOUSE_HOST,
        port=OLAP_CLICKHOUSE_PORT,
        username=OLAP_CLICKHOUSE_USER,
        password=OLAP_CLICKHOUSE_PASSWORD,
        database=OLAP_CLICKHOUSE_DATABASE,
    )
    rows = client.query(
        """
        SELECT
            username,
            email,
            full_name,
            country,
            segment,
            sum(telemetry_events) AS telemetry_events,
            sum(total_steps) AS total_steps,
            sum(total_active_minutes) AS total_active_minutes,
            avg(avg_battery_level) AS avg_battery_level,
            max(last_event_at) AS last_event_at
        FROM report_mart_view
        WHERE username = %(username)s
          AND report_date BETWEEN %(date_from)s AND %(date_to)s
        GROUP BY username, email, full_name, country, segment
        """,
        parameters={
            "username": username,
            "date_from": requested_from,
            "date_to": requested_to,
        },
    ).result_rows
    if not rows:
        return {
            "error": "report_not_found",
            "available_from": available_from.isoformat(),
            "available_to": available_to.isoformat(),
        }

    row = rows[0]

    return {
        "username": row[0],
        "email": row[1],
        "full_name": row[2],
        "country": row[3],
        "segment": row[4],
        "telemetry_events": row[5],
        "total_steps": row[6],
        "total_active_minutes": row[7],
        "avg_battery_level": float(row[8]),
        "last_event_at": row[9].isoformat(),
        "requested_from": requested_from.isoformat(),
        "requested_to": requested_to.isoformat(),
        "available_from": available_from.isoformat(),
        "available_to": available_to.isoformat(),
    }
