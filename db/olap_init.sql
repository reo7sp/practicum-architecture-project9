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
