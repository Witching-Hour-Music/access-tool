"""Generic helpers."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
