"""Dataclasses for in-memory work."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Wallet:
    id: int
    chain: str
    public_address: str
    label: str | None
    owner_entity: str | None
    account_purpose: str | None
    source: str | None
    notes: str | None
    is_active: int
    tags: str | None
