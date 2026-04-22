"""Anomaly detection."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from wallet_intel.services.snapshot import latest_balance_diff
from wallet_intel.src.db import get_conn
from wallet_intel.src.utils import utc_now_iso


def _load_thresholds(path: Path) -> dict:
    return json.loads(path.read_text())


def run_anomaly_scan(db_path: Path, thresholds_path: Path) -> None:
    t = _load_thresholds(thresholds_path)
    now = utc_now_iso()
    with get_conn(db_path) as conn:
        wallets = conn.execute("SELECT id, chain FROM master_wallets WHERE is_active=1").fetchall()
        for wallet in wallets:
            wallet_id = wallet["id"]
            chain = wallet["chain"]
            diff = latest_balance_diff(db_path, wallet_id)
            if diff and abs(diff["delta_pct"]) >= t["sudden_balance_change_pct"]:
                conn.execute(
                    "INSERT INTO wallet_flags(wallet_id, chain, flag_type, severity, details, created_at, is_open) VALUES (?, ?, ?, ?, ?, ?, 1)",
                    (wallet_id, chain, "anomaly_detected", "high", f"Balance moved {diff['delta_pct']:.2f}%", now),
                )

            activity = conn.execute(
                "SELECT tx_count, last_activity_at, snap_ts FROM activity_snapshots WHERE wallet_id=? ORDER BY snap_ts DESC LIMIT 2",
                (wallet_id,),
            ).fetchall()
            if len(activity) == 2:
                latest = activity[0]
                prev = activity[1]
                prev_count = max(1, int(prev["tx_count"] or 0))
                latest_count = int(latest["tx_count"] or 0)
                if latest_count >= prev_count * t["tx_spike_multiplier"]:
                    conn.execute(
                        "INSERT INTO wallet_flags(wallet_id, chain, flag_type, severity, details, created_at, is_open) VALUES (?, ?, ?, ?, ?, ?, 1)",
                        (wallet_id, chain, "anomaly_detected", "medium", f"TX spike {prev_count}->{latest_count}", now),
                    )

            bal = conn.execute(
                "SELECT native_balance, snap_ts FROM balance_snapshots WHERE wallet_id=? ORDER BY snap_ts DESC LIMIT 1",
                (wallet_id,),
            ).fetchone()
            if bal:
                last_snap = datetime.fromisoformat(bal["snap_ts"])
                if last_snap < datetime.now(timezone.utc) - timedelta(hours=t["stale_data_hours"]):
                    conn.execute(
                        "INSERT INTO wallet_flags(wallet_id, chain, flag_type, severity, details, created_at, is_open) VALUES (?, ?, ?, ?, ?, ?, 1)",
                        (wallet_id, chain, "stale_data", "medium", "Snapshot older than threshold", now),
                    )
