from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    frontend_origin: str | None
    environment: str
    session_cookie_name: str
    session_secret: str
    session_ttl_seconds: int
    resend_api_key: str | None
    password_reset_from_email: str | None
    password_reset_token_ttl_seconds: int
    password_reset_email_subject: str

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL"),
        frontend_origin=os.getenv("FRONTEND_ORIGIN"),
        environment=os.getenv("ENVIRONMENT", "development"),
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "fire_dashboard_session"),
        session_secret=os.getenv("SESSION_SECRET", "local-dev-session-secret"),
        session_ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", str(7 * 24 * 60 * 60))),
        resend_api_key=os.getenv("RESEND_API_KEY"),
        password_reset_from_email=os.getenv("PASSWORD_RESET_FROM_EMAIL"),
        password_reset_token_ttl_seconds=int(os.getenv("PASSWORD_RESET_TOKEN_TTL_SECONDS", "3600")),
        password_reset_email_subject=os.getenv(
            "PASSWORD_RESET_EMAIL_SUBJECT",
            "Reset your Fire Weather Dashboard password",
        ),
    )
