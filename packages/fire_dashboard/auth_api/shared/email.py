from __future__ import annotations

import json
from urllib import request
from urllib.error import HTTPError, URLError

from .config import get_settings


def send_password_reset_email(recipient_email: str, reset_url: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")
    if not settings.password_reset_from_email:
        raise RuntimeError("PASSWORD_RESET_FROM_EMAIL is not configured")

    payload = {
        "from": settings.password_reset_from_email,
        "to": [recipient_email],
        "subject": settings.password_reset_email_subject,
        "html": (
            "<p>You requested a password reset for Fire Weather Dashboard.</p>"
            f"<p><a href=\"{reset_url}\">Reset your password</a></p>"
            f"<p>This link expires in {settings.password_reset_token_ttl_seconds // 60} minutes.</p>"
            "<p>If you did not request this, you can ignore this email.</p>"
        ),
    }
    req = request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            if response.status >= 400:
                raise RuntimeError(f"Resend returned {response.status}")
    except HTTPError as exc:
        raise RuntimeError(f"Resend request failed with {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("Unable to reach Resend") from exc
