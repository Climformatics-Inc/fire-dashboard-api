from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from psycopg import connect
from psycopg.rows import dict_row

from .config import get_settings


@contextmanager
def get_db_connection() -> Iterator:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    with connect(settings.database_url, row_factory=dict_row, autocommit=True) as conn:
        yield conn


def migrations_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "migrations"
