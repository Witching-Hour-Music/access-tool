"""Export a master wallet dataset for debugging and offline analysis."""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def _read_value(payload: Any, *names: str) -> Any:
    for name in names:
        if isinstance(payload, dict) and name in payload:
            return payload[name]
        if hasattr(payload, name):
            return getattr(payload, name)
    return None


def _iter_pool_items(pools_payload: Any) -> list[Any]:
    if pools_payload is None:
        return []
    if isinstance(pools_payload, list | tuple):
        return list(pools_payload)
    for name in ("pools", "items", "nominators_pools", "accounts"):
        value = _read_value(pools_payload, name)
        if value is not None:
            return list(value)
    return []


def _pool_staking_amount(pool: Any) -> int:
    value = _read_value(
        pool,
        "amount",
        "balance",
        "staked",
        "stake",
        "user_stake",
        "nominator_stake",
        "validator_stake",
    )
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.debug("Ignoring unparsable staking pool amount %r", value)
        return 0


async def _safe_staking_value(ton_api: Any, address: str) -> int:
    """Return total nominators-pool stake for a wallet, or 0 on lookup failure."""
    try:
        pools_payload = await ton_api.get_account_nominators_pools(address)
    except Exception:
        logger.warning("Failed to fetch staking pools for %s", address, exc_info=True)
        return 0

    return sum(_pool_staking_amount(pool) for pool in _iter_pool_items(pools_payload))


async def _build_rows(with_staking: bool) -> list[dict[str, Any]]:
    from core.db import SessionLocal
    from core.ext.tonapi import TonApiService
    from core.services.wallet import WalletService

    with SessionLocal() as db_session:
        rows = WalletService(db_session).get_master_wallet_rows()

    if with_staking:
        ton_api = TonApiService()
        for row in rows:
            row["staked_in_pools"] = await _safe_staking_value(ton_api, row["address"])

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="JSON output path")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path("config/env_template/.core.env"),
        help="Environment file to load before connecting to services",
    )
    parser.add_argument(
        "--with-staking",
        action="store_true",
        help="Best-effort enrich rows with TON nominators-pool stake",
    )
    args = parser.parse_args()

    if args.env_file.exists():
        load_dotenv(args.env_file, override=True)

    rows = asyncio.run(_build_rows(args.with_staking))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
