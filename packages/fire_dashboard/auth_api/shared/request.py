from __future__ import annotations

import json
from http import cookies
from typing import Any


def get_method(event: dict[str, Any]) -> str:
    return (event.get("http", {}).get("method") or event.get("__ow_method") or "GET").upper()


def get_path(event: dict[str, Any]) -> str:
    return str(event.get("__ow_path") or event.get("http", {}).get("path") or "/")


def get_headers(event: dict[str, Any]) -> dict[str, str]:
    raw_headers: dict[str, Any] = {}
    if isinstance(event.get("__ow_headers"), dict):
        raw_headers.update(event["__ow_headers"])
    if isinstance(event.get("http", {}).get("headers"), dict):
        raw_headers.update(event["http"]["headers"])
    return {str(key).lower(): str(value) for key, value in raw_headers.items()}


def get_origin(event: dict[str, Any]) -> str | None:
    return get_headers(event).get("origin")


def parse_json_body(event: dict[str, Any]) -> dict[str, Any]:
    raw_body = event.get("body", event.get("__ow_body"))
    if raw_body in (None, ""):
        return {
            str(key): value
            for key, value in event.items()
            if not str(key).startswith("__ow_") and key not in {"http", "body"}
        }
    if isinstance(raw_body, dict):
        return raw_body
    if isinstance(raw_body, bytes):
        raw_body = raw_body.decode("utf-8")
    if isinstance(raw_body, str):
        return json.loads(raw_body)
    raise ValueError("Unsupported request body")


def get_cookie(event: dict[str, Any], cookie_name: str) -> str | None:
    cookie_header = get_headers(event).get("cookie")
    if not cookie_header:
        return None
    jar = cookies.SimpleCookie()
    jar.load(cookie_header)
    morsel = jar.get(cookie_name)
    return morsel.value if morsel else None
