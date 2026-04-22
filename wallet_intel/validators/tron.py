"""Tron address validation."""
from __future__ import annotations

import base58


def validate_tron(address: str) -> tuple[bool, str | None, str | None]:
    try:
        decoded = base58.b58decode_check(address)
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)
    if len(decoded) == 21 and decoded[0] == 0x41:
        return True, address, None
    return False, None, "Tron address must be base58check with 0x41 prefix"
