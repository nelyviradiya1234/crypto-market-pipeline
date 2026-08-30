"""Cryptocurrency Market Intelligence Dashboard.

IMPORTANT ARCHITECTURAL RULE:
This presentation layer reads exclusively from PostgreSQL. It NEVER calls CoinGecko directly.
"""

import time
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

from src.config import get_display_name, COIN_IDS, MAX_RETRIES, RETRY_DELAYS, STALE_THRESHOLD_MINUTES
from src.database.connection import get_connection
from src.database.queries import (
    get_latest_prices,
    get_price_history,
    get_pipeline_logs,
    get_pipeline_statistics,
    get_last_successful_pull,
    insert_snapshots,
    log_pipeline_run,
)
from src.ui.styles import apply_editorial_theme
from src.ui.components import (
    render_market_snapshot,
    render_market_pulse,
    render_pipeline_timeline,
    render_footer,
)
from src.ui.charts import (
    create_editorial_line_chart,
    create_performance_bar_chart,
    create_market_cap_bar_chart,
    create_volume_bar_chart,
)
from src.api.coingecko import fetch_market_data, RateLimitError, ServerError, ClientError, APIError
from src.pipeline.validation import validate_response, ValidationError
from src.pipeline.transform import transform_records

# Page Setup
st.set_page_config(
    page_title="Market Monitor — Crypto Intelligence",
    page_icon="◩",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply Editorial Financial Styling System
apply_editorial_theme()

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


def load_data():
    """Load database connection safely."""
    try:
        conn = get_connection()
        return conn, None
    except Exception as e:
        return None, str(e)


def refresh_data_from_ui():
    """Run the data ingestion pipeline safely from the Streamlit UI.

    Unlike pull_data.run_pipeline(), this never calls sys.exit() and
    returns a (success: bool, message: str) tuple for UI feedback.
    """
    conn = None
    try:
        conn = get_connection()
    except Exception as err:
        return False, f"Database connection failed: {err}"

    # Fetch from CoinGecko with retry
    raw_data = None
    last_exception = None
    status_code_type = "api_error"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw_data = fetch_market_data(COIN_IDS)
            break
        except RateLimitError as e:
            status_code_type = "rate_limited"
            last_exception = e
        except ClientError as e:
            status_code_type = "api_error"
            last_exception = e
            break
        except (ServerError, APIError) as e:
            status_code_type = "api_error"
            last_exception = e

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAYS[attempt - 1])

    if raw_data is None:
        err_detail = str(last_exception) if last_exception else "Failed to fetch data"
        log_pipeline_run(conn, status=status_code_type, rows_written=0, error_message=err_detail)
        conn.close()
        return False, f"API fetch failed: {err_detail}"

    # Validate
    try:
        validated_data = validate_response(raw_data, expected_coin_ids=COIN_IDS)
    except ValidationError as val_err:
        log_pipeline_run(conn, status="validation_error", rows_written=0, error_message=str(val_err))
        conn.close()
        return False, f"Validation error: {val_err}"

    # Transform
    try:
        transformed_records = transform_records(validated_data, data_source="coingecko")
    except Exception as t_err:
        log_pipeline_run(conn, status="validation_error", rows_written=0, error_message=str(t_err))
        conn.close()
        return False, f"Transform error: {t_err}"

    # Insert into DB
    try:
        rows_written = insert_snapshots(conn, transformed_records)
        conn.commit()
        log_pipeline_run(conn, status="success", rows_written=rows_written, error_message=None)
        conn.close()
        return True, f"✅ Refreshed — {rows_written} rows written at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
    except Exception as db_err:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database write error: {db_err}"


