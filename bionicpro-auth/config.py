import os

from utils import parse_duration


SESSION_COOKIE_NAME = "bionicpro_session"
STATE_COOKIE_NAME = "bionicpro_auth_state"
LISTEN_ADDR = os.getenv("LISTEN_ADDR", "0.0.0.0:8000")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
KEYCLOAK_PUBLIC_URL = os.getenv("KEYCLOAK_PUBLIC_URL", "http://localhost:8080").rstrip("/")
KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", KEYCLOAK_PUBLIC_URL).rstrip("/")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "bionicpro-auth")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
SESSION_TTL = parse_duration(os.getenv("SESSION_TTL", "30m"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAME_SITE = os.getenv("COOKIE_SAME_SITE", "Lax")
SESSION_ENCRYPTION_SECRET = os.getenv("SESSION_ENCRYPTION_SECRET", "change-me-session-encryption-secret")
PROFILE_STORE_PATH = os.getenv("PROFILE_STORE_PATH", "./data/profiles.db")
