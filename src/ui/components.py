"""UI components for Editorial Financial layout."""

from datetime import datetime, timezone
import pandas as pd
import streamlit as st

from src.config import STALE_THRESHOLD_MINUTES, get_coin_symbol, get_coin_name, get_display_name


def format_currency(val: float) -> str:
    """Format numerical values into readable financial currency notation."""
    if val is None or pd.isna(val):
        return "N/A"
    if val >= 1e12:
        return f"${val / 1e12:.2f}T"
    elif val >= 1e9:
        return f"${val / 1e9:.2f}B"
    elif val >= 1e6:
        return f"${val / 1e6:.2f}M"
    elif val >= 1:
        return f"${val:,.2f}"
    else:
        return f"${val:.4f}"


def format_pct(val: float) -> str:
    """Format percentage values with sign and arrow symbol."""
    if val is None or pd.isna(val):
        return "N/A"
    if val > 0:
        return f"▲ +{val:.2f}%"
    elif val < 0:
        return f"▼ {val:.2f}%"
    else:
        return "0.00%"


def render_header(last_pull_time):
    """Render top brand title bar and compact data freshness status badge."""
    now_utc = datetime.now(timezone.utc)

    if last_pull_time:
        if last_pull_time.tzinfo is None:
            last_pull_utc = last_pull_time.replace(tzinfo=timezone.utc)
        else:
            last_pull_utc = last_pull_time

        diff_minutes = int((now_utc - last_pull_utc).total_seconds() / 60)
        is_stale = diff_minutes > STALE_THRESHOLD_MINUTES

        if is_stale:
            pill_class = "stale"
            status_text = f"● DATA DELAYED · {diff_minutes}M AGO"
        else:
            pill_class = "live"
            status_text = f"● LIVE · {diff_minutes}M AGO"
    else:
        pill_class = "error"
        status_text = "● PIPELINE ISSUE"

    st.markdown(f"""
    <div class="brand-header">
        <div>
            <div class="brand-title">
                MARKET MONITOR
                <span class="brand-title-badge">PRO</span>
            </div>
            <div class="brand-subtitle">Crypto market intelligence & pipeline health</div>
        </div>
        <div>
            <span class="freshness-pill {pill_class}">
                <span class="pulse-dot"></span> {status_text}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_market_snapshot(latest_df: pd.DataFrame):
    """Render editorial market snapshot grid displaying tracked cryptocurrencies."""
    st.markdown("""
    <div class="section-title-bar">
        <div>
            <div class="section-label">Real-Time Overview</div>
            <h3 class="section-heading">Market Snapshot</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if latest_df.empty:
        st.info("No market data available.")
        return

    coins = latest_df.to_dict("records")
    cols = st.columns(4)

    for idx, coin in enumerate(coins):
        col_idx = idx % 4
        symbol = get_coin_symbol(coin["coin_id"])
        name = get_coin_name(coin["coin_id"])
        price = coin["price_usd"]
        change = coin["change_24h_pct"]

        change_class = "positive" if (change is not None and change >= 0) else "negative"
        formatted_change = format_pct(change)
        formatted_price = f"${price:,.2f}" if price >= 1 else f"${price:.4f}"

        with cols[col_idx]:
            st.markdown(f"""
            <div class="market-card">
                <div class="coin-header-row">
                    <span><span class="coin-symbol">{symbol}</span><span class="coin-name">{name}</span></span>
                </div>
                <div class="coin-price">{formatted_price}</div>
                <div class="coin-change {change_class}">
                    {formatted_change} <span style="font-size: 0.7rem; margin-left: 0.2rem; color: #64748B;">24h</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)


def render_market_pulse(latest_df: pd.DataFrame):
    """Render Market Pulse highlighting Top Gainer, Top Loser, and Highest Volume asset."""
    if latest_df.empty:
        return

    valid_changes = latest_df.dropna(subset=["change_24h_pct"])
    top_gainer = valid_changes.sort_values(by="change_24h_pct", ascending=False).iloc[0] if not valid_changes.empty else None
    top_loser = valid_changes.sort_values(by="change_24h_pct", ascending=True).iloc[0] if not valid_changes.empty else None

    valid_vol = latest_df.dropna(subset=["volume_24h_usd"])
    top_volume = valid_vol.sort_values(by="volume_24h_usd", ascending=False).iloc[0] if not valid_vol.empty else None

    st.markdown("""
    <div class="section-title-bar">
        <div>
            <div class="section-label">Market Intelligence</div>
            <h3 class="section-heading">Market Pulse</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        if top_gainer is not None:
            g_name = get_coin_name(top_gainer["coin_id"])
            g_sym = get_coin_symbol(top_gainer["coin_id"])
            g_pct = format_pct(top_gainer["change_24h_pct"])
            st.markdown(f"""
            <div class="pulse-card">
                <div class="pulse-card-label">Top Gainer (24h)</div>
                <div class="pulse-card-val">{g_sym} <span style="font-size: 0.85rem; font-weight: 500; color: #64748B;">{g_name}</span></div>
                <div class="pulse-card-sub" style="color: #16A34A;">{g_pct}</div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        if top_loser is not None:
            l_name = get_coin_name(top_loser["coin_id"])
            l_sym = get_coin_symbol(top_loser["coin_id"])
            l_pct = format_pct(top_loser["change_24h_pct"])
            st.markdown(f"""
            <div class="pulse-card">
                <div class="pulse-card-label">Top Loser (24h)</div>
                <div class="pulse-card-val">{l_sym} <span style="font-size: 0.85rem; font-weight: 500; color: #64748B;">{l_name}</span></div>
                <div class="pulse-card-sub" style="color: #DC2626;">{l_pct}</div>
            </div>
            """, unsafe_allow_html=True)

    with c3:
        if top_volume is not None:
            v_name = get_coin_name(top_volume["coin_id"])
            v_sym = get_coin_symbol(top_volume["coin_id"])
            v_val = format_currency(top_volume["volume_24h_usd"])
            st.markdown(f"""
            <div class="pulse-card">
                <div class="pulse-card-label">Highest Volume (24h)</div>
                <div class="pulse-card-val">{v_sym} <span style="font-size: 0.85rem; font-weight: 500; color: #64748B;">{v_name}</span></div>
                <div class="pulse-card-sub" style="color: #0F172A;">{v_val}</div>
            </div>
            """, unsafe_allow_html=True)


def render_pipeline_timeline(stats: dict, logs_df: pd.DataFrame):
    """Render Pipeline Health summary metrics and clean operational log table."""
    st.markdown("""
    <div class="section-title-bar">
        <div>
            <div class="section-label">Observability & Health</div>
            <h3 class="section-heading">Pipeline Operations</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total Executions", stats.get("total_runs", 0))
    with s2:
        st.metric("Successful Runs", stats.get("successful_runs", 0))
    with s3:
        st.metric("Failed Runs", stats.get("failed_runs", 0))
    with s4:
        st.metric("Success Rate", f"{stats.get('success_rate_pct', 0.0)}%")

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    if not logs_df.empty:
        st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #64748B; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.5rem;'>Execution History</div>", unsafe_allow_html=True)

        display_logs = logs_df.copy()
        display_logs["Time (UTC)"] = pd.to_datetime(display_logs["run_at"]).dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        display_logs["Status"] = display_logs["status"].str.upper()
        display_logs["Rows Written"] = display_logs["rows_written"]
        display_logs["Description"] = display_logs["error_message"].fillna("—")

        # Select clean user-facing columns (exclude internal ID)
        clean_df = display_logs[["Time (UTC)", "Status", "Rows Written", "Description"]]

        st.dataframe(clean_df, use_container_width=True, hide_index=True)


def render_footer():
    """Render subtle editorial footer."""
    st.markdown("""
    <div class="editorial-footer">
        <div>COIN DATA PROVIDED BY COINGECKO API</div>
        <div>AUTOMATED INGESTION · SCHEDULED EVERY 30 MIN</div>
    </div>
    """, unsafe_allow_html=True)