def main():
    conn, error_msg = load_data()

    if error_msg:
        st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
        st.error("⚠️ DATA CONNECTION ISSUE — Unable to connect to PostgreSQL data warehouse.")
        st.info("Please verify your `DATABASE_URL` environment variable or Streamlit secrets configuration.")
        st.caption(f"Details: {error_msg}")
        return

    # Load Core Metrics
    last_pull_time = get_last_successful_pull(conn)
    stats = get_pipeline_statistics(conn)
    latest_df = get_latest_prices(conn)

    # 1. Header — Title, Freshness Pill, and Refresh Button on one clean row
    now_utc = datetime.now(timezone.utc)
    if last_pull_time:
        lp = last_pull_time.replace(tzinfo=timezone.utc) if last_pull_time.tzinfo is None else last_pull_time
        diff_minutes = int((now_utc - lp).total_seconds() / 60)
        is_stale = diff_minutes > STALE_THRESHOLD_MINUTES
        pill_class = "stale" if is_stale else "live"
        status_text = f"DATA DELAYED · {diff_minutes}M AGO" if is_stale else f"LIVE · {diff_minutes}M AGO"
    else:
        pill_class = "error"
        status_text = "PIPELINE ISSUE"

    title_col, action_col = st.columns([2.2, 1.8])

    with title_col:
        st.markdown("""
        <div>
            <div class="brand-title">
                MARKET MONITOR
                <span class="brand-title-badge">PRO</span>
            </div>
            <div class="brand-subtitle">Crypto market intelligence & pipeline health</div>
        </div>
        """, unsafe_allow_html=True)

    with action_col:
        pill_subcol, btn_subcol = st.columns([1.3, 1.0])
        with pill_subcol:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%; padding-top: 1.35rem;">
                <span class="freshness-pill {pill_class}">
                    <span class="pulse-dot"></span> {status_text}
                </span>
            </div>
            """, unsafe_allow_html=True)

        with btn_subcol:
            st.markdown("<div style='margin-top: 0.35rem;'></div>", unsafe_allow_html=True)
            if st.button("↻ Refresh", key="refresh_data_btn", use_container_width=True):
                with st.spinner("Pulling fresh data from CoinGecko..."):
                    success, message = refresh_data_from_ui()
                if success:
                    st.toast(message, icon="✅")
                    st.rerun()
                else:
                    st.toast(message, icon="❌")

    # Header divider
    st.markdown("<div style='border-bottom: 1px solid #E2E8F0; margin-bottom: 1.75rem;'></div>", unsafe_allow_html=True)

    if latest_df.empty:
        st.info("ℹ️ NO MARKET DATA AVAILABLE — Ingestion pipeline has not been executed yet.")
        st.markdown("""
        Run setup scripts to populate your database:
        - Database Schema Setup: `python init_db.py`
        - Live Data Ingestion: `python pull_data.py` (or `python generate_sample_data.py` for synthetic demo history)
        """)
        conn.close()
        return

    # 2. Main Product Section Navigation
    nav_tab1, nav_tab2, nav_tab3, nav_tab4 = st.tabs([
        "OVERVIEW",
        "MARKETS & VOLUME",
        "HISTORICAL PERFORMANCE",
        "PIPELINE HEALTH"
    ])

    coins_list = sorted(latest_df["coin_id"].unique().tolist())

    # ------------------------------------------------------------------
    # TAB 1: OVERVIEW
    # ------------------------------------------------------------------
    with nav_tab1:
        # Market Snapshot Grid
        render_market_snapshot(latest_df)

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # Price Performance Hero Section
        st.markdown("""
        <div class="section-title-bar">
            <div>
                <div class="section-label">Price Analytics</div>
                <h3 class="section-heading">Price Performance</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)

        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([3, 2, 2, 1])

        with ctrl_col1:
            selected_coins = st.multiselect(
                "Filter Assets",
                options=coins_list,
                default=coins_list[:3] if len(coins_list) >= 3 else coins_list,
                format_func=get_display_name,
                label_visibility="collapsed"
            )

        with ctrl_col2:
            chart_mode_choice = st.radio(
                "Analysis Mode",
                options=["Price (USD)", "Indexed (Base=100)"],
                index=1,
                horizontal=True,
                label_visibility="collapsed"
            )

        with ctrl_col3:
            time_option = st.radio(
                "Time Window",
                options=["24H", "3D", "7D", "30D", "ALL"],
                index=2,
                horizontal=True,
                label_visibility="collapsed"
            )

        with ctrl_col4:
            if st.button("↻ Refresh", use_container_width=True):
                st.rerun()

        hours_map = {"24H": 24, "3D": 72, "7D": 168, "30D": 720, "ALL": None}
        selected_hours = hours_map[time_option]
        calc_mode = "indexed" if "Indexed" in chart_mode_choice else "price"

        if selected_coins:
            history_df = get_price_history(conn, selected_coins=selected_coins, hours=selected_hours)
            if not history_df.empty:
                line_fig = create_editorial_line_chart(history_df, mode=calc_mode)
                st.plotly_chart(line_fig, use_container_width=True, config=PLOTLY_CONFIG)
            else:
                st.warning("No price history records found for selected query.")
        else:
            st.info("Select at least one cryptocurrency asset to display history.")

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # Market Pulse Highlights
        render_market_pulse(latest_df)

    # ------------------------------------------------------------------
    # TAB 2: MARKETS & VOLUME
    # ------------------------------------------------------------------
    with nav_tab2:
        st.markdown("""
        <div class="section-title-bar">
            <div>
                <div class="section-label">Relative Asset Comparisons</div>
                <h3 class="section-heading">Market Structure & Dynamics</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)

        m_col1, m_col2 = st.columns(2)

        with m_col1:
            bar_fig = create_performance_bar_chart(latest_df)
            st.plotly_chart(bar_fig, use_container_width=True, config=PLOTLY_CONFIG)

        with m_col2:
            mcap_fig = create_market_cap_bar_chart(latest_df)
            st.plotly_chart(mcap_fig, use_container_width=True, config=PLOTLY_CONFIG)

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        vol_fig = create_volume_bar_chart(latest_df)
        st.plotly_chart(vol_fig, use_container_width=True, config=PLOTLY_CONFIG)

    # ------------------------------------------------------------------
    # TAB 3: HISTORICAL PERFORMANCE
    # ------------------------------------------------------------------
    with nav_tab3:
        st.markdown("""
        <div class="section-title-bar">
            <div>
                <div class="section-label">Deep Historical Inspection</div>
                <h3 class="section-heading">Multi-Asset Time Series Analysis</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)

        p_col1, p_col2, p_col3 = st.columns([3, 2, 2])
        with p_col1:
            all_selected = st.multiselect(
                "Select Cryptocurrencies to Compare",
                options=coins_list,
                default=coins_list,
                format_func=get_display_name
            )
        with p_col2:
            hist_mode_choice = st.radio(
                "Historical Mode",
                options=["Price (USD)", "Indexed (Base=100)"],
                index=1,
                horizontal=True
            )
        with p_col3:
            perf_time_option = st.selectbox(
                "Time Window",
                options=["Last 24 Hours", "Last 3 Days", "Last 7 Days", "Last 30 Days", "All Data"],
                index=2
            )

        perf_hours_map = {
            "Last 24 Hours": 24,
            "Last 3 Days": 72,
            "Last 7 Days": 168,
            "Last 30 Days": 720,
            "All Data": None
        }
        hist_calc_mode = "indexed" if "Indexed" in hist_mode_choice else "price"

        if all_selected:
            full_history_df = get_price_history(conn, selected_coins=all_selected, hours=perf_hours_map[perf_time_option])
            if not full_history_df.empty:
                full_fig = create_editorial_line_chart(full_history_df, mode=hist_calc_mode)
                st.plotly_chart(full_fig, use_container_width=True, config=PLOTLY_CONFIG)
            else:
                st.warning("No historical price records found for selected criteria.")
        else:
            st.info("Select at least one cryptocurrency to view comparison.")

    # ------------------------------------------------------------------
    # TAB 4: PIPELINE HEALTH
    # ------------------------------------------------------------------
    with nav_tab4:
        logs_df = get_pipeline_logs(conn, limit=25)
        render_pipeline_timeline(stats, logs_df)

    # 3. Editorial Footer
    render_footer()

    conn.close()


if __name__ == "__main__":
    main()
