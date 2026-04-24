CREATE TABLE IF NOT EXISTS telemetry_events (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    prosthesis_id TEXT NOT NULL,
    event_at TIMESTAMPTZ NOT NULL,
    steps INTEGER NOT NULL,
    active_minutes INTEGER NOT NULL,
    battery_level NUMERIC(5,2) NOT NULL
);

INSERT INTO telemetry_events (username, prosthesis_id, event_at, steps, active_minutes, battery_level)
VALUES
    ('user1', 'prosthesis-a1', '2026-04-10T08:00:00Z', 5200, 72, 84.5),
    ('user1', 'prosthesis-a1', '2026-04-11T08:00:00Z', 6100, 80, 82.1),
    ('user1', 'prosthesis-a1', '2026-04-12T08:00:00Z', 4800, 65, 79.4),
    ('admin1', 'prosthesis-b1', '2026-04-10T09:30:00Z', 3200, 44, 88.0),
    ('admin1', 'prosthesis-b1', '2026-04-11T09:30:00Z', 3900, 49, 86.7),
    ('prothetic1', 'prosthesis-c1', '2026-04-10T11:15:00Z', 7600, 95, 77.8),
    ('prothetic1', 'prosthesis-c1', '2026-04-11T11:15:00Z', 8100, 103, 74.9),
    ('prothetic1', 'prosthesis-c1', '2026-04-12T11:15:00Z', 7900, 100, 72.3),
    ('john.doe', 'prosthesis-d1', '2026-04-11T06:45:00Z', 4400, 58, 81.0),
    ('jane.smith', 'prosthesis-e1', '2026-04-12T07:20:00Z', 5100, 67, 83.6)
ON CONFLICT DO NOTHING;
