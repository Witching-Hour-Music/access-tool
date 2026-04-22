PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS master_wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain TEXT NOT NULL,
    public_address TEXT NOT NULL,
    label TEXT,
    owner_entity TEXT,
    account_purpose TEXT,
    source TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1,
    tags TEXT,
    UNIQUE(chain, public_address)
);

CREATE TABLE IF NOT EXISTS wallet_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    is_valid INTEGER NOT NULL,
    normalized_address TEXT,
    validation_error TEXT,
    validated_at TEXT NOT NULL,
    FOREIGN KEY(wallet_id) REFERENCES master_wallets(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_wallet_validation_wallet_id ON wallet_validation(wallet_id);

CREATE TABLE IF NOT EXISTS balance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    chain TEXT NOT NULL,
    native_symbol TEXT,
    native_balance REAL NOT NULL DEFAULT 0,
    native_balance_usd REAL,
    total_wallet_usd REAL,
    block_ref TEXT,
    snap_ts TEXT NOT NULL,
    FOREIGN KEY(wallet_id) REFERENCES master_wallets(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_balance_wallet_time ON balance_snapshots(wallet_id, snap_ts);

CREATE TABLE IF NOT EXISTS token_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    wallet_id INTEGER NOT NULL,
    chain TEXT NOT NULL,
    token_address TEXT,
    token_symbol TEXT,
    token_name TEXT,
    token_standard TEXT,
    token_balance REAL NOT NULL,
    token_price_usd REAL,
    token_value_usd REAL,
    first_seen_at TEXT,
    last_seen_at TEXT,
    FOREIGN KEY(snapshot_id) REFERENCES balance_snapshots(id) ON DELETE CASCADE,
    FOREIGN KEY(wallet_id) REFERENCES master_wallets(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_token_wallet ON token_holdings(wallet_id, chain, token_address);

CREATE TABLE IF NOT EXISTS activity_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    chain TEXT NOT NULL,
    tx_count INTEGER DEFAULT 0,
    last_tx_hash TEXT,
    last_activity_at TEXT,
    inflow_native REAL DEFAULT 0,
    outflow_native REAL DEFAULT 0,
    snap_ts TEXT NOT NULL,
    FOREIGN KEY(wallet_id) REFERENCES master_wallets(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_activity_wallet_time ON activity_snapshots(wallet_id, snap_ts);

CREATE TABLE IF NOT EXISTS wallet_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    chain TEXT NOT NULL,
    flag_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    is_open INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(wallet_id) REFERENCES master_wallets(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_flags_wallet_open ON wallet_flags(wallet_id, is_open);

CREATE TABLE IF NOT EXISTS price_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_key TEXT NOT NULL,
    symbol TEXT,
    chain TEXT,
    price_usd REAL NOT NULL,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    UNIQUE(asset_key)
);

CREATE TABLE IF NOT EXISTS reconciliation_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at TEXT NOT NULL,
    export_path TEXT NOT NULL,
    checksum TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    status TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_event_time ON audit_log(event_type, created_at);
