import threading
import time
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from flask import Flask, jsonify, make_response, redirect, request

from config import (
    COOKIE_SAME_SITE,
    COOKIE_SECURE,
    FRONTEND_BASE_URL,
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_PUBLIC_URL,
    KEYCLOAK_REALM,
    LISTEN_ADDR,
    PROFILE_STORE_PATH,
    PUBLIC_BASE_URL,
    SESSION_COOKIE_NAME,
    SESSION_ENCRYPTION_SECRET,
    SESSION_TTL,
    STATE_COOKIE_NAME,
)
from keycloak_client import revoke_refresh_token, token_request
from olap_client import get_report_for_user
from store import Profile, ProfileStore, Session, SessionStore
from utils import decode_jwt_claims, pkce_challenge


store = SessionStore(SESSION_ENCRYPTION_SECRET, SESSION_TTL)
profiles = ProfileStore(PROFILE_STORE_PATH)
app = Flask(__name__)


def extract_profile(tokens: dict[str, str]) -> Profile:
    claims = decode_jwt_claims(tokens.get("id_token", "")) or decode_jwt_claims(tokens.get("access_token", ""))
    profile = Profile(claims={})
    for key, value in claims.items():
        if key == "sub":
            profile.subject = value
        elif key == "preferred_username":
            profile.preferred_username = value
            profile.username = value
        elif key == "email":
            profile.email = value
        elif key == "given_name":
            profile.first_name = value
        elif key == "family_name":
            profile.last_name = value
        elif key == "name":
            profile.name = value
        elif key == "identity_provider":
            profile.identity_provider = value
        elif key == "identity_provider_identity":
            profile.identity_provider_id = value
        else:
            profile.claims[key] = value
    if not profile.name:
        profile.name = " ".join(part for part in [profile.first_name, profile.last_name] if part).strip()

    return profile


def refresh_session(record: Session) -> Session:
    refresh_token = store.fernet.decrypt(record.encrypted_refresh_token).decode("utf-8")
    tokens = token_request(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": KEYCLOAK_CLIENT_ID,
        }
    )
    profile = extract_profile(tokens)
    if not profile.subject:
        profile = record.profile
    elif record.profile.identity_provider and not profile.identity_provider:
        profile.identity_provider = record.profile.identity_provider
    profiles.upsert(profile)

    record.access_token = tokens["access_token"]
    record.access_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(tokens["expires_in"]))
    record.encrypted_refresh_token = store.fernet.encrypt(tokens["refresh_token"].encode("utf-8"))
    if int(tokens.get("refresh_expires_in", 0)) > 0:
        record.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(tokens["refresh_expires_in"]))
    record.profile = profile
    record.last_refreshed_at = datetime.now(timezone.utc)

    return record


def ensure_authenticated(rotate: bool = True) -> tuple[Session | None, str | None]:
    session_id = request.cookies.get(SESSION_COOKIE_NAME, "")
    if not session_id:
        return None, None
    record = store.get_session(session_id)
    if record is None:
        return None, None
    if datetime.now(timezone.utc) >= record.access_token_expires_at - timedelta(seconds=10):
        try:
            record = refresh_session(record)
        except Exception:
            store.delete_session(session_id)
            return None, None
    if not rotate:
        return record, None
    rotated = store.rotate_session(record.session_id)
    if rotated is None:
        return None, None

    return rotated, rotated.session_id


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin == FRONTEND_BASE_URL:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Requested-With"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    return response


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"})


@app.route("/auth/login", methods=["GET"])
def login():
    provider = request.args.get("provider", "")
    flow = store.create_auth_flow(provider)
    params = {
        "client_id": KEYCLOAK_CLIENT_ID,
        "redirect_uri": f"{PUBLIC_BASE_URL}/auth/callback",
        "response_type": "code",
        "scope": "openid profile email",
        "state": flow["state"],
        "code_challenge": pkce_challenge(flow["verifier"]),
        "code_challenge_method": "S256",
    }
    if provider:
        params["kc_idp_hint"] = provider
    response = redirect(
        f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth?{urlencode(params)}"
    )
    response.set_cookie(
        STATE_COOKIE_NAME,
        flow["state"],
        max_age=600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAME_SITE,
        path="/",
    )

    return response


