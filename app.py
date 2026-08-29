"""Cryptocurrency Market Intelligence Dashboard.

IMPORTANT ARCHITECTURAL RULE:
This presentation layer reads exclusively from PostgreSQL. It NEVER calls CoinGecko directly.
"""

from datetime import datetime, timezone
import pandas as pd
import streamlit as st

from src.config import get_display_name
from src.database.connection import get_connection
from src.database.queries import (
    get_latest_prices,
    get_price_history,
    get_pipeline_logs,
    get_pipeline_statistics,
    get_last_successful_pull,
)
from src.ui.styles import apply_editorial_theme
from src.ui.components import (
    render_header,
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

    # 1. Header & Freshness Status
    render_header(last_pull_time)

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
