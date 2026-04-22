"""CSV/Markdown report generation."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from wallet_intel.src.db import get_conn
from wallet_intel.src.utils import sha256_text, utc_now_iso


def _write_df(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def export_reports(db_path: Path, export_dir: Path) -> dict[str, Path]:
    ts = utc_now_iso().replace(":", "-")
    paths: dict[str, Path] = {}

    with get_conn(db_path) as conn:
        wallet_summary = pd.read_sql_query(
            """
            SELECT m.id, m.chain, m.public_address, m.label, m.owner_entity,
                   b.total_wallet_usd, b.snap_ts
            FROM master_wallets m
            LEFT JOIN balance_snapshots b ON b.id = (
                SELECT id FROM balance_snapshots WHERE wallet_id = m.id ORDER BY snap_ts DESC LIMIT 1
            )
            WHERE m.is_active = 1
            """,
            conn,
        )
        chain_summary = wallet_summary.groupby("chain", as_index=False).agg(
            wallets=("id", "count"),
            total_usd=("total_wallet_usd", "sum"),
        )
        anomaly_report = pd.read_sql_query(
            "SELECT * FROM wallet_flags WHERE is_open=1 ORDER BY created_at DESC", conn
        )
        dormant_wallets = anomaly_report[anomaly_report["flag_type"] == "dormant_wallet"]
        valuation_history = pd.read_sql_query(
            "SELECT wallet_id, chain, total_wallet_usd, snap_ts FROM balance_snapshots ORDER BY snap_ts DESC",
            conn,
        )
        reconciliation = pd.read_sql_query(
            "SELECT * FROM master_wallets WHERE is_active=1 ORDER BY chain, public_address", conn
        )

    outputs = {
        "wallet_summary.csv": wallet_summary,
        "chain_summary.csv": chain_summary,
        "anomaly_report.csv": anomaly_report,
        "dormant_wallets.csv": dormant_wallets,
        "valuation_history.csv": valuation_history,
        "reconciliation_export.csv": reconciliation,
    }

    for name, df in outputs.items():
        path = export_dir / f"{ts}_{name}"
        _write_df(df, path)
        paths[name] = path

    md = export_dir / f"{ts}_summary.md"
    total = float(wallet_summary["total_wallet_usd"].fillna(0).sum()) if not wallet_summary.empty else 0.0
    md.write_text(
        "\n".join(
            [
                "# Wallet Intelligence Summary",
                f"- Generated at: {utc_now_iso()}",
                f"- Active wallets: {len(wallet_summary)}",
                f"- Total portfolio USD: {total:,.2f}",
                f"- Open flags: {len(anomaly_report)}",
            ]
        )
    )
    paths["summary.md"] = md

    checksum = sha256_text("\n".join(str(p) for p in paths.values()))
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO reconciliation_exports(generated_at, export_path, checksum, notes) VALUES (?, ?, ?, ?)",
            (utc_now_iso(), str(export_dir), checksum, "Automated export batch"),
        )
    return paths
