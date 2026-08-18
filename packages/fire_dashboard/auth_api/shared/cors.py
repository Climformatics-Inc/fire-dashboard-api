from __future__ import annotations

from typing import Any

from .config import get_settings
from .request import get_origin


def cors_headers(event: dict[str, Any] | None = None, methods: str = "GET, POST, OPTIONS") -> dict[str, str]:
    settings = get_settings()
    request_origin = get_origin(event or {})
    allow_origin = settings.frontend_origin or request_origin or "http://localhost:5173"
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": methods,
        "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization, X-Session-Token",
        "Access-Control-Expose-Headers": "X-Session-Token",
        "Access-Control-Max-Age": "3600",
        "Content-Type": "application/json",
        "Vary": "Origin",
    }
