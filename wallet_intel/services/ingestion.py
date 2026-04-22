"""Wallet ingestion strictly from master_wallets table."""
from __future__ import annotations

import logging
from pathlib import Path

from wallet_intel.src.db import get_conn
from wallet_intel.src.models import Wallet
from wallet_intel.src.utils import utc_now_iso
from wallet_intel.validators.factory import validate_by_chain


logger = logging.getLogger(__name__)


def load_active_wallets(db_path: Path) -> list[Wallet]:
    with get_conn(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, chain, public_address, label, owner_entity,
                   account_purpose, source, notes, is_active, tags
            FROM master_wallets
            WHERE is_active = 1
            """
        ).fetchall()
        wallets = [Wallet(**dict(row)) for row in rows]
    logger.info("Loaded %s active wallets from master_wallets", len(wallets))
    return wallets


def validate_and_normalize_wallets(db_path: Path, wallets: list[Wallet]) -> list[Wallet]:
    seen = set()
    valid_wallets = []
    with get_conn(db_path) as conn:
        for w in wallets:
            ok, normalized, err = validate_by_chain(w.chain, w.public_address)
            conn.execute(
                """
                INSERT INTO wallet_validation(wallet_id, is_valid, normalized_address, validation_error, validated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (w.id, int(ok), normalized, err, utc_now_iso()),
            )
            if not ok:
                logger.warning("wallet_id=%s invalid: %s", w.id, err)
                continue
            key = (w.chain.lower(), normalized)
            if key in seen:
                logger.info("Skipping duplicate wallet pair %s", key)
                continue
            seen.add(key)
            w.public_address = normalized or w.public_address
            valid_wallets.append(w)
    return valid_wallets
