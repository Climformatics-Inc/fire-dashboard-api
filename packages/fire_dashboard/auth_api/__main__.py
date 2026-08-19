from __future__ import annotations

import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ACTION_DIR = Path(__file__).resolve().parent
VENDOR_DIR = ACTION_DIR / "vendor"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))
if str(ACTION_DIR) not in sys.path:
    sys.path.insert(0, str(ACTION_DIR))

from shared.config import get_settings
from shared.request import get_method, get_path, parse_json_body
from shared.response import error_response, json_response, no_content_response


def current_user(event: dict[str, Any], *, require_active: bool) -> dict[str, Any] | None:
    from shared.auth import current_user as _current_user

    return _current_user(event, require_active=require_active)


def serialize_user(user: dict[str, Any]) -> dict[str, Any]:
    from shared.auth import serialize_user as _serialize_user

    return _serialize_user(user)


def get_db_connection():
    from shared.db import get_db_connection as _get_db_connection

    return _get_db_connection()


def create_user(conn: Any, *, user_id: str, email: str, password_hash: str):
    from shared.repository import create_user as _create_user

    return _create_user(conn, user_id=user_id, email=email, password_hash=password_hash)


def get_user_by_email(conn: Any, email: str):
    from shared.repository import get_user_by_email as _get_user_by_email

    return _get_user_by_email(conn, email)


def get_user_by_id(conn: Any, user_id: str):
    from shared.repository import get_user_by_id as _get_user_by_id

    return _get_user_by_id(conn, user_id)


def list_users(conn: Any):
    from shared.repository import list_users as _list_users

    return _list_users(conn)


def set_user_disabled(conn: Any, user_id: str, *, is_disabled: bool) -> None:
    from shared.repository import set_user_disabled as _set_user_disabled

    _set_user_disabled(conn, user_id, is_disabled=is_disabled)


def delete_user(conn: Any, user_id: str) -> None:
    from shared.repository import delete_user as _delete_user

    _delete_user(conn, user_id)


def list_active_plans(conn: Any):
    from shared.repository import list_active_plans as _list_active_plans

    return _list_active_plans(conn)


def get_plan(conn: Any, plan_id: str):
    from shared.repository import get_plan as _get_plan

    return _get_plan(conn, plan_id)


def get_access_code(conn: Any, code: str):
    from shared.repository import get_access_code as _get_access_code

    return _get_access_code(conn, code)


def activate_placeholder_subscription(conn: Any, *, subscription_id: str, user_id: str, plan_id: str, now: datetime) -> None:
    from shared.repository import activate_placeholder_subscription as _activate_placeholder_subscription

    _activate_placeholder_subscription(conn, subscription_id=subscription_id, user_id=user_id, plan_id=plan_id, now=now)


def update_subscription_status(conn: Any, *, user_id: str, plan_id: str, status: str, now: datetime) -> None:
    from shared.repository import update_subscription_status as _update_subscription_status

    _update_subscription_status(conn, user_id=user_id, plan_id=plan_id, status=status, now=now)


def create_password_reset_token_record(
    conn: Any,
    *,
    token_id: str,
    user_id: str,
    token_hash: str,
    expires_at: datetime,
) -> None:
    from shared.repository import create_password_reset_token as _create_password_reset_token

    _create_password_reset_token(conn, token_id=token_id, user_id=user_id, token_hash=token_hash, expires_at=expires_at)


def invalidate_password_reset_tokens_for_user(conn: Any, user_id: str) -> None:
    from shared.repository import invalidate_password_reset_tokens_for_user as _invalidate_password_reset_tokens_for_user

    _invalidate_password_reset_tokens_for_user(conn, user_id)


def get_password_reset_token(conn: Any, token_hash: str):
    from shared.repository import get_password_reset_token as _get_password_reset_token

    return _get_password_reset_token(conn, token_hash)


def consume_password_reset_token(conn: Any, token_id: str, *, consumed_at: datetime) -> None:
    from shared.repository import consume_password_reset_token as _consume_password_reset_token

    _consume_password_reset_token(conn, token_id, consumed_at=consumed_at)


def update_user_password(conn: Any, user_id: str, password_hash: str) -> None:
    from shared.repository import update_user_password as _update_user_password

    _update_user_password(conn, user_id, password_hash)


