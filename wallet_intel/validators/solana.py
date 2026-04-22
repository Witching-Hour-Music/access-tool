"""Solana address validation."""
from __future__ import annotations

import base58


def validate_solana(address: str) -> tuple[bool, str | None, str | None]:
    try:
        raw = base58.b58decode(address)
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)
    if len(raw) == 32:
        return True, address, None
    return False, None, "Solana address must decode to 32 bytes"
