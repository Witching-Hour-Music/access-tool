"""Streamlit local dashboard for watch-only wallet intelligence."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from wallet_intel.src.config import load_settings
from wallet_intel.src.db import get_conn


st.set_page_config(page_title="Wallet Intelligence", layout="wide")
st.title("Local-First Watch-Only Wallet Intelligence")

settings = load_settings()

with get_conn(settings.db_path) as conn:
    wallets = pd.read_sql_query(
        "SELECT id, chain, public_address, label, owner_entity FROM master_wallets WHERE is_active=1", conn
    )
    latest_balances = pd.read_sql_query(
        """
        SELECT b.wallet_id, b.chain, b.total_wallet_usd, b.snap_ts
        FROM balance_snapshots b
        JOIN (
            SELECT wallet_id, MAX(snap_ts) max_snap
            FROM balance_snapshots
            GROUP BY wallet_id
        ) t ON t.wallet_id = b.wallet_id AND t.max_snap = b.snap_ts
        """,
        conn,
    )
    flags = pd.read_sql_query(
        "SELECT wallet_id, chain, flag_type, severity, details, created_at FROM wallet_flags WHERE is_open=1 ORDER BY created_at DESC",
        conn,
    )

total_value = float(latest_balances["total_wallet_usd"].fillna(0).sum()) if not latest_balances.empty else 0
last_update = latest_balances["snap_ts"].max() if not latest_balances.empty else "n/a"

col1, col2, col3 = st.columns(3)
col1.metric("Total Portfolio USD", f"${total_value:,.2f}")
col2.metric("Active Wallets", len(wallets))
col3.metric("Last Update", str(last_update))

st.subheader("Chain Distribution")
if not latest_balances.empty:
    chain_dist = latest_balances.groupby("chain", as_index=False)["total_wallet_usd"].sum()
    st.bar_chart(chain_dist.set_index("chain"))

st.subheader("Wallets")
st.dataframe(wallets, use_container_width=True)

st.subheader("Latest Balances")
st.dataframe(latest_balances, use_container_width=True)

st.subheader("Anomaly / Risk Alerts")
st.dataframe(flags, use_container_width=True)
