"""Snapshot utilities and diff operations."""
from __future__ import annotations

from pathlib import Path

from wallet_intel.src.db import get_conn


def latest_balance_diff(db_path: Path, wallet_id: int):
    with get_conn(db_path) as conn:
        rows = conn.execute(
            """
            SELECT total_wallet_usd, snap_ts
            FROM balance_snapshots
            WHERE wallet_id = ?
            ORDER BY snap_ts DESC
            LIMIT 2
            """,
            (wallet_id,),
        ).fetchall()
    if len(rows) < 2:
        return None
    newest, previous = rows[0], rows[1]
    old = float(previous["total_wallet_usd"] or 0)
    new = float(newest["total_wallet_usd"] or 0)
    pct = ((new - old) / old * 100) if old else 0
    return {
        "old_total": old,
        "new_total": new,
        "delta": new - old,
        "delta_pct": pct,
        "new_ts": newest["snap_ts"],
    }