def hash_password(password: str) -> str:
    from shared.security import hash_password as _hash_password

    return _hash_password(password)


def normalize_email(value: str) -> str:
    from shared.security import normalize_email as _normalize_email

    return _normalize_email(value)


def validate_password(password: str) -> str | None:
    from shared.security import validate_password as _validate_password

    return _validate_password(password)


def verify_password(password_hash: str, password: str) -> bool:
    from shared.security import verify_password as _verify_password

    return _verify_password(password_hash, password)


def generate_one_time_token() -> str:
    from shared.security import generate_one_time_token as _generate_one_time_token

    return _generate_one_time_token()


def hash_session_token(token: str, secret: str) -> str:
    from shared.security import hash_session_token as _hash_session_token

    return _hash_session_token(token, secret)


def safe_equal_string(left: str, right: str) -> bool:
    from shared.security import safe_equal_string as _safe_equal_string

    return _safe_equal_string(left, right)


def build_session_cookie(token: str) -> str:
    from shared.session import build_session_cookie as _build_session_cookie

    return _build_session_cookie(token)


def build_clear_cookie() -> str:
    from shared.session import build_clear_cookie as _build_clear_cookie

    return _build_clear_cookie()


def session_response(
    event: dict[str, Any],
    status_code: int,
    payload: dict[str, Any],
    token: str,
) -> dict[str, Any]:
    return json_response(
        event,
        status_code,
        payload,
        extra_headers={
            "Set-Cookie": build_session_cookie(token),
            "X-Session-Token": token,
        },
    )


def create_user_session(conn: Any, user_id: str) -> str:
    from shared.session import create_user_session as _create_user_session

    return _create_user_session(conn, user_id)


def revoke_session_from_event(conn: Any, event: dict[str, Any]) -> None:
    from shared.session import revoke_session_from_event as _revoke_session_from_event

    _revoke_session_from_event(conn, event)


def revoke_all_user_sessions(conn: Any, user_id: str) -> None:
    from shared.session import revoke_all_user_sessions as _revoke_all_user_sessions

    _revoke_all_user_sessions(conn, user_id)


def send_password_reset_email(recipient_email: str, reset_url: str) -> None:
    from shared.email import send_password_reset_email as _send_password_reset_email

    _send_password_reset_email(recipient_email, reset_url)


def _matches_path(path: str, route: str) -> bool:
    return path == route or path.endswith(route)


def _admin_user_id(path: str, suffix: str) -> str | None:
    marker = "/admin/users/"
    if marker not in path or not path.endswith(suffix):
        return None
    user_path = path[path.rfind(marker) + len(marker):]
    user_id = user_path[: -len(suffix)]
    user_id = user_id.rstrip("/")
    return user_id or None


def _current_admin(event: dict[str, Any]) -> dict[str, Any] | None:
    user = current_user(event, require_active=False)
    if not user or not user.get("is_admin"):
        return None
    return user


def _require_admin(event: dict[str, Any]) -> dict[str, Any] | dict[str, Any] | None:
    user = _current_admin(event)
    if user is None:
        return error_response(event, 403, "forbidden")
    return user


def _valid_plan(conn: Any, plan_id: str) -> dict[str, Any] | None:
    plan = get_plan(conn, plan_id)
    if not plan or not plan.get("is_active"):
        return None
    return plan


def _valid_access_code(conn: Any, code: str) -> dict[str, Any] | None:
    access_code = get_access_code(conn, code)
    if not access_code or not access_code.get("is_active"):
        return None
    plan = _valid_plan(conn, access_code["target_plan_id"])
    if not plan:
        return None
    return access_code


def _password_reset_success(event: dict[str, Any]) -> dict[str, Any]:
    return json_response(event, 200, {"status": "password_reset_requested"})


def _issue_password_reset(conn: Any, user: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.frontend_origin:
        raise RuntimeError("FRONTEND_ORIGIN is not configured")

    raw_token = generate_one_time_token()
    token_hash = hash_session_token(raw_token, settings.session_secret)
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.password_reset_token_ttl_seconds)
    invalidate_password_reset_tokens_for_user(conn, user["id"])
    create_password_reset_token_record(
        conn,
        token_id=str(uuid.uuid4()),
        user_id=user["id"],
        token_hash=token_hash,
        expires_at=expires_at,
    )
    reset_url = f"{settings.frontend_origin.rstrip('/')}/reset-password?token={raw_token}"
    send_password_reset_email(user["email"], reset_url)


