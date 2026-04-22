"""Etherscan-compatible API client for EVM chains."""
from __future__ import annotations

from wallet_intel.providers.base import HttpProvider


class EvmScanClient(HttpProvider):
    def __init__(self, base_url: str, api_key: str):
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key

    def _call(self, module: str, action: str, **kwargs):
        params = {"module": module, "action": action, "apikey": self.api_key, **kwargs}
        return self.get(self.base_url, params=params)

    def normal_transactions(self, address: str, startblock: int = 0, endblock: int = 99999999):
        data = self._call(
            "account",
            "txlist",
            address=address,
            startblock=startblock,
            endblock=endblock,
            sort="desc",
        )
        return data.get("result", []) if str(data.get("status")) == "1" else []

    def token_transfers(self, address: str, startblock: int = 0, endblock: int = 99999999):
        data = self._call(
            "account",
            "tokentx",
            address=address,
            startblock=startblock,
            endblock=endblock,
            sort="desc",
        )
        return data.get("result", []) if str(data.get("status")) == "1" else []
