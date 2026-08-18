from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

def _password_hasher() -> Any:
    from argon2 import PasswordHasher

    return PasswordHasher()


def normalize_email(value: str) -> str:
    return value.strip().lower()


def validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(ch.isalpha() for ch in password):
        return "Password must include at least one letter."
    if not any(ch.isdigit() for ch in password):
        return "Password must include at least one number."
    return None


def hash_password(password: str) -> str:
    return _password_hasher().hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    from argon2.exceptions import VerifyMismatchError

    try:
        return _password_hasher().verify(password_hash, password)
    except VerifyMismatchError:
        return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def generate_one_time_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def safe_equal_string(left: str, right: str) -> bool:
    left_bytes = left.encode("utf-8")
    right_bytes = right.encode("utf-8")
    if len(left_bytes) != len(right_bytes):
        return False
    return secrets.compare_digest(left_bytes, right_bytes)
