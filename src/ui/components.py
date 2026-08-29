"""UI components for Editorial Financial layout."""

from datetime import datetime, timezone
import pandas as pd
import streamlit as st

from src.config import STALE_THRESHOLD_MINUTES


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
    """Format percentage values with sign."""
    if val is None or pd.isna(val):
        return "N/A"
    prefix = "+" if val > 0 else ""
    return f"{prefix}{val:.2f}%"


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
            status_text = f"● DATA STALE · UPDATED {diff_minutes}M AGO"
        else:
            pill_class = "live"
            status_text = f"● LIVE DATA · {diff_minutes}M AGO"
    else:
        pill_class = "error"
        status_text = "● NO SNAPSHOTS"

    st.markdown(f"""
    <div class="brand-header">
        <div>
            <div class="brand-title">
                CRYPTO <span style="color: #94A3B8; font-weight: 300;">/</span> MARKET INTELLIGENCE
                <span class="brand-title-badge">PRO</span>
            </div>
            <div class="brand-subtitle">Automated market monitoring and historical performance analytics</div>
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
        symbol = coin["symbol"].upper()
        name = coin["coin_id"].capitalize()
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
            g_name = top_gainer["coin_id"].capitalize()
            g_sym = top_gainer["symbol"].upper()
            g_pct = format_pct(top_gainer["change_24h_pct"])
            st.markdown(f"""
            <div class="pulse-card">
                <div class="pulse-card-label">🔥 Top Gainer (24h)</div>
                <div class="pulse-card-val">{g_sym} <span style="font-size: 0.9rem; font-weight: 500; color: #64748B;">{g_name}</span></div>
                <div class="pulse-card-sub" style="color: #16A34A;">{g_pct}</div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        if top_loser is not None:
            l_name = top_loser["coin_id"].capitalize()
            l_sym = top_loser["symbol"].upper()
            l_pct = format_pct(top_loser["change_24h_pct"])
            st.markdown(f"""
            <div class="pulse-card">
                <div class="pulse-card-label">📉 Top Loser (24h)</div>
                <div class="pulse-card-val">{l_sym} <span style="font-size: 0.9rem; font-weight: 500; color: #64748B;">{l_name}</span></div>
                <div class="pulse-card-sub" style="color: #DC2626;">{l_pct}</div>
            </div>
            """, unsafe_allow_html=True)

    with c3:
        if top_volume is not None:
            v_name = top_volume["coin_id"].capitalize()
            v_sym = top_volume["symbol"].upper()
            v_val = format_currency(top_volume["volume_24h_usd"])
            st.markdown(f"""
            <div class="pulse-card">
                <div class="pulse-card-label">📊 Highest Volume (24h)</div>
                <div class="pulse-card-val">{v_sym} <span style="font-size: 0.9rem; font-weight: 500; color: #64748B;">{v_name}</span></div>
                <div class="pulse-card-sub" style="color: #0F172A;">{v_val}</div>
            </div>
            """, unsafe_allow_html=True)


def render_pipeline_timeline(stats: dict, logs_df: pd.DataFrame):
    """Render Pipeline Health summary metrics and compact operational log timeline."""
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
        st.metric("Total Ingestion Runs", stats.get("total_runs", 0))
    with s2:
        st.metric("Successful Executions", stats.get("successful_runs", 0))
    with s3:
        st.metric("Failed Runs", stats.get("failed_runs", 0))
    with s4:
        st.metric("Success Rate", f"{stats.get('success_rate_pct', 0.0)}%")

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    if not logs_df.empty:
        st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #64748B; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;'>Recent Operational Activity</div>", unsafe_allow_html=True)

        recent_entries = logs_df.head(6).to_dict("records")
        for log in recent_entries:
            run_time = pd.to_datetime(log["run_at"]).strftime("%H:%M UTC (%Y-%m-%d)")
            status = log["status"]
            rows = log["rows_written"]
            error = log["error_message"] or "Clean execution"

            st.markdown(f"""
            <div class="pipeline-status-row">
                <div>
                    <span class="pipeline-dot {status}"></span>
                    <strong style="color: #0F172A; text-transform: uppercase;">{status}</strong>
                    <span style="color: #64748B; margin-left: 0.75rem;">{run_time}</span>
                </div>
                <div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; background: #F1F5F9; padding: 0.15rem 0.4rem; border-radius: 4px; color: #334155;">{rows} rows</span>
                    <span style="color: #94A3B8; font-size: 0.75rem; margin-left: 0.5rem;">{error[:40]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("View full pipeline execution history table →"):
            st.dataframe(logs_df, use_container_width=True, hide_index=True)


def render_footer():
    """Render subtle editorial footer."""
    st.markdown("""
    <div class="editorial-footer">
        <div>COIN DATA PROVIDED BY COINGECKO API</div>
        <div>AUTOMATED INGESTION · SCHEDULED EVERY 30 MIN</div>
    </div>
    """, unsafe_allow_html=True)
