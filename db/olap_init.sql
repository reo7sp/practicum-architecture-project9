CREATE DATABASE IF NOT EXISTS olap_db;

CREATE TABLE IF NOT EXISTS olap_db.report_mart_daily
(
    report_date Date,
    username String,
    email String,
    full_name String,
    country String,
    segment String,
    telemetry_events UInt32,
    total_steps UInt32,
    total_active_minutes UInt32,
    avg_battery_level Float64,
    last_event_at DateTime,
    loaded_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (username, report_date);

CREATE TABLE IF NOT EXISTS olap_db.etl_metadata
(
    pipeline_name String,
    available_from Nullable(Date),
    available_to Nullable(Date),
    updated_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY pipeline_name;

CREATE TABLE IF NOT EXISTS olap_db.kafka_crm_clients
(
    payload String
)
ENGINE = Kafka('kafka:9092', 'dbserver1.public.crm_clients', 'crm-group', 'JSONAsString');

CREATE TABLE IF NOT EXISTS olap_db.crm_clients_latest
(
    username String,
    email String,
    full_name String,
    country String,
    segment String,
    updated_at DateTime
)
ENGINE = ReplacingMergeTree
ORDER BY username;

CREATE MATERIALIZED VIEW IF NOT EXISTS olap_db.crm_clients_mv TO olap_db.crm_clients_latest AS
SELECT
    JSONExtractString(payload, 'after.username') AS username,
    JSONExtractString(payload, 'after.email') AS email,
    JSONExtractString(payload, 'after.full_name') AS full_name,
    JSONExtractString(payload, 'after.country') AS country,
    JSONExtractString(payload, 'after.segment') AS segment,
    now() AS updated_at
FROM olap_db.kafka_crm_clients
WHERE JSONExtractString(payload, 'after.username') != '';

CREATE TABLE IF NOT EXISTS olap_db.report_mart_view
(
    report_date Date,
    username String,
    email String,
    full_name String,
    country String,
    segment String,
    telemetry_events UInt32,
    total_steps UInt32,
    total_active_minutes UInt32,
    avg_battery_level Float64,
    last_event_at DateTime
)
ENGINE = MergeTree
ORDER BY (username, report_date);

CREATE MATERIALIZED VIEW IF NOT EXISTS olap_db.report_mart_view_mv TO olap_db.report_mart_view AS
SELECT
    rd.report_date,
    rd.username,
    coalesce(c.email, rd.email) AS email,
    coalesce(c.full_name, rd.full_name) AS full_name,
    coalesce(c.country, rd.country) AS country,
    coalesce(c.segment, rd.segment) AS segment,
    rd.telemetry_events,
    rd.total_steps,
    rd.total_active_minutes,
    rd.avg_battery_level,
    rd.last_event_at
FROM olap_db.report_mart_daily AS rd
LEFT JOIN olap_db.crm_clients_latest AS c ON rd.username = c.username;
