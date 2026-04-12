import requests

from config import (
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET,
    KEYCLOAK_INTERNAL_URL,
    KEYCLOAK_REALM,
)
from store import Session


http_client = requests.Session()


def token_request(payload: dict[str, str]) -> dict:
    payload["client_secret"] = KEYCLOAK_CLIENT_SECRET
    response = http_client.post(
        f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
        data=payload,
        timeout=15,
    )
    response.raise_for_status()

    return response.json()


def revoke_refresh_token(session_store, record: Session) -> None:
    refresh_token = session_store.fernet.decrypt(record.encrypted_refresh_token).decode("utf-8")
    payload = {
        "client_id": KEYCLOAK_CLIENT_ID,
        "refresh_token": refresh_token,
        "client_secret": KEYCLOAK_CLIENT_SECRET,
    }
    http_client.post(
        f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/revoke",
        data=payload,
        timeout=15,
    )
