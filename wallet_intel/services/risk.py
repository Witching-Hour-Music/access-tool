"""Risk flags derived from snapshots and metadata."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from wallet_intel.src.db import get_conn
from wallet_intel.src.utils import utc_now_iso


def evaluate_risk(db_path: Path, thresholds_path: Path) -> None:
    thresholds = json.loads(thresholds_path.read_text())
    now = utc_now_iso()
    dormant_cutoff = datetime.now(timezone.utc) - timedelta(days=thresholds["dormancy_days"])

    with get_conn(db_path) as conn:
        wallets = conn.execute(
            "SELECT id, chain, tags FROM master_wallets WHERE is_active=1"
        ).fetchall()
        for w in wallets:
            wallet_id = w["id"]
            chain = w["chain"]
            tags = (w["tags"] or "").strip()

            if not tags:
                conn.execute(
                    "INSERT INTO wallet_flags(wallet_id, chain, flag_type, severity, details, created_at, is_open) VALUES (?, ?, 'untagged_wallet', 'low', 'No tags assigned', ?, 1)",
                    (wallet_id, chain, now),
                )

            latest_balance = conn.execute(
                "SELECT native_balance, total_wallet_usd FROM balance_snapshots WHERE wallet_id=? ORDER BY snap_ts DESC LIMIT 1",
                (wallet_id,),
            ).fetchone()
            latest_activity = conn.execute(
                "SELECT last_activity_at FROM activity_snapshots WHERE wallet_id=? ORDER BY snap_ts DESC LIMIT 1",
                (wallet_id,),
            ).fetchone()

            if latest_activity and latest_activity["last_activity_at"]:
                try:
                    last_dt = datetime.fromisoformat(str(latest_activity["last_activity_at"]).replace("Z", "+00:00"))
                except ValueError:
                    last_dt = datetime.now(timezone.utc)
            else:
                last_dt = datetime.fromtimestamp(0, timezone.utc)

            total_usd = float(latest_balance["total_wallet_usd"] or 0) if latest_balance else 0
            if last_dt < dormant_cutoff:
                conn.execute(
                    "INSERT INTO wallet_flags(wallet_id, chain, flag_type, severity, details, created_at, is_open) VALUES (?, ?, 'dormant_wallet', 'medium', 'No recent activity', ?, 1)",
                    (wallet_id, chain, now),
                )
                if total_usd > 0:
                    conn.execute(
                        "INSERT INTO wallet_flags(wallet_id, chain, flag_type, severity, details, created_at, is_open) VALUES (?, ?, 'inactive_but_holding', 'high', 'Dormant wallet still holds value', ?, 1)",
                        (wallet_id, chain, now),
                    )
