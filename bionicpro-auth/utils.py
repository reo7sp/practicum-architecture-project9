import base64
import hashlib
import json
import secrets
from datetime import timedelta


def parse_duration(value: str) -> timedelta:
    if value.endswith("m"):
        return timedelta(minutes=int(value[:-1]))
    if value.endswith("h"):
        return timedelta(hours=int(value[:-1]))
    if value.endswith("s"):
        return timedelta(seconds=int(value[:-1]))
    raise ValueError(f"Unsupported duration format: {value}")


def random_string(length: int = 48) -> str:
    return secrets.token_urlsafe(length)[:length]


def pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def decode_jwt_claims(raw_token: str) -> dict[str, str]:
    parts = raw_token.split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(payload + padding)
    parsed = json.loads(decoded)
    claims: dict[str, str] = {}
    for key, value in parsed.items():
        if isinstance(value, (str, int, float, bool)):
            claims[key] = str(value)

    return claims
