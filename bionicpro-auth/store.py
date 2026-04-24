import base64
import hashlib
import json
import os
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet

from utils import random_string


@dataclass
class Profile:
    subject: str = ""
    username: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    name: str = ""
    preferred_username: str = ""
    identity_provider: str = ""
    identity_provider_id: str = ""
    claims: dict[str, str] = field(default_factory=dict)
    updated_at: str = ""


@dataclass
class Session:
    session_id: str
    access_token: str
    access_token_expires_at: datetime
    encrypted_refresh_token: bytes
    refresh_token_expires_at: datetime
    profile: Profile
    created_at: datetime
    last_refreshed_at: datetime
    last_session_rotation_at: datetime


class ProfileStore:
    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    subject TEXT PRIMARY KEY,
                    username TEXT,
                    email TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    name TEXT,
                    preferred_username TEXT,
                    identity_provider TEXT,
                    identity_provider_id TEXT,
                    claims_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def upsert(self, profile: Profile) -> None:
        profile.updated_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO profiles (
                    subject, username, email, first_name, last_name, name, preferred_username,
                    identity_provider, identity_provider_id, claims_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(subject) DO UPDATE SET
                    username = excluded.username,
                    email = excluded.email,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    name = excluded.name,
                    preferred_username = excluded.preferred_username,
                    identity_provider = excluded.identity_provider,
                    identity_provider_id = excluded.identity_provider_id,
                    claims_json = excluded.claims_json,
                    updated_at = excluded.updated_at
                """,
                (
                    profile.subject,
                    profile.username,
                    profile.email,
                    profile.first_name,
                    profile.last_name,
                    profile.name,
                    profile.preferred_username,
                    profile.identity_provider,
                    profile.identity_provider_id,
                    json.dumps(profile.claims),
                    profile.updated_at,
                ),
            )
            connection.commit()


class SessionStore:
    def __init__(self, secret: str, session_ttl: timedelta) -> None:
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(digest))
        self.session_ttl = session_ttl
        self.sessions: dict[str, Session] = {}
        self.auth_flows: dict[str, dict[str, Any]] = {}
        self.lock = threading.RLock()

    def create_auth_flow(self, provider: str) -> dict[str, str]:
        state = random_string(48)
        verifier = random_string(96)
        with self.lock:
            self.auth_flows[state] = {
                "verifier": verifier,
                "provider": provider,
                "created_at": datetime.now(timezone.utc),
            }

        return {"state": state, "verifier": verifier}

    def pop_auth_flow(self, state: str) -> dict[str, Any] | None:
        with self.lock:
            return self.auth_flows.pop(state, None)

    def create_session(self, tokens: dict[str, Any], profile: Profile) -> Session:
        now = datetime.now(timezone.utc)
        refresh_expires_at = now + self.session_ttl
        if int(tokens.get("refresh_expires_in", 0)) > 0:
            refresh_expires_at = now + timedelta(seconds=int(tokens["refresh_expires_in"]))

        record = Session(
            session_id=random_string(48),
            access_token=tokens["access_token"],
            access_token_expires_at=now + timedelta(seconds=int(tokens["expires_in"])),
            encrypted_refresh_token=self.fernet.encrypt(tokens["refresh_token"].encode("utf-8")),
            refresh_token_expires_at=refresh_expires_at,
            profile=profile,
            created_at=now,
            last_refreshed_at=now,
            last_session_rotation_at=now,
        )

        with self.lock:
            self.sessions[record.session_id] = record

        return record

    def get_session(self, session_id: str) -> Session | None:
        with self.lock:
            session = self.sessions.get(session_id)
            if session is None:
                return None
            if datetime.now(timezone.utc) > session.refresh_token_expires_at:
                self.sessions.pop(session_id, None)
                return None

            return session

    def delete_session(self, session_id: str) -> None:
        with self.lock:
            self.sessions.pop(session_id, None)

    def rotate_session(self, session_id: str) -> Session | None:
        with self.lock:
            current = self.sessions.get(session_id)
            if current is None:
                return None
            new_id = random_string(48)
            rotated = Session(
                session_id=new_id,
                access_token=current.access_token,
                access_token_expires_at=current.access_token_expires_at,
                encrypted_refresh_token=current.encrypted_refresh_token,
                refresh_token_expires_at=current.refresh_token_expires_at,
                profile=current.profile,
                created_at=current.created_at,
                last_refreshed_at=current.last_refreshed_at,
                last_session_rotation_at=datetime.now(timezone.utc),
            )
            self.sessions[new_id] = rotated
            self.sessions.pop(session_id, None)

            return rotated

    def cleanup(self) -> None:
        now = datetime.now(timezone.utc)
        with self.lock:
            expired_sessions = [
                session_id
                for session_id, record in self.sessions.items()
                if now > record.refresh_token_expires_at
            ]
            for session_id in expired_sessions:
                self.sessions.pop(session_id, None)

            expired_flows = [
                state
                for state, flow in self.auth_flows.items()
                if now - flow["created_at"] > timedelta(minutes=10)
            ]
            for state in expired_flows:
                self.auth_flows.pop(state, None)
