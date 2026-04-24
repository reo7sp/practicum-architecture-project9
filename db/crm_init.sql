CREATE TABLE IF NOT EXISTS crm_clients (
    username TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    country TEXT NOT NULL,
    segment TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO crm_clients (username, email, full_name, country, segment)
VALUES
    ('user1', 'user1@example.com', 'User One', 'RU', 'standard'),
    ('admin1', 'admin1@example.com', 'Admin One', 'RU', 'admin'),
    ('prothetic1', 'prothetic1@example.com', 'Prothetic One', 'RU', 'prosthetics'),
    ('john.doe', 'john@example.com', 'John Doe', 'US', 'foreign'),
    ('jane.smith', 'jane@example.com', 'Jane Smith', 'DE', 'foreign')
ON CONFLICT (username) DO NOTHING;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cdc_admin') THEN
        CREATE USER cdc_admin WITH REPLICATION PASSWORD 'cdc_password';
    END IF;
END;
$$;
GRANT SELECT ON crm_clients TO cdc_admin;
CREATE PUBLICATION IF NOT EXISTS crm_pub FOR TABLE crm_clients;
