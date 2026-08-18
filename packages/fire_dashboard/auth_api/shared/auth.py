from __future__ import annotations

import os
from typing import Any

from .config import get_settings
from .request import get_headers
from .security import hash_session_token


def _bootstrap_admin_user(event: dict[str, Any]) -> dict[str, Any] | None:
    settings = get_settings()
    email = os.getenv("ADMIN_EMAIL")
    if not email:
        return None
    from .session import resolve_session_token

    token = resolve_session_token(event, settings)
    if not token:
        return None
    expected = f"bootstrap-admin:{hash_session_token(email, settings.session_secret)}"
    if token != expected:
        return None
    return {
        "id": "bootstrap-admin",
        "email": email,
        "subscription_status": "active",
        "plan_id": os.getenv("ADMIN_PLAN_ID", "pro"),
        "is_admin": True,
    }


def current_user(event: dict[str, Any], *, require_active: bool) -> dict[str, Any] | None:
    admin_user = _bootstrap_admin_user(event)
    if admin_user is not None:
        return admin_user

    from .db import get_db_connection
    from .session import get_session_user_from_event

    with get_db_connection() as conn:
        return get_session_user_from_event(conn, event, require_active=require_active)


def serialize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "email": user["email"],
        "subscriptionStatus": user.get("subscription_status") or "inactive",
        "planId": user.get("plan_id"),
        "isAdmin": bool(user.get("is_admin")),
    }