def main(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    method = get_method(event)
    if method == "OPTIONS":
        return no_content_response(event)

    path = get_path(event)

    try:
        if _matches_path(path, "/auth/signup") and method == "POST":
            return handle_signup(event)
        if _matches_path(path, "/auth/signup-and-subscribe") and method == "POST":
            return handle_signup_and_subscribe(event)
        if _matches_path(path, "/auth/signup-with-access-code") and method == "POST":
            return handle_signup_with_access_code(event)
        if _matches_path(path, "/auth/signin") and method == "POST":
            return handle_signin(event)
        if _matches_path(path, "/auth/signout") and method == "POST":
            return handle_signout(event)
        if _matches_path(path, "/auth/me") and method == "GET":
            return handle_me(event)
        if _matches_path(path, "/auth/forgot-password") and method == "POST":
            return handle_forgot_password(event)
        if _matches_path(path, "/auth/reset-password") and method == "POST":
            return handle_reset_password(event)
        if _matches_path(path, "/plans") and method == "GET":
            return handle_plans(event)
        if _matches_path(path, "/plans/select") and method == "POST":
            return handle_plan_select(event)
        if _matches_path(path, "/plans/activate-with-access-code") and method == "POST":
            return handle_activate_with_access_code(event)
        if _matches_path(path, "/checkout/placeholder/start") and method == "POST":
            return handle_placeholder_start(event)
        if _matches_path(path, "/checkout/placeholder/complete") and method == "POST":
            return handle_placeholder_complete(event)
        if _matches_path(path, "/admin/users") and method == "GET":
            return handle_admin_users(event)

        user_id = _admin_user_id(path, "/disable")
        if user_id and method == "POST":
            return handle_admin_disable_user(event, user_id)
        user_id = _admin_user_id(path, "/enable")
        if user_id and method == "POST":
            return handle_admin_enable_user(event, user_id)
        user_id = _admin_user_id(path, "/delete")
        if user_id and method == "POST":
            return handle_admin_delete_user(event, user_id)
        user_id = _admin_user_id(path, "/subscription")
        if user_id and method == "POST":
            return handle_admin_subscription(event, user_id)
        user_id = _admin_user_id(path, "/password-reset")
        if user_id and method == "POST":
            return handle_admin_password_reset(event, user_id)

        if path in ("/", "") and method == "GET":
            return json_response(event, 200, {"status": "ok"})
    except ValueError as exc:
        return error_response(event, 400, "bad_request", message=str(exc))
    except RuntimeError as exc:
        return error_response(event, 500, "server_error", message=str(exc))

    return error_response(event, 404, "not_found")


def handle_signup(event: dict[str, Any]) -> dict[str, Any]:
    body = parse_json_body(event)
    email = normalize_email(str(body.get("email", "")))
    password = str(body.get("password", ""))

    if not email or "@" not in email:
        return error_response(event, 400, "invalid_email")
    password_error = validate_password(password)
    if password_error:
        return error_response(event, 400, "invalid_password", message=password_error)

    with get_db_connection() as conn:
        if get_user_by_email(conn, email):
            return error_response(event, 409, "email_exists")
        user = create_user(conn, user_id=str(uuid.uuid4()), email=email, password_hash=hash_password(password))
        user_view = current_user_for_id(conn, user["id"])
        token = create_user_session(conn, user["id"])

    return session_response(
        event,
        201,
        {
            "userId": user["id"],
            "email": user["email"],
            "status": "created",
            "user": serialize_user(user_view),
        },
        token,
    )


def handle_signup_and_subscribe(event: dict[str, Any]) -> dict[str, Any]:
    body = parse_json_body(event)
    email = normalize_email(str(body.get("email", "")))
    password = str(body.get("password", ""))
    plan_id = str(body.get("planId", ""))

    if not email or "@" not in email:
        return error_response(event, 400, "invalid_email")
    password_error = validate_password(password)
    if password_error:
        return error_response(event, 400, "invalid_password", message=password_error)
    if not plan_id:
        return error_response(event, 400, "plan_required")

    with get_db_connection() as conn:
        if get_user_by_email(conn, email):
            return error_response(event, 409, "email_exists")
        plan = _valid_plan(conn, plan_id)
        if not plan:
            return error_response(event, 404, "plan_not_found")

        user = create_user(conn, user_id=str(uuid.uuid4()), email=email, password_hash=hash_password(password))
        activate_placeholder_subscription(
            conn,
            subscription_id=str(uuid.uuid4()),
            user_id=user["id"],
            plan_id=plan_id,
            now=datetime.now(UTC),
        )
        user_view = current_user_for_id(conn, user["id"])
        token = create_user_session(conn, user["id"])

    return session_response(event, 201, {"user": serialize_user(user_view)}, token)


def handle_signup_with_access_code(event: dict[str, Any]) -> dict[str, Any]:
    body = parse_json_body(event)
    email = normalize_email(str(body.get("email", "")))
    password = str(body.get("password", ""))
    access_code_value = str(body.get("accessCode", ""))

    if not email or "@" not in email:
        return error_response(event, 400, "invalid_email")
    password_error = validate_password(password)
    if password_error:
        return error_response(event, 400, "invalid_password", message=password_error)
    if not access_code_value:
        return error_response(event, 400, "access_code_required")

    with get_db_connection() as conn:
        if get_user_by_email(conn, email):
            return error_response(event, 409, "email_exists")
        access_code = _valid_access_code(conn, access_code_value)
        if not access_code:
            return error_response(event, 400, "invalid_access_code")

        user = create_user(conn, user_id=str(uuid.uuid4()), email=email, password_hash=hash_password(password))
        activate_placeholder_subscription(
            conn,
            subscription_id=str(uuid.uuid4()),
            user_id=user["id"],
            plan_id=access_code["target_plan_id"],
            now=datetime.now(UTC),
        )
        user_view = current_user_for_id(conn, user["id"])
        token = create_user_session(conn, user["id"])

    return session_response(event, 201, {"user": serialize_user(user_view)}, token)


def handle_signin(event: dict[str, Any]) -> dict[str, Any]:
    body = parse_json_body(event)
    email = normalize_email(str(body.get("email", "")))
    password = str(body.get("password", ""))
    settings = get_settings()

    admin_email = normalize_email(os.getenv("ADMIN_EMAIL", ""))
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    if (
        admin_email
        and email == admin_email
        and admin_password
        and safe_equal_string(password, admin_password)
    ):
        token = f"bootstrap-admin:{hash_session_token(admin_email, settings.session_secret)}"
        user_view = {
            "id": "bootstrap-admin",
            "email": admin_email,
            "subscription_status": "active",
            "plan_id": os.getenv("ADMIN_PLAN_ID", "pro"),
            "is_admin": True,
        }
        return session_response(event, 200, {"user": serialize_user(user_view)}, token)

    with get_db_connection() as conn:
        user = get_user_by_email(conn, email)
        if not user or not verify_password(user["password_hash"], password):
            return error_response(event, 401, "invalid_credentials")
        user_view = current_user_for_id(conn, user["id"])
        if user_view is None or user_view.get("is_disabled"):
            return error_response(event, 403, "user_disabled")
        token = create_user_session(conn, user["id"])

    return session_response(event, 200, {"user": serialize_user(user_view)}, token)


def handle_signout(event: dict[str, Any]) -> dict[str, Any]:
    with get_db_connection() as conn:
        revoke_session_from_event(conn, event)
    return json_response(event, 200, {"status": "signed_out"}, extra_headers={"Set-Cookie": build_clear_cookie()})


def handle_me(event: dict[str, Any]) -> dict[str, Any]:
    user = current_user(event, require_active=False)
    return json_response(event, 200, {"user": serialize_user(user) if user else None})


def handle_plans(event: dict[str, Any]) -> dict[str, Any]:
    with get_db_connection() as conn:
        plans = list_active_plans(conn)
    return json_response(event, 200, {"plans": plans})


def handle_plan_select(event: dict[str, Any]) -> dict[str, Any]:
    user = current_user(event, require_active=False)
    if not user:
        return error_response(event, 401, "unauthorized")

    body = parse_json_body(event)
    plan_id = str(body.get("planId", ""))
    if not plan_id:
        return error_response(event, 400, "plan_required")

    with get_db_connection() as conn:
        plan = _valid_plan(conn, plan_id)
        if not plan:
            return error_response(event, 404, "plan_not_found")
        activate_placeholder_subscription(
            conn,
            subscription_id=str(uuid.uuid4()),
            user_id=user["id"],
            plan_id=plan_id,
            now=datetime.now(UTC),
        )
        user_view = current_user_for_id(conn, user["id"])

    return json_response(event, 200, {"user": serialize_user(user_view)})


def handle_activate_with_access_code(event: dict[str, Any]) -> dict[str, Any]:
    user = current_user(event, require_active=False)
    if not user:
        return error_response(event, 401, "unauthorized")

    body = parse_json_body(event)
    access_code_value = str(body.get("accessCode", ""))
    if not access_code_value:
        return error_response(event, 400, "access_code_required")

    with get_db_connection() as conn:
        access_code = _valid_access_code(conn, access_code_value)
        if not access_code:
            return error_response(event, 400, "invalid_access_code")
        activate_placeholder_subscription(
            conn,
            subscription_id=str(uuid.uuid4()),
            user_id=user["id"],
            plan_id=access_code["target_plan_id"],
            now=datetime.now(UTC),
        )
        user_view = current_user_for_id(conn, user["id"])

    return json_response(event, 200, {"user": serialize_user(user_view)})


def handle_forgot_password(event: dict[str, Any]) -> dict[str, Any]:
    body = parse_json_body(event)
    email = normalize_email(str(body.get("email", "")))
    if not email or "@" not in email:
        return _password_reset_success(event)

    with get_db_connection() as conn:
        user = get_user_by_email(conn, email)
        if user and not user.get("is_disabled"):
            try:
                _issue_password_reset(conn, user)
            except Exception as exc:
                if get_settings().is_production:
                    raise
                print(f"Password reset email skipped: {exc}")

    return _password_reset_success(event)


def handle_reset_password(event: dict[str, Any]) -> dict[str, Any]:
    body = parse_json_body(event)
    token = str(body.get("token", "")).strip()
    password = str(body.get("password", ""))

    if not token:
        return error_response(event, 400, "token_required")
    password_error = validate_password(password)
    if password_error:
        return error_response(event, 400, "invalid_password", message=password_error)

    settings = get_settings()
    token_hash = hash_session_token(token, settings.session_secret)
    now = datetime.now(UTC)

    with get_db_connection() as conn:
        reset_token = get_password_reset_token(conn, token_hash)
        if not reset_token:
            return error_response(event, 400, "invalid_reset_token")
        if reset_token.get("consumed_at"):
            return error_response(event, 400, "reset_token_consumed")
        if reset_token["expires_at"] <= now:
            return error_response(event, 400, "reset_token_expired")

        update_user_password(conn, reset_token["user_id"], hash_password(password))
        consume_password_reset_token(conn, reset_token["id"], consumed_at=now)
        revoke_all_user_sessions(conn, reset_token["user_id"])

    return json_response(event, 200, {"status": "password_reset"})


def handle_placeholder_start(event: dict[str, Any]) -> dict[str, Any]:
    body = parse_json_body(event)
    email = normalize_email(str(body.get("email", "")))
    plan_id = str(body.get("planId", ""))

    with get_db_connection() as conn:
        user = get_user_by_email(conn, email)
        plan = get_plan(conn, plan_id)

    if not user:
        return error_response(event, 404, "user_not_found")
    if not plan or not plan.get("is_active"):
        return error_response(event, 404, "plan_not_found")

    return json_response(event, 200, {"checkoutId": str(uuid.uuid4()), "planId": plan_id, "status": "started"})


def handle_placeholder_complete(event: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if settings.is_production:
        return error_response(event, 403, "disabled")

    body = parse_json_body(event)
    email = normalize_email(str(body.get("email", "")))
    plan_id = str(body.get("planId", ""))
    checkout_id = str(body.get("checkoutId", ""))
    if not checkout_id:
        return error_response(event, 400, "missing_checkout_id")

    with get_db_connection() as conn:
        user = get_user_by_email(conn, email)
        plan = get_plan(conn, plan_id)
        if not user:
            return error_response(event, 404, "user_not_found")
        if not plan or not plan.get("is_active"):
            return error_response(event, 404, "plan_not_found")

        activate_placeholder_subscription(
            conn,
            subscription_id=str(uuid.uuid4()),
            user_id=user["id"],
            plan_id=plan_id,
            now=datetime.now(UTC),
        )

    return json_response(event, 200, {"status": "paid", "subscriptionStatus": "active", "planId": plan_id})


def handle_admin_users(event: dict[str, Any]) -> dict[str, Any]:
    forbidden = _require_admin(event)
    if isinstance(forbidden, dict) and forbidden.get("statusCode"):
        return forbidden

    with get_db_connection() as conn:
        users = list_users(conn)

    payload = {
        "users": [
            {
                "id": user["id"],
                "email": user["email"],
                "isAdmin": bool(user.get("is_admin")),
                "isDisabled": bool(user.get("is_disabled")),
                "subscriptionStatus": user.get("subscription_status") or "inactive",
                "planId": user.get("plan_id"),
                "createdAt": user["createdAt"].isoformat() if user.get("createdAt") else None,
                "updatedAt": user["updatedAt"].isoformat() if user.get("updatedAt") else None,
            }
            for user in users
        ]
    }
    return json_response(event, 200, payload)


def handle_admin_disable_user(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    forbidden = _require_admin(event)
    if isinstance(forbidden, dict) and forbidden.get("statusCode"):
        return forbidden

    with get_db_connection() as conn:
        target = get_user_by_id(conn, user_id)
        if not target:
            return error_response(event, 404, "user_not_found")
        set_user_disabled(conn, user_id, is_disabled=True)
        revoke_all_user_sessions(conn, user_id)

    return json_response(event, 200, {"status": "disabled"})


def handle_admin_enable_user(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    forbidden = _require_admin(event)
    if isinstance(forbidden, dict) and forbidden.get("statusCode"):
        return forbidden

    with get_db_connection() as conn:
        target = get_user_by_id(conn, user_id)
        if not target:
            return error_response(event, 404, "user_not_found")
        set_user_disabled(conn, user_id, is_disabled=False)

    return json_response(event, 200, {"status": "enabled"})


def handle_admin_delete_user(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    admin_user = _require_admin(event)
    if isinstance(admin_user, dict) and admin_user.get("statusCode"):
        return admin_user

    if admin_user["id"] == user_id:
        return error_response(event, 400, "cannot_delete_current_admin")

    with get_db_connection() as conn:
        target = get_user_by_id(conn, user_id)
        if not target:
            return error_response(event, 404, "user_not_found")
        delete_user(conn, user_id)

    return json_response(event, 200, {"status": "deleted"})


def handle_admin_subscription(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    forbidden = _require_admin(event)
    if isinstance(forbidden, dict) and forbidden.get("statusCode"):
        return forbidden

    body = parse_json_body(event)
    plan_id = str(body.get("planId", ""))
    status = str(body.get("status", ""))
    if status not in {"active", "inactive"}:
        return error_response(event, 400, "invalid_subscription_status")
    if not plan_id:
        return error_response(event, 400, "plan_required")

    with get_db_connection() as conn:
        target = get_user_by_id(conn, user_id)
        if not target:
            return error_response(event, 404, "user_not_found")
        plan = _valid_plan(conn, plan_id)
        if not plan:
            return error_response(event, 404, "plan_not_found")
        update_subscription_status(conn, user_id=user_id, plan_id=plan_id, status=status, now=datetime.now(UTC))
        user_view = current_user_for_id(conn, user_id)

    return json_response(event, 200, {"user": serialize_user(user_view)})


def handle_admin_password_reset(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    forbidden = _require_admin(event)
    if isinstance(forbidden, dict) and forbidden.get("statusCode"):
        return forbidden

    with get_db_connection() as conn:
        user = get_user_by_id(conn, user_id)
        if not user:
            return error_response(event, 404, "user_not_found")
        if not user.get("is_disabled"):
            _issue_password_reset(conn, user)

    return _password_reset_success(event)


def current_user_for_id(conn: Any, user_id: str) -> dict[str, Any] | None:
    from shared.repository import get_user_view_by_id

    return get_user_view_by_id(conn, user_id)
