"""Price caching and retrieval."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from wallet_intel.providers.pricing import PricingClient
from wallet_intel.src.db import get_conn
from wallet_intel.src.utils import utc_now_iso


logger = logging.getLogger(__name__)

COIN_MAP = {
    "ethereum": ("ethereum", "ETH"),
    "polygon": ("matic-network", "MATIC"),
    "arbitrum": ("ethereum", "ETH"),
    "optimism": ("ethereum", "ETH"),
    "base": ("ethereum", "ETH"),
    "bsc": ("binancecoin", "BNB"),
    "bitcoin": ("bitcoin", "BTC"),
    "solana": ("solana", "SOL"),
    "tron": ("tron", "TRX"),
}


def get_cached_price(db_path: Path, asset_key: str) -> float | None:
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT price_usd, expires_at FROM price_cache WHERE asset_key = ?",
            (asset_key,),
        ).fetchone()
    if not row:
        return None
    expires = datetime.fromisoformat(row["expires_at"])
    if expires > datetime.now(timezone.utc):
        return float(row["price_usd"])
    return None


def refresh_base_prices(db_path: Path, pricing: PricingClient) -> None:
    with get_conn(db_path) as conn:
        for chain, (coin_id, symbol) in COIN_MAP.items():
            asset_key = f"native:{chain}"
            price = pricing.get_price(coin_id=coin_id, symbol=symbol)
            if price is None:
                logger.warning("Price unavailable for %s", chain)
                continue
            now = datetime.now(timezone.utc)
            expires = now + timedelta(minutes=10)
            conn.execute(
                """
                INSERT INTO price_cache(asset_key, symbol, chain, price_usd, source, fetched_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_key) DO UPDATE SET
                  price_usd=excluded.price_usd,
                  source=excluded.source,
                  fetched_at=excluded.fetched_at,
                  expires_at=excluded.expires_at
                """,
                (asset_key, symbol, chain, price, "coingecko_or_cmc", utc_now_iso(), expires.isoformat()),
            )