@app.route("/auth/callback", methods=["GET"])
def callback():
    error = request.args.get("error", "")
    if error:
        return redirect(f"{FRONTEND_BASE_URL}?authError={error}")

    state = request.args.get("state", "")
    code = request.args.get("code", "")
    cookie_state = request.cookies.get(STATE_COOKIE_NAME, "")
    if not state or not code or not cookie_state or cookie_state != state:
        return jsonify({"error": "invalid_state"}), 400

    flow = store.pop_auth_flow(state)
    if flow is None:
        return jsonify({"error": "unknown_auth_flow"}), 400

    tokens = token_request(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{PUBLIC_BASE_URL}/auth/callback",
            "client_id": KEYCLOAK_CLIENT_ID,
            "code_verifier": flow["verifier"],
        }
    )
    profile = extract_profile(tokens)

    if flow["provider"] and not profile.identity_provider:
        profile.identity_provider = flow["provider"]
    profiles.upsert(profile)
    session = store.create_session(tokens, profile)

    response = redirect(FRONTEND_BASE_URL)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session.session_id,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAME_SITE,
        path="/",
    )
    response.set_cookie(
        STATE_COOKIE_NAME,
        "",
        max_age=0,
        expires=0,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAME_SITE,
        path="/",
    )

    return response


@app.route("/auth/logout", methods=["POST", "OPTIONS"])
def logout():
    if request.method == "OPTIONS":
        return ("", 204)

    session_id = request.cookies.get(SESSION_COOKIE_NAME, "")
    if session_id:
        record = store.get_session(session_id)
        if record is not None:
            try:
                revoke_refresh_token(store, record)
            except Exception:
                pass
        store.delete_session(session_id)

    response = make_response("", 204)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        "",
        max_age=0,
        expires=0,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAME_SITE,
        path="/",
    )

    return response


@app.route("/api/session", methods=["GET", "OPTIONS"])
def session_status():
    if request.method == "OPTIONS":
        return ("", 204)

    record, rotated_id = ensure_authenticated(rotate=True)
    if record is None:
        return jsonify({"authenticated": False}), 401

    response = jsonify(
        {
            "authenticated": True,
            "access_token_valid": datetime.now(timezone.utc) < record.access_token_expires_at,
            "user": asdict(record.profile),
        }
    )
    if rotated_id:
        response.set_cookie(
            SESSION_COOKIE_NAME,
            rotated_id,
            max_age=int(SESSION_TTL.total_seconds()),
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAME_SITE,
            path="/",
        )
        response.headers["X-Session-Rotated"] = rotated_id

    return response


@app.route("/reports", methods=["GET", "OPTIONS"])
def reports_download():
    if request.method == "OPTIONS":
        return ("", 204)

    record, rotated_id = ensure_authenticated(rotate=True)
    if record is None:
        return jsonify({"error": "unauthorized"}), 401

    requested_username = request.args.get("username")
    current_username = record.profile.username or record.profile.email
    if requested_username and requested_username != current_username:
        return jsonify({"error": "forbidden"}), 403

    date_from_value = request.args.get("date_from")
    date_to_value = request.args.get("date_to")
    date_from = datetime.strptime(date_from_value, "%Y-%m-%d").date() if date_from_value else None
    date_to = datetime.strptime(date_to_value, "%Y-%m-%d").date() if date_to_value else None

    report = get_report_for_user(current_username, date_from, date_to)
    if report is None:
        return jsonify({"error": "report_mart_not_ready"}), 503
    if report.get("error") == "period_not_available":
        return jsonify(report), 409
    if report.get("error") == "report_not_found":
        return jsonify(report), 404

    response = jsonify(report)
    if rotated_id:
        response.set_cookie(
            SESSION_COOKIE_NAME,
            rotated_id,
            max_age=int(SESSION_TTL.total_seconds()),
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAME_SITE,
            path="/",
        )
        response.headers["X-Session-Rotated"] = rotated_id

    return response


def cleanup_worker() -> None:
    while True:
        store.cleanup()
        time.sleep(60)


def main() -> None:
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    host, port = LISTEN_ADDR.split(":")
    app.run(host=host or "0.0.0.0", port=int(port), debug=False)


if __name__ == "__main__":
    main()
