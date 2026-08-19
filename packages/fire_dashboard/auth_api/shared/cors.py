from __future__ import annotations

from typing import Any

from .config import get_settings
from .request import get_origin


def _normalize_origin(origin: str | None) -> str | None:
    if not origin:
        return None
    return origin.rstrip("/")


def cors_headers(event: dict[str, Any] | None = None, methods: str = "GET, POST, OPTIONS") -> dict[str, str]:
    settings = get_settings()
    request_origin = get_origin(event or {})
    configured = _normalize_origin(settings.frontend_origin)
    requested = _normalize_origin(request_origin)

    if configured and requested and configured == requested:
        allow_origin = requested
    elif configured:
        allow_origin = configured
    elif requested:
        allow_origin = requested
    else:
        allow_origin = "http://localhost:5173"
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
