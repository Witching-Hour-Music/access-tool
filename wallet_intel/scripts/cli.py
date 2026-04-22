#!/usr/bin/env python3
"""CLI for local-first watch-only wallet intelligence."""
from __future__ import annotations

import argparse
from pathlib import Path

from wallet_intel.services.orchestrator import (
    run_activity,
    run_anomalies,
    run_balances,
    run_export,
    run_full_refresh,
    run_pricing,
)
from wallet_intel.src.config import load_settings
from wallet_intel.src.db import init_db
from wallet_intel.src.logging_config import setup_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Watch-only wallet intelligence CLI")
    parser.add_argument("command", choices=[
        "init-db",
        "run-full-refresh",
        "run-balances",
        "run-activity",
        "run-pricing",
        "run-anomalies",
        "export-reports",
    ])
    parser.add_argument("--schema", default="wallet_intel/sql/schema.sql")
    parser.add_argument("--thresholds", default="wallet_intel/config/thresholds.json")
    return parser


def main() -> None:
    settings = load_settings()
    setup_logging(str(settings.log_dir / "wallet_intel.log"))

    args = build_parser().parse_args()
    schema = Path(args.schema)
    thresholds = Path(args.thresholds)

    if args.command == "init-db":
        init_db(settings.db_path, schema)
    elif args.command == "run-full-refresh":
        run_full_refresh(settings, thresholds)
    elif args.command == "run-balances":
        run_balances(settings)
    elif args.command == "run-activity":
        run_activity(settings)
    elif args.command == "run-pricing":
        run_pricing(settings)
    elif args.command == "run-anomalies":
        run_anomalies(settings, thresholds)
    elif args.command == "export-reports":
        run_export(settings)


if __name__ == "__main__":
    main()
