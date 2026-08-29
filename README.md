# Cryptocurrency Market Data Pipeline & Monitoring Dashboard

An enterprise-grade, production-style cryptocurrency market data pipeline and monitoring dashboard built with Python, CoinGecko API, PostgreSQL (Neon), GitHub Actions, and Streamlit.

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
    H -->|SQL Queries| J
    I -->|Health Metrics| J
```

> ⚠️ **Key Architecture Decision**: The Streamlit presentation layer **never queries CoinGecko directly**. It queries only the PostgreSQL database. This ensures:
> 1. **Zero API rate-limit risk** from concurrent dashboard visitors.
> 2. **Complete immunity to API outages**: If CoinGecko experiences downtime, the dashboard continues to function flawlessly using historical snapshots.
> 3. **Auditability & Observability**: Every execution outcome (success, rate limit, validation failure, DB error) is persisted in `pipeline_log`.

---

## ✨ Features

- **Automated 30-Minute Ingestion**: Periodically pulls market metrics for top cryptocurrencies (Bitcoin, Ethereum, Solana, BNB, XRP, Cardano, Dogecoin, Polkadot).
- **Resilient API Client**: Handles HTTP status codes (200, 429, 400-404, 500-504), network timeouts, and transient errors using **exponential backoff retries** (5s, 15s, 45s).
- **Strict Data Validation**: Validates response structure, presence of critical fields, numeric price bounds, and complete batch arrival before database insertion.
- **Transactional Atomicity**: All snapshots within an ingestion run are written in a single database transaction (`BEGIN...COMMIT`), preventing partial batch corruption.
- **Pipeline Health Observability**: Tracks success rate, execution duration, rows written, and detailed error messages in `pipeline_log`.
- **Data Freshness Monitoring**: Real-time freshness warnings on the dashboard if snapshot data is older than 45 minutes.
- **Interactive Visualizations**: Interactive Plotly trend line charts, 24h percentage change bar graphs, and human-readable market cap ($1.27T, $415B) & volume comparisons.
- **Zero-Cost Deployment Architecture**: Compatible with Neon PostgreSQL free tier, GitHub Actions free tier, and Streamlit Cloud.

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
git clone https://github.com/your-username/crypto-market-pipeline.git
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

Output:
```text
Connecting to PostgreSQL database...
Executing schema initialization (tables & indexes)...
✅ Database initialized successfully. All tables and indexes are ready.
```

---

## 🏃 Running the Application

### Option A: Ingest Live CoinGecko Data
Execute a live market pull:

```bash
python pull_data.py
```

Output:
```text
Pipeline completed successfully.
Coins requested: 8
Coins received: 8
Rows written: 8
Pulled at: 2026-08-27 12:00:04 UTC
```

### Option B: Generate Synthetic Historical Demo Data
For development or demonstrating the dashboard with 10 days of realistic history:

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

The test suite validates data transformation, schema rules, and API exception handling (using `unittest.mock` to avoid calling live APIs):

```bash
pytest tests/ -v
```

Expected output:
```text
tests/test_api.py::test_fetch_market_data_success PASSED
tests/test_api.py::test_fetch_market_data_rate_limit PASSED
tests/test_api.py::test_fetch_market_data_server_error PASSED
tests/test_api.py::test_fetch_market_data_client_error PASSED
tests/test_api.py::test_fetch_market_data_timeout PASSED
tests/test_api.py::test_fetch_market_data_connection_error PASSED
tests/test_transform.py::test_transform_records_mapping PASSED
tests/test_transform.py::test_transform_records_null_handling PASSED
tests/test_validation.py::test_validate_response_valid PASSED
tests/test_validation.py::test_validate_response_not_a_list PASSED
tests/test_validation.py::test_validate_response_empty PASSED
tests/test_validation.py::test_validate_response_incomplete_batch PASSED
tests/test_validation.py::test_validate_response_missing_price PASSED
tests/test_validation.py::test_validate_response_negative_price PASSED
tests/test_validation.py::test_validate_response_non_numeric_price PASSED
tests/test_validation.py::test_validate_response_nullable_fields_allowed_none PASSED
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

### Manual Execution (`workflow_dispatch`)
You can trigger the ingestion pipeline on demand from GitHub:
1. Open repository on GitHub.
2. Go to **Actions** tab.
3. Select **Pull crypto prices** workflow.
4. Click **Run workflow** → **Run workflow**.

---

## ☁️ Deployment Guide (Streamlit Cloud)

1. Push code to GitHub.
2. Log in to [Streamlit Cloud](https://streamlit.io/cloud).
3. Click **New app** and select your GitHub repository and branch.
4. Set Main file path: `app.py`.
5. Under **Advanced settings → Secrets**, paste:
   ```toml
   DATABASE_URL = "postgresql://user:password@ep-example.neon.tech/neondb?sslmode=require"
   ```
6. Click **Deploy**.

---

## 🧠 Engineering & Architecture Discussion

### 1. Data Integrity & Validation Strategy
Data from external APIs cannot be trusted blindly. The pipeline enforces a validation boundary:
- **Critical Fields**: Missing prices or non-numeric prices immediately trigger `ValidationError` and stop ingestion before writing corrupt records.
- **Batch Completeness**: If CoinGecko returns fewer coins than requested (e.g., 7 instead of 8), the entire snapshot is rejected to preserve batch snapshot uniformity.
- **Transactional Storage**: Ingestion uses `BEGIN...COMMIT`. If database insertion fails halfway through a batch, a `ROLLBACK` is executed, preventing partial writes.

### 2. Failure & Rate-Limit Handling
- **HTTP 429 (Rate Limit)**: Logged as `rate_limited` in `pipeline_log`. The pipeline backs off exponentially (5s, 15s, 45s) before trying again.
- **HTTP 5xx (Server Error)**: Retried up to 3 times before failing cleanly with exit code `1`.
- **Non-zero Exit Codes**: When any stage fails, the script calls `sys.exit(1)`. This signals GitHub Actions to flag the workflow run as failed, allowing GitHub notifications to trigger.

### 3. Future Scaling Considerations
If scaling from 8 cryptocurrencies to 10,000+ assets with sub-minute ingestion intervals:
- **Asynchronous Ingestion**: Replace `requests` with `aiohttp` or `httpx` for concurrent API querying.
- **Time-Series Database**: Migrate from standard PostgreSQL to **TimescaleDB** (hyper-tables) or ClickHouse for optimized time-series compression and continuous aggregates.
- **Message Queue & Workers**: Introduce **Apache Kafka** or **RabbitMQ** with **Celery** background workers to decouple ingestion, validation, and storage.
- **Orchestration**: Transition from GitHub Actions to **Apache Airflow** or **Dagster** for dependency management, backfilling, and dynamic retries.

---

## 🔍 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **`DATABASE_URL is not set`** | Missing `.env` file or environment variable | Copy `.env.example` to `.env` and set valid database URI |
| **`CoinGecko returned HTTP 429`** | Free tier API rate limit exceeded | The script automatically retries with backoff. Wait 1-2 minutes |
| **Dashboard shows "Data may be stale"** | GitHub Actions workflow paused or failed | Check GitHub Actions tab for errors; run `python pull_data.py` manually |
| **Dashboard shows "No market data"** | Database tables are empty | Execute `python init_db.py` followed by `python pull_data.py` or `python generate_sample_data.py` |
