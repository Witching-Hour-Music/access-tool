"""Transaction activity collection."""
from __future__ import annotations

from pathlib import Path

from wallet_intel.providers.bitcoin_api import BitcoinApiClient
from wallet_intel.providers.evm_rpc import EvmRpcClient
from wallet_intel.providers.evm_scan import EvmScanClient
from wallet_intel.providers.trongrid import TronGridClient
from wallet_intel.src.db import get_conn
from wallet_intel.src.models import Wallet
from wallet_intel.src.utils import utc_now_iso


def collect_activity(db_path: Path, wallets: list[Wallet], clients: dict) -> None:
    snap_ts = utc_now_iso()
    with get_conn(db_path) as conn:
        for w in wallets:
            chain = w.chain.lower()
            tx_count = 0
            last_tx_hash = None
            last_activity_at = None
            inflow = 0.0
            outflow = 0.0
            try:
                if chain in {"base", "ethereum", "polygon", "arbitrum", "optimism", "bsc"}:
                    rpc: EvmRpcClient = clients[f"evm_rpc:{chain}"]
                    scan: EvmScanClient | None = clients.get(f"evm_scan:{chain}")
                    tx_count = rpc.get_tx_count(w.public_address)
                    if scan:
                        txs = scan.normal_transactions(w.public_address)
                        if txs:
                            last = txs[0]
                            last_tx_hash = last.get("hash")
                            last_activity_at = last.get("timeStamp")
                elif chain == "bitcoin":
                    btc: BitcoinApiClient = clients["bitcoin"]
                    activity = btc.get_activity(w.public_address)
                    tx_count = int(activity.get("tx_count", 0))
                    last_tx_hash = activity.get("last_tx_hash")
                    last_activity_at = activity.get("last_activity_at")
                elif chain == "tron":
                    tron: TronGridClient = clients["tron"]
                    activity = tron.get_activity(w.public_address)
                    tx_count = int(activity.get("tx_count", 0))
                    last_tx_hash = activity.get("last_tx_hash")
                    last_activity_at = str(activity.get("last_activity_at")) if activity.get("last_activity_at") else None

                conn.execute(
                    """
                    INSERT INTO activity_snapshots(
                        wallet_id, chain, tx_count, last_tx_hash, last_activity_at,
                        inflow_native, outflow_native, snap_ts
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (w.id, chain, tx_count, last_tx_hash, last_activity_at, inflow, outflow, snap_ts),
                )
            except Exception as exc:  # noqa: BLE001
                conn.execute(
                    "INSERT INTO wallet_flags(wallet_id, chain, flag_type, severity, details, created_at, is_open) VALUES (?, ?, ?, ?, ?, ?, 1)",
                    (w.id, chain, "rpc_failure", "high", f"activity: {exc}", snap_ts),
                )
