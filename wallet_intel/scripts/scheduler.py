#!/usr/bin/env python3
"""Local APScheduler job runner."""
from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from wallet_intel.services.orchestrator import run_activity, run_anomalies, run_balances, run_export, run_pricing
from wallet_intel.src.config import load_settings
from wallet_intel.src.logging_config import setup_logging


def main() -> None:
    settings = load_settings()
    setup_logging(str(settings.log_dir / "wallet_intel_scheduler.log"))

    scheduler = BlockingScheduler(timezone=settings.local_timezone)
    from pathlib import Path

    thresholds = Path("wallet_intel/config/thresholds.json")

    scheduler.add_job(lambda: run_pricing(settings), "interval", minutes=10, id="pricing_refresh")
    scheduler.add_job(lambda: run_balances(settings), "interval", minutes=15, id="balance_refresh")
    scheduler.add_job(lambda: run_activity(settings), "interval", minutes=20, id="activity_refresh")
    scheduler.add_job(lambda: run_anomalies(settings, thresholds), "interval", minutes=30, id="anomaly_scan")
    scheduler.add_job(lambda: run_export(settings), "interval", hours=1, id="report_export")

    scheduler.start()


if __name__ == "__main__":
    main()
