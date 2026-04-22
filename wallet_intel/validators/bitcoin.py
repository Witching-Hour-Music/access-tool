"""Bitcoin address validation."""
from __future__ import annotations

import re

import base58
from bech32 import bech32_decode


BASE58_RE = re.compile(r"^[123mn][a-km-zA-HJ-NP-Z1-9]{25,34}$")
BECH32_RE = re.compile(r"^(bc1|tb1)[a-z0-9]{25,87}$")


def validate_bitcoin(address: str) -> tuple[bool, str | None, str | None]:
    if BASE58_RE.match(address):
        try:
            decoded = base58.b58decode_check(address)
            if decoded:
                return True, address, None
        except Exception as exc:  # noqa: BLE001
            return False, None, str(exc)
    if BECH32_RE.match(address):
        hrp, data = bech32_decode(address)
        if hrp in {"bc", "tb"} and data:
            return True, address, None
    return False, None, "Invalid BTC address format"
