"""TronGrid client."""
from __future__ import annotations

from wallet_intel.providers.base import HttpProvider


class TronGridClient(HttpProvider):
    def __init__(self, base_url: str, api_key: str = ""):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self):
        return {"TRON-PRO-API-KEY": self.api_key} if self.api_key else {}

    def account(self, address: str):
        data = self.get(f"{self.base_url}/v1/accounts/{address}", headers=self._headers())
        return (data.get("data") or [{}])[0]

    def get_native_balance(self, address: str) -> float:
        sun = self.account(address).get("balance", 0)
        return sun / 1_000_000

    def get_activity(self, address: str):
        data = self.get(
            f"{self.base_url}/v1/accounts/{address}/transactions",
            params={"limit": 1, "only_confirmed": "true", "order_by": "block_timestamp,desc"},
            headers=self._headers(),
        )
        items = data.get("data", [])
        tx = items[0] if items else {}
        return {
            "tx_count": self.account(address).get("transactions_out", 0) + self.account(address).get("transactions_in", 0),
            "last_tx_hash": tx.get("txID"),
            "last_activity_at": tx.get("block_timestamp"),
        }

    def get_trc20_holdings(self, address: str):
        acct = self.account(address)
        holdings = []
        for token_addr, raw_balance in (acct.get("trc20") or [{}])[0].items() if acct.get("trc20") else []:
            value = float(raw_balance)
            if value > 0:
                holdings.append(
                    {
                        "token_address": token_addr,
                        "token_balance": value,
                        "token_standard": "TRC20",
                    }
                )
        return holdings
