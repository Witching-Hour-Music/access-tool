import argparse
import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


async def _safe_staking_value(address: str, ton_api) -> int:
    """
    Best-effort extraction of stake amount from TON API account payload.
    Returns 0 when staking data is absent.
    """
    account_info = await ton_api.get_account_info(address)

    staking_info = getattr(account_info, "staking", None)
    if staking_info is None:
        return 0

    total = 0
    if isinstance(staking_info, dict):
        for key in ("balance", "staked", "amount", "total"):
            value = staking_info.get(key)
            if value is not None:
                try:
                    return int(str(value))
                except ValueError:
                    continue

    for attr in ("balance", "staked", "amount", "total"):
        value = getattr(staking_info, attr, None)
        if value is not None:
            try:
                total = int(str(value))
                break
            except ValueError:
                continue

    return total


async def build_master_wallet_db(include_staking: bool) -> list[dict]:
    from core.services.db import DBService
    from core.services.wallet import WalletService

    with DBService().db_session() as db_session:
        wallet_service = WalletService(db_session)
        rows = wallet_service.get_master_wallet_rows()

    if not include_staking:
        for row in rows:
            row["staked_in_pools"] = 0
        return rows

    from core.ext.tonapi import TonApiService

    ton_api = TonApiService()
    for row in rows:
        row["staked_in_pools"] = await _safe_staking_value(
            row["wallet_address"], ton_api
        )

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build master wallet dataset with balances and optional staking."
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path("config/env/.core.env"),
        help="Path to env file with DB/API settings",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/master_wallet_db.json"),
        help="Output JSON file path",
    )
    parser.add_argument(
        "--with-staking",
        action="store_true",
        help="Enrich with staked_in_pools using TON API lookups",
    )

    args = parser.parse_args()
    if args.env_file.exists():
        load_dotenv(args.env_file)
    else:
        logger.warning("Env file %s not found, using current process env", args.env_file)

    # Allow running this export against partially filled env templates.
    if not os.getenv("TELEGRAM_APP_ID"):
        os.environ["TELEGRAM_APP_ID"] = "0"

    rows = asyncio.run(build_master_wallet_db(include_staking=args.with_staking))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    logger.warning("Master wallet database exported: %s (rows=%d)", args.output, len(rows))


if __name__ == "__main__":
    main()
