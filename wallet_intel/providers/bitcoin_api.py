"""Bitcoin API client (watch-only)."""
from __future__ import annotations

from wallet_intel.providers.base import HttpProvider


class BitcoinApiClient(HttpProvider):
    def __init__(self, base_url: str, api_key: str = ""):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def address_info(self, address: str):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        return self.get(f"{self.base_url}/addrs/{address}", headers=headers)

    def get_native_balance(self, address: str) -> float:
        data = self.address_info(address)
        sat = data.get("final_balance") or data.get("balance") or 0
        return sat / 100_000_000

    def get_activity(self, address: str):
        data = self.address_info(address)
        txrefs = data.get("txrefs", []) or data.get("txs", [])
        return {
            "tx_count": data.get("n_tx") or len(txrefs),
            "last_tx_hash": (txrefs[0].get("tx_hash") if txrefs else None),
            "last_activity_at": (txrefs[0].get("confirmed") if txrefs else None),
        }
