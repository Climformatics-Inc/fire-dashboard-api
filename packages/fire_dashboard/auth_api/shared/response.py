from __future__ import annotations

import json
from typing import Any

from .cors import cors_headers


def json_response(
    event: dict[str, Any] | None,
    status_code: int,
    payload: dict[str, Any],
    *,
    methods: str = "GET, POST, OPTIONS",
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    headers = cors_headers(event, methods=methods)
    if extra_headers:
        headers.update(extra_headers)
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(payload),
    }


def no_content_response(event: dict[str, Any] | None, *, methods: str = "GET, POST, OPTIONS") -> dict[str, Any]:
    return {
        "statusCode": 204,
        "headers": cors_headers(event, methods=methods),
    }


def error_response(
    event: dict[str, Any] | None,
    status_code: int,
    code: str,
    *,
    message: str | None = None,
    methods: str = "GET, POST, OPTIONS",
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": code}
    if message:
        payload["message"] = message
    return json_response(event, status_code, payload, methods=methods, extra_headers=extra_headers)
