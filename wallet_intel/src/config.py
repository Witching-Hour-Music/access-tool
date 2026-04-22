"""Environment-driven configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_path: Path
    export_dir: Path
    log_dir: Path
    cache_dir: Path
    local_timezone: str

    evm_rpc: dict[str, str]
    scan_api_keys: dict[str, str]
    scan_api_urls: dict[str, str]

    solana_rpc_url: str
    bitcoin_api_url: str
    bitcoin_api_key: str
    trongrid_api_key: str
    tron_rpc_url: str

    coingecko_api_key: str
    coinmarketcap_api_key: str


SCAN_BASE_URLS = {
    "ethereum": "https://api.etherscan.io/api",
    "polygon": "https://api.polygonscan.com/api",
    "arbitrum": "https://api.arbiscan.io/api",
    "optimism": "https://api-optimistic.etherscan.io/api",
    "base": "https://api.basescan.org/api",
    "bsc": "https://api.bscscan.com/api",
}


def load_settings() -> Settings:
    db_path = Path(os.getenv("DB_PATH", "./wallet_intel/data/wallet_intel.db"))
    export_dir = Path(os.getenv("EXPORT_DIR", "./wallet_intel/data/exports"))
    log_dir = Path(os.getenv("LOG_DIR", "./wallet_intel/data/logs"))
    cache_dir = Path(os.getenv("CACHE_DIR", "./wallet_intel/data/cache"))

    for p in (db_path.parent, export_dir, log_dir, cache_dir):
        p.mkdir(parents=True, exist_ok=True)

    return Settings(
        db_path=db_path,
        export_dir=export_dir,
        log_dir=log_dir,
        cache_dir=cache_dir,
        local_timezone=os.getenv("LOCAL_TIMEZONE", "UTC"),
        evm_rpc={
            "base": os.getenv("EVM_RPC_BASE", ""),
            "ethereum": os.getenv("EVM_RPC_ETH", ""),
            "polygon": os.getenv("EVM_RPC_POLYGON", ""),
            "arbitrum": os.getenv("EVM_RPC_ARBITRUM", ""),
            "optimism": os.getenv("EVM_RPC_OPTIMISM", ""),
            "bsc": os.getenv("EVM_RPC_BSC", ""),
        },
        scan_api_keys={
            "ethereum": os.getenv("ETHERSCAN_API_KEY", ""),
            "polygon": os.getenv("POLYGONSCAN_API_KEY", ""),
            "arbitrum": os.getenv("ARBISCAN_API_KEY", ""),
            "optimism": os.getenv("OPTIMISMSCAN_API_KEY", ""),
            "base": os.getenv("BASESCAN_API_KEY", ""),
            "bsc": os.getenv("BSCSCAN_API_KEY", ""),
        },
        scan_api_urls=SCAN_BASE_URLS,
        solana_rpc_url=os.getenv("SOLANA_RPC_URL", ""),
        bitcoin_api_url=os.getenv("BITCOIN_API_URL", ""),
        bitcoin_api_key=os.getenv("BITCOIN_API_KEY", ""),
        trongrid_api_key=os.getenv("TRONGRID_API_KEY", ""),
        tron_rpc_url=os.getenv("TRON_RPC_URL", ""),
        coingecko_api_key=os.getenv("COINGECKO_API_KEY", ""),
        coinmarketcap_api_key=os.getenv("COINMARKETCAP_API_KEY", ""),
    )
