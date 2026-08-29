-- Schema definition for Cryptocurrency Market Data Pipeline

-- 1. Price Snapshots Table
CREATE TABLE IF NOT EXISTS price_snapshots (
    id SERIAL PRIMARY KEY,
    coin_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    price_usd NUMERIC NOT NULL,
    market_cap_usd NUMERIC,
    volume_24h_usd NUMERIC,
    change_24h_pct NUMERIC,
    pulled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_source TEXT DEFAULT 'coingecko'
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_coin_time
ON price_snapshots (coin_id, pulled_at);

CREATE INDEX IF NOT EXISTS idx_pulled_at
ON price_snapshots (pulled_at);


-- 2. Pipeline Execution Log Table
CREATE TABLE IF NOT EXISTS pipeline_log (
    id SERIAL PRIMARY KEY,
    run_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL,
    rows_written INT DEFAULT 0,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_log_run_at
ON pipeline_log (run_at);
