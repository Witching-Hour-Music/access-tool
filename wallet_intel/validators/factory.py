"""Validation router by chain."""
from __future__ import annotations

from wallet_intel.validators.bitcoin import validate_bitcoin
from wallet_intel.validators.evm import validate_evm
from wallet_intel.validators.solana import validate_solana
from wallet_intel.validators.tron import validate_tron


EVM_CHAINS = {"base", "ethereum", "polygon", "arbitrum", "optimism", "bsc"}


def validate_by_chain(chain: str, address: str) -> tuple[bool, str | None, str | None]:
    c = chain.lower()
    if c in EVM_CHAINS:
        return validate_evm(address)
    if c == "bitcoin":
        return validate_bitcoin(address)
    if c == "solana":
        return validate_solana(address)
    if c == "tron":
        return validate_tron(address)
    return False, None, f"Unsupported chain: {chain}"
