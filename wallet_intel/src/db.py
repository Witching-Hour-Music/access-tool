"""SQLite helpers."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_conn(db_path: Path):
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path, schema_path: Path) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(schema_path.read_text())
