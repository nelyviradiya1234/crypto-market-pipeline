# Market Monitor — Cryptocurrency Market Data Pipeline & Intelligence Dashboard

An enterprise-grade, production-style cryptocurrency market data pipeline and financial intelligence dashboard built with Python, CoinGecko API, PostgreSQL (Neon), GitHub Actions, and Streamlit.

---

## 📌 Architectural Overview

This system strictly decouples data ingestion from data visualization to guarantee operational reliability, historical persistence, and dashboard resilience against third-party API downtime.

```mermaid
flowchart TD
    subgraph Data Source
        A[CoinGecko Market API]
    end

    subgraph Scheduled Automation
        B[GitHub Actions<br/>Cron: */30 * * * *]
    end

    subgraph Data Pipeline
        C[pull_data.py]
        D[Validation Engine]
        E[Transformation Engine]
        F[Logging & Observability]
    end

    subgraph Database Storage
        G[(Neon PostgreSQL)]
        H[(price_snapshots)]
        I[(pipeline_log)]
    end

    subgraph Visualization Layer
        J[Streamlit Dashboard<br/>app.py]
    end

    B -->|Triggers every 30m| C
    A -->|HTTPS /coins/markets| C
    C --> D
    D --> E
    E -->|Transactional INSERT| H
    C -->|Run Status & Stats| I
    H -->|Read-Only SQL Queries| J
    I -->|Health Metrics| J
```

> ⚠️ **Key Architecture Decision**: The Streamlit presentation layer **never queries CoinGecko directly**. It queries only the PostgreSQL database. This ensures:
> 1. **Zero API rate-limit risk** from concurrent dashboard visitors.
> 2. **Complete immunity to API outages**: If CoinGecko experiences downtime, the dashboard continues to function flawlessly using historical snapshots.
> 3. **Auditability & Observability**: Every execution outcome (success, rate limit, validation failure, DB error) is persisted in `pipeline_log`.

---

## ✨ Key Features & Capabilities

- **Dual Analysis Modes**:
  - **Absolute Price (USD)**: Shows actual USD prices ($78,800 BTC vs $0.21 ADA).
  - **Indexed Relative Performance (Base = 100)**: Normalizes initial prices to 100, allowing direct percentage return comparison across assets with radically different price scales.
- **Centralized Coin Metadata**: Professional display names (`BTC — Bitcoin`, `ETH — Ethereum`, `SOL — Solana`, `BNB — Binance Coin`, `XRP — Ripple`, `ADA — Cardano`, `DOGE — Dogecoin`, `DOT — Polkadot`).
- **Automated 30-Minute Ingestion**: Periodically pulls market metrics for top cryptocurrencies via GitHub Actions.
- **Resilient API Client**: Handles HTTP status codes (200, 429, 400-404, 500-504) and transient errors using **exponential backoff retries** (5s, 15s, 45s).
- **Strict Data Validation**: Validates response structure, presence of critical fields, numeric price bounds, and complete batch arrival before database insertion.
- **Transactional Atomicity**: All snapshots within an ingestion run are written in a single database transaction (`BEGIN...COMMIT`), preventing partial batch corruption.
- **Operational Observability**: Tracks execution metrics, total runs, success rate %, and detailed error messages in `pipeline_log`.
- **Data Freshness Monitoring**: Real-time freshness badge on the dashboard (`● LIVE · 2M AGO`) with automated delay warnings if data is > 45 minutes old.
- **Clean Restyled Visualizations**: Custom Plotly line charts, horizontal zero-baseline 24h mover charts, and market cap & trading volume bar graphs with clean tooltips and hidden modebars.

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ | Core pipeline & application logic |
| **Data Source** | CoinGecko API (`/coins/markets`) | External REST API for market prices |
| **Database** | PostgreSQL / Neon | Transactional storage for snapshots & logs |
| **DB Driver** | `psycopg2-binary` | PostgreSQL connection driver |
| **Visualization** | Streamlit, Plotly, pandas | Interactive analytics web application |
| **Automation** | GitHub Actions | Scheduled workflow runner (30-min cron) |
| **Testing** | `pytest` | Unit test suite with API mocking |

---

## 🗄️ Database Schema

The database consists of two main tables created via `init_db.py` (defined in `sql/schema.sql`):

### 1. `price_snapshots`
Stores every individual market observation snapshot.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Unique record identifier |
| `coin_id` | `TEXT` | `NOT NULL` | Cryptocurrency slug (e.g., `bitcoin`, `solana`) |
| `symbol` | `TEXT` | `NOT NULL` | Uppercase symbol (e.g., `BTC`, `SOL`) |
| `price_usd` | `NUMERIC` | `NOT NULL` | Current price in USD |
| `market_cap_usd` | `NUMERIC` | `NULLABLE` | Market capitalization in USD |
| `volume_24h_usd` | `NUMERIC` | `NULLABLE` | 24-hour trading volume in USD |
| `change_24h_pct` | `NUMERIC` | `NULLABLE` | 24-hour percentage price change |
| `pulled_at` | `TIMESTAMPTZ` | `NOT NULL` | Snapshot timestamp in UTC |
| `data_source` | `TEXT` | `DEFAULT 'coingecko'` | Source identifier (`coingecko` or `synthetic`) |

**Indexes**:
- `idx_coin_time ON price_snapshots (coin_id, pulled_at)`
- `idx_pulled_at ON price_snapshots (pulled_at)`

### 2. `pipeline_log`
Tracks pipeline execution metrics and failures.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Unique log entry identifier |
| `run_at` | `TIMESTAMPTZ` | `NOT NULL` | Pipeline execution timestamp in UTC |
| `status` | `TEXT` | `NOT NULL` | Run outcome (`success`, `rate_limited`, `api_error`, `validation_error`, `db_error`) |
| `rows_written` | `INT` | `DEFAULT 0` | Total snapshots written to DB |
| `error_message` | `TEXT` | `NULLABLE` | Exception message or detailed failure context |

---

## 🚀 Local Setup & Installation

### 1. Prerequisites
- Python 3.11 or higher
- Git
- PostgreSQL database instance (Neon free tier recommended or local PostgreSQL)

### 2. Clone Repository & Install Dependencies
```bash
git clone https://github.com/nelyviradiya1234/crypto-market-pipeline.git
cd crypto-market-pipeline

# Create virtual environment
python -m venv venv
# Activate on Windows:
venv\Scripts\activate
# Activate on Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and set your PostgreSQL connection string:

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql://user:password@ep-example-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### 4. Initialize Database
Run the idempotent schema initialization script to create tables and indexes:

```bash
python init_db.py
```

---

## 🏃 Running the Application

### Option A: Ingest Live CoinGecko Data
Execute a live market pull:

```bash
python pull_data.py
```

### Option B: Generate Synthetic Historical Demo Data
For development or demonstrating the dashboard with 7 days of realistic 30-minute history:

```bash
python generate_sample_data.py
```

### Launch the Streamlit Dashboard
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🧪 Running Unit Tests

```bash
pytest tests/ -v
```

---

## ⚙️ Scheduled Automation with GitHub Actions

The workflow file `.github/workflows/pull.yml` automates snapshot collection every 30 minutes.

### Setting Up GitHub Secrets
1. Push your repository to GitHub.
2. Navigate to: **Settings → Secrets and variables → Actions**.
3. Click **New repository secret**.
4. Name: `DATABASE_URL`
5. Value: `<your_neon_postgresql_connection_string>`
6. Click **Add secret**.
