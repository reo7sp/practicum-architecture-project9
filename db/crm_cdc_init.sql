DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cdc_admin') THEN
        CREATE USER cdc_admin WITH REPLICATION PASSWORD 'cdc_password';
    END IF;
END;
$$;

GRANT CONNECT ON DATABASE crm_db TO cdc_admin;
GRANT USAGE ON SCHEMA public TO cdc_admin;
GRANT SELECT ON TABLE public.crm_clients TO cdc_admin;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'crm_pub') THEN
        CREATE PUBLICATION crm_pub FOR TABLE public.crm_clients;
    END IF;
END;
$$;
