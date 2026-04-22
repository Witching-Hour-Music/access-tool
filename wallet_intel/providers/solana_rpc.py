"""Solana RPC watch-only client."""
from __future__ import annotations

from wallet_intel.providers.base import HttpProvider


class SolanaRpcClient(HttpProvider):
    def __init__(self, rpc_url: str):
        super().__init__()
        self.rpc_url = rpc_url

    def _rpc(self, method: str, params: list):
        return self.post(self.rpc_url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})

    def get_native_balance(self, address: str) -> float:
        lamports = self._rpc("getBalance", [address]).get("result", {}).get("value", 0)
        return lamports / 1_000_000_000

    def get_token_holdings(self, address: str):
        res = self._rpc(
            "getTokenAccountsByOwner",
            [address, {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, {"encoding": "jsonParsed"}],
        )
        items = []
        for entry in res.get("result", {}).get("value", []):
            info = entry.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
            mint = info.get("mint")
            token_amount = info.get("tokenAmount", {})
            ui_amount = token_amount.get("uiAmount") or 0
            if mint and ui_amount:
                items.append({"token_address": mint, "token_balance": float(ui_amount), "token_standard": "SPL"})
        return items
