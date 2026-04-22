# Local-First Watch-Only Wallet Intelligence Platform

This project is a **watch-only** wallet command center. It only uses public addresses present in `master_wallets` and never requests/handles private keys, seed phrases, or wallet passwords.

## Safety Guarantees
- Uses **only** wallets that already exist in `master_wallets`.
- Never scans disk, browser, or memory for wallets.
- Never imports, exports, or derives private key material.
- Uses only public RPC/API data.

## Structure
- `src/` core config, DB, logging, utilities.
- `providers/` RPC/API clients (EVM, Solana, Bitcoin, Tron, pricing).
- `validators/` chain-specific address validation.
- `services/` ingestion, balances, activity, snapshots, anomaly/risk, reporting.
- `scripts/` CLI + scheduler entrypoints.
- `dashboard/` Streamlit app.
- `sql/schema.sql` SQLite schema.
- `config/thresholds.json` anomaly/risk thresholds.
- `data/` local database, exports, logs, cache.

## Setup
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r wallet_intel/requirements.txt
cp wallet_intel/.env.example .env
```

Set `.env` values for your RPC/API endpoints.

## Initialize DB
```bash
python wallet_intel/scripts/cli.py init-db
```

> This creates all required tables, including `master_wallets`.

## Add Wallets (Manual Only)
You must manually insert records into `master_wallets`.

Example (manual SQL):
```sql
INSERT INTO master_wallets(chain, public_address, label, owner_entity, account_purpose, source, notes, is_active, tags)
VALUES ('polygon','0x851d5fa26636df46b6196879582324c311556b46','Nike Swoosh Contract','self','tracking','manual','watch-only',1,'brand,contract');
```

## CLI Commands
```bash
python wallet_intel/scripts/cli.py init-db
python wallet_intel/scripts/cli.py run-full-refresh
python wallet_intel/scripts/cli.py run-balances
python wallet_intel/scripts/cli.py run-activity
python wallet_intel/scripts/cli.py run-pricing
python wallet_intel/scripts/cli.py run-anomalies
python wallet_intel/scripts/cli.py export-reports
```

## Scheduler
```bash
python wallet_intel/scripts/scheduler.py
```

Jobs:
- balance refresh
- activity refresh
- pricing refresh
- anomaly scan
- report export

## Reports
Generated in `EXPORT_DIR`:
- `wallet_summary.csv`
- `chain_summary.csv`
- `anomaly_report.csv`
- `dormant_wallets.csv`
- `valuation_history.csv`
- `reconciliation_export.csv`
- markdown summary

## Dashboard
```bash
streamlit run wallet_intel/dashboard/app.py
```

Shows:
- total portfolio value
- wallet list
- chain distribution
- anomaly alerts
- last update time

## Cron-compatible examples
```bash
*/15 * * * * cd /workspace/access-tool && /usr/bin/python wallet_intel/scripts/cli.py run-balances
*/20 * * * * cd /workspace/access-tool && /usr/bin/python wallet_intel/scripts/cli.py run-activity
*/10 * * * * cd /workspace/access-tool && /usr/bin/python wallet_intel/scripts/cli.py run-pricing
*/30 * * * * cd /workspace/access-tool && /usr/bin/python wallet_intel/scripts/cli.py run-anomalies
0 * * * * cd /workspace/access-tool && /usr/bin/python wallet_intel/scripts/cli.py export-reports
```
