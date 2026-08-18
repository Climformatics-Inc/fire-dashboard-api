from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from .config import Settings, get_settings
from .request import get_cookie, get_headers
from .repository import create_session, get_session_user, revoke_session, revoke_sessions_for_user
from .security import generate_session_token, hash_session_token


def build_session_cookie(token: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    parts = [
        f"{settings.session_cookie_name}={token}",
        "Path=/",
        "HttpOnly",
        f"Max-Age={settings.session_ttl_seconds}",
    ]
    if settings.is_production:
        parts.append("Secure")
        parts.append("SameSite=None")
    else:
        parts.append("SameSite=Lax")
    return "; ".join(parts)


def build_clear_cookie(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    parts = [
        f"{settings.session_cookie_name}=",
        "Path=/",
        "HttpOnly",
        "Max-Age=0",
    ]
    if settings.is_production:
        parts.append("Secure")
        parts.append("SameSite=None")
    else:
        parts.append("SameSite=Lax")
    return "; ".join(parts)


def create_user_session(conn: Any, user_id: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    token = generate_session_token()
    token_hash = hash_session_token(token, settings.session_secret)
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.session_ttl_seconds)
    create_session(
        conn,
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        session_token_hash=token_hash,
        expires_at=expires_at,
    )
    return token


def resolve_session_token(event: dict[str, Any], settings: Settings | None = None) -> str | None:
    settings = settings or get_settings()
    token = get_cookie(event, settings.session_cookie_name)
    if token:
        return token

    token = str(event.get("sessionToken", "")).strip()
    if token:
        return token

    token = get_headers(event).get("x-session-token", "").strip()
    if token:
        return token

    authorization = get_headers(event).get("authorization", "")
    if authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()

    return None


def get_session_user_from_event(conn: Any, event: dict[str, Any], *, require_active: bool) -> dict[str, Any] | None:
    settings = get_settings()
    token = resolve_session_token(event, settings)
    if not token:
        return None
    token_hash = hash_session_token(token, settings.session_secret)
    user = get_session_user(conn, token_hash, datetime.now(UTC))
    if not user or user.get("is_disabled"):
        return None
    if require_active and user.get("subscription_status") != "active":
        return None
    return user


def revoke_session_from_event(conn: Any, event: dict[str, Any]) -> None:
    settings = get_settings()
    token = resolve_session_token(event, settings)
    if not token:
        return
    token_hash = hash_session_token(token, settings.session_secret)
    revoke_session(conn, token_hash, datetime.now(UTC))


def revoke_all_user_sessions(conn: Any, user_id: str) -> None:
    revoke_sessions_for_user(conn, user_id, datetime.now(UTC))
