from __future__ import annotations

from datetime import datetime
from typing import Any


def create_user(conn: Any, *, user_id: str, email: str, password_hash: str) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, password_hash_algorithm)
            VALUES (%s, %s, %s, 'argon2id')
            RETURNING id::text AS id, email, is_disabled, is_admin
            """,
            (user_id, email, password_hash),
        )
        return cur.fetchone()


def get_user_by_email(conn: Any, email: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text AS id, email, password_hash, is_disabled, is_admin
            FROM users
            WHERE email = %s
            """,
            (email,),
        )
        return cur.fetchone()


def get_user_by_id(conn: Any, user_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text AS id, email, password_hash, is_disabled, is_admin
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )
        return cur.fetchone()


def get_user_view_by_id(conn: Any, user_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              u.id::text AS id,
              u.email,
              u.is_disabled,
              u.is_admin,
              s.status AS subscription_status,
              s.plan_id
            FROM users u
            LEFT JOIN LATERAL (
              SELECT plan_id, status
              FROM subscriptions
              WHERE user_id = u.id
              ORDER BY updated_at DESC, created_at DESC
              LIMIT 1
            ) s ON true
            WHERE u.id = %s
            """,
            (user_id,),
        )
        return cur.fetchone()


def list_users(conn: Any) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              u.id::text AS id,
              u.email,
              u.is_disabled,
              u.is_admin,
              u.created_at AS "createdAt",
              u.updated_at AS "updatedAt",
              s.status AS subscription_status,
              s.plan_id
            FROM users u
            LEFT JOIN LATERAL (
              SELECT plan_id, status
              FROM subscriptions
              WHERE user_id = u.id
              ORDER BY updated_at DESC, created_at DESC
              LIMIT 1
            ) s ON true
            ORDER BY u.created_at DESC, u.id DESC
            """
        )
        return list(cur.fetchall())


def list_active_plans(conn: Any) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              id,
              name,
              description,
              price_cents AS "priceCents",
              currency,
              billing_interval AS "billingInterval"
            FROM plans
            WHERE is_active = true
            ORDER BY id
            """
        )
        return list(cur.fetchall())


def get_plan(conn: Any, plan_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, description, price_cents, currency, billing_interval, is_active
            FROM plans
            WHERE id = %s
            """,
            (plan_id,),
        )
        return cur.fetchone()


def get_access_code(conn: Any, code: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT code, target_plan_id, is_active
            FROM access_codes
            WHERE code = %s COLLATE "C"
            """,
            (code,),
        )
        return cur.fetchone()


def activate_placeholder_subscription(
    conn: Any,
    *,
    subscription_id: str,
    user_id: str,
    plan_id: str,
    now: datetime,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text AS id
            FROM subscriptions
            WHERE user_id = %s
            ORDER BY updated_at DESC, created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                """
                UPDATE subscriptions
                SET plan_id = %s,
                    status = 'active',
                    provider = 'placeholder',
                    current_period_start = %s,
                    current_period_end = NULL,
                    updated_at = %s
                WHERE id = %s
                """,
                (plan_id, now, now, existing["id"]),
            )
            return

        cur.execute(
            """
            INSERT INTO subscriptions (
              id,
              user_id,
              plan_id,
              status,
              provider,
              current_period_start,
              current_period_end
            )
            VALUES (%s, %s, %s, 'active', 'placeholder', %s, NULL)
            """,
            (subscription_id, user_id, plan_id, now),
        )


def update_subscription_status(
    conn: Any,
    *,
    user_id: str,
    plan_id: str,
    status: str,
    now: datetime,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text AS id
            FROM subscriptions
            WHERE user_id = %s
            ORDER BY updated_at DESC, created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                """
                UPDATE subscriptions
                SET plan_id = %s,
                    status = %s,
                    provider = 'placeholder',
                    current_period_start = %s,
                    current_period_end = NULL,
                    updated_at = %s
                WHERE id = %s
                """,
                (plan_id, status, now, now, existing["id"]),
            )
            return

        cur.execute(
            """
            INSERT INTO subscriptions (
              id,
              user_id,
              plan_id,
              status,
              provider,
              current_period_start,
              current_period_end
            )
            VALUES (%s, %s, %s, %s, 'placeholder', %s, NULL)
            """,
            (str(__import__("uuid").uuid4()), user_id, plan_id, status, now),
        )


def set_user_disabled(conn: Any, user_id: str, *, is_disabled: bool) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET is_disabled = %s,
                updated_at = now()
            WHERE id = %s
            """,
            (is_disabled, user_id),
        )


def delete_user(conn: Any, user_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM users
            WHERE id = %s
            """,
            (user_id,),
        )


def update_user_password(conn: Any, user_id: str, password_hash: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET password_hash = %s,
                password_hash_algorithm = 'argon2id',
                updated_at = now()
            WHERE id = %s
            """,
            (password_hash, user_id),
        )


def create_password_reset_token(
    conn: Any,
    *,
    token_id: str,
    user_id: str,
    token_hash: str,
    expires_at: datetime,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at)
            VALUES (%s, %s, %s, %s)
            """,
            (token_id, user_id, token_hash, expires_at),
        )


def invalidate_password_reset_tokens_for_user(conn: Any, user_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE password_reset_tokens
            SET consumed_at = COALESCE(consumed_at, now())
            WHERE user_id = %s
              AND consumed_at IS NULL
            """,
            (user_id,),
        )


def get_password_reset_token(conn: Any, token_hash: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              id::text AS id,
              user_id::text AS user_id,
              expires_at,
              consumed_at
            FROM password_reset_tokens
            WHERE token_hash = %s
            """,
            (token_hash,),
        )
        return cur.fetchone()


def consume_password_reset_token(conn: Any, token_id: str, *, consumed_at: datetime) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE password_reset_tokens
            SET consumed_at = %s
            WHERE id = %s
            """,
            (consumed_at, token_id),
        )


def create_session(
    conn: Any,
    *,
    session_id: str,
    user_id: str,
    session_token_hash: str,
    expires_at: datetime,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sessions (id, user_id, session_token_hash, expires_at)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, user_id, session_token_hash, expires_at),
        )


def revoke_session(conn: Any, session_token_hash: str, revoked_at: datetime) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE sessions
            SET revoked_at = %s
                WHERE session_token_hash = %s
              AND revoked_at IS NULL
            """,
            (revoked_at, session_token_hash),
        )


def revoke_sessions_for_user(conn: Any, user_id: str, revoked_at: datetime) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE sessions
            SET revoked_at = %s
            WHERE user_id = %s
              AND revoked_at IS NULL
            """,
            (revoked_at, user_id),
        )


def get_session_user(conn: Any, session_token_hash: str, now: datetime) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              u.id::text AS id,
              u.email,
              u.is_disabled,
              u.is_admin,
              s.status AS subscription_status,
              s.plan_id
            FROM sessions sess
            JOIN users u ON u.id = sess.user_id
            LEFT JOIN LATERAL (
              SELECT plan_id, status
              FROM subscriptions
              WHERE user_id = u.id
              ORDER BY updated_at DESC, created_at DESC
              LIMIT 1
            ) s ON true
            WHERE sess.session_token_hash = %s
              AND sess.revoked_at IS NULL
              AND sess.expires_at > %s
            """,
            (session_token_hash, now),
        )
        return cur.fetchone()
