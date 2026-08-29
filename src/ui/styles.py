"""Design system CSS styles for Warm Light / Editorial Financial UI/UX."""

import streamlit as st

EDITORIAL_CSS = """
<style>
    /* Google Font Imports */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global Theme Overrides */
    html, body, [class*="st-"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        color: #0F172A;
    }

    /* Page Background */
    .stApp {
        background-color: #F8F9FA !important;
    }

    /* Hide Streamlit Header Overlay & Sidebar */
    [data-testid="stSidebar"] {
        display: none !important;
    }

    [data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 10 !important;
    }

    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Main Container Padding Reset (plenty of top clearance) */
    .block-container {
        padding-top: 4.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1280px !important;
    }

    /* Header Brand Bar */
    .brand-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 1.25rem;
        margin-bottom: 1.75rem;
    }

    .brand-title {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #0F172A;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .brand-title-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 500;
        background-color: #0F172A;
        color: #FFFFFF;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        letter-spacing: 0.05em;
    }

    .brand-subtitle {
        font-size: 0.875rem;
        color: #64748B;
        margin-top: 0.25rem;
        font-weight: 400;
    }

    /* Freshness Indicator Badge */
    .freshness-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        text-transform: uppercase;
        border: 1px solid transparent;
    }

    .freshness-pill.live {
        background-color: #F0FDF4;
        color: #16A34A;
        border-color: #DCFCE7;
    }

    .freshness-pill.stale {
        background-color: #FFFBEB;
        color: #D97706;
        border-color: #FEF3C7;
    }

    .freshness-pill.error {
        background-color: #FEF2F2;
        color: #DC2626;
        border-color: #FEE2E2;
    }

    .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
    }

    .live .pulse-dot { background-color: #16A34A; }
    .stale .pulse-dot { background-color: #D97706; }
    .error .pulse-dot { background-color: #DC2626; }

    /* Section Titles */
    .section-title-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    .section-label {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .section-heading {
        font-size: 1.125rem;
        font-weight: 600;
        color: #0F172A;
        margin: 0;
        letter-spacing: -0.01em;
    }

    /* Market Snapshot Item Cards */
    .market-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem 1.15rem;
        transition: all 0.15s ease-in-out;
        height: 100%;
    }

    .market-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    .coin-header-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 0.5rem;
    }

    .coin-symbol {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.95rem;
        color: #0F172A;
    }

    .coin-name {
        font-size: 0.75rem;
        color: #64748B;
        margin-left: 0.35rem;
    }

    .coin-price {
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #0F172A;
        margin: 0;
    }

    .coin-change {
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        margin-top: 0.35rem;
    }

    .coin-change.positive { color: #16A34A; }
    .coin-change.negative { color: #DC2626; }

    /* Market Pulse Cards */
    .pulse-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.1rem;
        height: 100%;
    }

    .pulse-card-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #64748B;
        margin-bottom: 0.4rem;
    }

    .pulse-card-val {
        font-size: 1.2rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.1rem;
    }

    .pulse-card-sub {
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* Pipeline Status Indicators */
    .pipeline-status-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0.8rem;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        margin-bottom: 0.4rem;
        font-size: 0.825rem;
    }

    .pipeline-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
        display: inline-block;
    }

    .pipeline-dot.success { background-color: #16A34A; }
    .pipeline-dot.rate_limited { background-color: #D97706; }
    .pipeline-dot.api_error, .pipeline-dot.db_error, .pipeline-dot.validation_error { background-color: #DC2626; }

    /* Streamlit Tabs Overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
        border-bottom: 1px solid #E2E8F0;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 2.75rem;
        background-color: transparent;
        border: none;
        color: #64748B;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0;
        letter-spacing: 0.02em;
    }

    .stTabs [aria-selected="true"] {
        color: #0F172A !important;
        border-bottom: 2px solid #0F172A !important;
        background-color: transparent !important;
    }

    /* Streamlit Buttons Overrides */
    .stButton > button {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        padding: 0.35rem 0.85rem !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
        transition: all 0.15s ease !important;
    }

    .stButton > button:hover {
        border-color: #0F172A !important;
        background-color: #F8FAFC !important;
    }

    /* DataFrame Table Styling */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
        background: #FFFFFF;
    }

    /* Footer Styling */
    .editorial-footer {
        border-top: 1px solid #E2E8F0;
        padding-top: 1.5rem;
        margin-top: 3.5rem;
        display: flex;
        justify-content: space-between;
        color: #94A3B8;
        font-size: 0.75rem;
        letter-spacing: 0.03em;
    }
</style>
"""


def apply_editorial_theme():
    """Inject custom editorial CSS theme into Streamlit app."""
    st.markdown(EDITORIAL_CSS, unsafe_allow_html=True)
