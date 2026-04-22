"""Base-first reusable EVM RPC client."""
from __future__ import annotations

from web3 import Web3


class EvmRpcClient:
    def __init__(self, rpc_url: str):
        if not rpc_url:
            raise ValueError("Missing EVM RPC URL")
        self.web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 15}))

    def get_native_balance(self, address: str) -> tuple[float, int]:
        wei = self.web3.eth.get_balance(address)
        block_number = self.web3.eth.block_number
        return float(self.web3.from_wei(wei, "ether")), block_number

    def get_tx_count(self, address: str) -> int:
        return self.web3.eth.get_transaction_count(address)
