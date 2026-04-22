"""Balance collection and snapshot persistence."""
from __future__ import annotations

import logging
from pathlib import Path

from wallet_intel.providers.bitcoin_api import BitcoinApiClient
from wallet_intel.providers.evm_rpc import EvmRpcClient
from wallet_intel.providers.evm_scan import EvmScanClient
from wallet_intel.providers.solana_rpc import SolanaRpcClient
from wallet_intel.providers.trongrid import TronGridClient
from wallet_intel.services.pricing_service import get_cached_price
from wallet_intel.src.db import get_conn
from wallet_intel.src.models import Wallet
from wallet_intel.src.utils import utc_now_iso


logger = logging.getLogger(__name__)

NATIVE_SYMBOL = {
    "base": "ETH",
    "ethereum": "ETH",
    "polygon": "POL",
    "arbitrum": "ETH",
    "optimism": "ETH",
    "bsc": "BNB",
    "bitcoin": "BTC",
    "solana": "SOL",
    "tron": "TRX",
}


def _insert_tokens(conn, wallet_id: int, chain: str, snapshot_id: int, items: list[dict], snap_ts: str) -> float:
    total = 0.0
    for token in items:
        val = float(token.get("token_value_usd") or 0)
        total += val
        conn.execute(
            """
            INSERT INTO token_holdings(
                snapshot_id, wallet_id, chain, token_address, token_symbol,
                token_name, token_standard, token_balance, token_price_usd,
                token_value_usd, first_seen_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                wallet_id,
                chain,
                token.get("token_address"),
                token.get("token_symbol"),
                token.get("token_name"),
                token.get("token_standard"),
                float(token.get("token_balance", 0)),
                float(token.get("token_price_usd") or 0),
                val,
                snap_ts,
                snap_ts,
            ),
        )
    return total


def _evm_token_holdings(scan: EvmScanClient, wallet: Wallet) -> list[dict]:
    transfers = scan.token_transfers(wallet.public_address)
    aggregated = {}
    address_l = wallet.public_address.lower()
    for tx in transfers:
        token_addr = (tx.get("contractAddress") or "").lower()
        symbol = tx.get("tokenSymbol") or "UNK"
        name = tx.get("tokenName") or symbol
        decimals = int(tx.get("tokenDecimal") or 18)
        value = float(tx.get("value") or 0) / (10 ** decimals)
        sign = 1 if (tx.get("to") or "").lower() == address_l else -1
        k = (token_addr, symbol, name)
        aggregated[k] = aggregated.get(k, 0.0) + (sign * value)
    items = []
    for (token_addr, symbol, name), bal in aggregated.items():
        if bal > 0:
            items.append(
                {
                    "token_address": token_addr,
                    "token_symbol": symbol,
                    "token_name": name,
                    "token_standard": "ERC20",
                    "token_balance": bal,
                }
            )
    return items


def collect_balances(db_path: Path, wallets: list[Wallet], clients: dict) -> None:
    snap_ts = utc_now_iso()
    with get_conn(db_path) as conn:
        for w in wallets:
            native_balance = 0.0
            block_ref = None
            token_items = []
            chain = w.chain.lower()
            try:
                if chain in {"base", "ethereum", "polygon", "arbitrum", "optimism", "bsc"}:
                    rpc: EvmRpcClient = clients[f"evm_rpc:{chain}"]
                    scan: EvmScanClient | None = clients.get(f"evm_scan:{chain}")
                    native_balance, block_number = rpc.get_native_balance(w.public_address)
                    block_ref = str(block_number)
                    if scan:
                        token_items = _evm_token_holdings(scan, w)
                elif chain == "bitcoin":
                    btc: BitcoinApiClient = clients["bitcoin"]
                    native_balance = btc.get_native_balance(w.public_address)
                elif chain == "solana":
                    sol: SolanaRpcClient = clients["solana"]
                    native_balance = sol.get_native_balance(w.public_address)
                    token_items = sol.get_token_holdings(w.public_address)
                elif chain == "tron":
                    tron: TronGridClient = clients["tron"]
                    native_balance = tron.get_native_balance(w.public_address)
                    token_items = tron.get_trc20_holdings(w.public_address)
                else:
                    continue

                native_price = get_cached_price(db_path, f"native:{chain}") or 0
                native_usd = native_balance * native_price

                cur = conn.execute(
                    """
                    INSERT INTO balance_snapshots(
                        wallet_id, chain, native_symbol, native_balance,
                        native_balance_usd, total_wallet_usd, block_ref, snap_ts
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        w.id,
                        chain,
                        NATIVE_SYMBOL.get(chain, "UNK"),
                        native_balance,
                        native_usd,
                        native_usd,
                        block_ref,
                        snap_ts,
                    ),
                )
                snapshot_id = cur.lastrowid
                token_usd = _insert_tokens(conn, w.id, chain, snapshot_id, token_items, snap_ts)
                total = native_usd + token_usd
                conn.execute("UPDATE balance_snapshots SET total_wallet_usd=? WHERE id=?", (total, snapshot_id))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Balance collection failed wallet_id=%s chain=%s err=%s", w.id, chain, exc)
                conn.execute(
                    "INSERT INTO wallet_flags(wallet_id, chain, flag_type, severity, details, created_at, is_open) VALUES (?, ?, ?, ?, ?, ?, 1)",
                    (w.id, chain, "rpc_failure", "high", str(exc), snap_ts),
                )
