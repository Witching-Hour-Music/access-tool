"""End-to-end orchestration and dependency wiring."""
from __future__ import annotations

from pathlib import Path

from wallet_intel.providers.bitcoin_api import BitcoinApiClient
from wallet_intel.providers.evm_rpc import EvmRpcClient
from wallet_intel.providers.evm_scan import EvmScanClient
from wallet_intel.providers.pricing import PricingClient
from wallet_intel.providers.solana_rpc import SolanaRpcClient
from wallet_intel.providers.trongrid import TronGridClient
from wallet_intel.services.activity import collect_activity
from wallet_intel.services.anomaly import run_anomaly_scan
from wallet_intel.services.balances import collect_balances
from wallet_intel.services.ingestion import load_active_wallets, validate_and_normalize_wallets
from wallet_intel.services.pricing_service import refresh_base_prices
from wallet_intel.services.reporting import export_reports
from wallet_intel.services.risk import evaluate_risk
from wallet_intel.src.config import Settings
from wallet_intel.src.db import get_conn
from wallet_intel.src.utils import utc_now_iso


def build_clients(settings: Settings) -> dict:
    clients = {}
    for chain, rpc_url in settings.evm_rpc.items():
        if rpc_url:
            clients[f"evm_rpc:{chain}"] = EvmRpcClient(rpc_url)
        api_key = settings.scan_api_keys.get(chain, "")
        api_url = settings.scan_api_urls.get(chain, "")
        if api_key and api_url:
            clients[f"evm_scan:{chain}"] = EvmScanClient(api_url, api_key)

    if settings.solana_rpc_url:
        clients["solana"] = SolanaRpcClient(settings.solana_rpc_url)
    if settings.bitcoin_api_url:
        clients["bitcoin"] = BitcoinApiClient(settings.bitcoin_api_url, settings.bitcoin_api_key)
    if settings.tron_rpc_url:
        clients["tron"] = TronGridClient(settings.tron_rpc_url, settings.trongrid_api_key)

    clients["pricing"] = PricingClient(settings.coingecko_api_key, settings.coinmarketcap_api_key)
    return clients


def _audit(db_path: Path, event_type: str, status: str, details: str) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO audit_log(event_type, entity_type, entity_id, status, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (event_type, "system", "0", status, details, utc_now_iso()),
        )


def run_balances(settings: Settings) -> None:
    clients = build_clients(settings)
    wallets = validate_and_normalize_wallets(settings.db_path, load_active_wallets(settings.db_path))
    refresh_base_prices(settings.db_path, clients["pricing"])
    collect_balances(settings.db_path, wallets, clients)
    _audit(settings.db_path, "run_balances", "ok", f"wallets={len(wallets)}")


def run_activity(settings: Settings) -> None:
    clients = build_clients(settings)
    wallets = validate_and_normalize_wallets(settings.db_path, load_active_wallets(settings.db_path))
    collect_activity(settings.db_path, wallets, clients)
    _audit(settings.db_path, "run_activity", "ok", f"wallets={len(wallets)}")


def run_pricing(settings: Settings) -> None:
    clients = build_clients(settings)
    refresh_base_prices(settings.db_path, clients["pricing"])
    _audit(settings.db_path, "run_pricing", "ok", "price cache refreshed")


def run_anomalies(settings: Settings, thresholds_path: Path) -> None:
    run_anomaly_scan(settings.db_path, thresholds_path)
    evaluate_risk(settings.db_path, thresholds_path)
    _audit(settings.db_path, "run_anomalies", "ok", "anomalies/risk evaluated")


def run_full_refresh(settings: Settings, thresholds_path: Path) -> None:
    run_pricing(settings)
    run_balances(settings)
    run_activity(settings)
    run_anomalies(settings, thresholds_path)


def run_export(settings: Settings) -> dict[str, Path]:
    out = export_reports(settings.db_path, settings.export_dir)
    _audit(settings.db_path, "export_reports", "ok", f"files={len(out)}")
    return out
