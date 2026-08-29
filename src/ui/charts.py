"""Restyled Plotly visualization functions for Editorial Financial presentation."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.config import COIN_METADATA, get_coin_symbol, get_coin_name, get_display_name

# Editorial Palette
EDITORIAL_PALETTE = {
    "bitcoin": "#0F172A",      # Dark Slate
    "ethereum": "#2563EB",     # Royal Blue
    "solana": "#16A34A",       # Emerald Green
    "binancecoin": "#D97706",  # Amber Gold
    "ripple": "#8B5CF6",       # Deep Purple
    "cardano": "#EC4899",      # Vibrant Pink
    "dogecoin": "#14B8A6",     # Teal
    "polkadot": "#F97316",     # Vibrant Orange
}

FALLBACK_PALETTE = ["#0F172A", "#2563EB", "#16A34A", "#D97706", "#8B5CF6", "#EC4899", "#14B8A6", "#F97316"]


def apply_editorial_chart_layout(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    """Apply consistent editorial styling to Plotly figure objects."""
    fig.update_layout(
        title={
            "text": title if title else None,
            "font": {"family": "Inter, sans-serif", "size": 14, "color": "#0F172A", "weight": 600},
            "x": 0.0,
            "xanchor": "left",
            "y": 0.98,
            "yanchor": "top"
        } if title else None,
        font={"family": "Inter, sans-serif", "color": "#64748B", "size": 12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin={"l": 10, "r": 15, "t": 55 if title else 25, "b": 25},
        xaxis={
            "showgrid": True,
            "gridcolor": "#F1F5F9",
            "gridwidth": 1,
            "zeroline": False,
            "linecolor": "#E2E8F0",
            "tickfont": {"size": 11, "color": "#64748B"}
        },
        yaxis={
            "showgrid": True,
            "gridcolor": "#F1F5F9",
            "gridwidth": 1,
            "zeroline": False,
            "linecolor": "#E2E8F0",
            "tickfont": {"size": 11, "color": "#64748B"}
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
            "font": {"size": 11, "color": "#0F172A", "family": "Inter, sans-serif"},
            "title": None,
            "bgcolor": "rgba(0,0,0,0)"
        },
        hoverlabel={
            "bgcolor": "#0F172A",
            "font_size": 12,
            "font_family": "Inter, sans-serif",
            "font_color": "#FFFFFF"
        }
    )
    return fig


def create_editorial_line_chart(df: pd.DataFrame, mode: str = "price") -> go.Figure:
    """Create line chart for price time-series with Absolute Price or Indexed Performance mode.

    Args:
        df: DataFrame containing price history.
        mode: 'price' (USD) or 'indexed' (Base = 100).
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No historical price data available for selected query.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font={"size": 13, "color": "#94A3B8"}
        )
        return apply_editorial_chart_layout(fig, height=380)

    plot_df = df.copy()
    plot_df["pulled_at"] = pd.to_datetime(plot_df["pulled_at"])
    plot_df = plot_df.sort_values(by=["coin_id", "pulled_at"])

    # User-friendly display names
    plot_df["display_name"] = plot_df["coin_id"].apply(get_display_name)
    plot_df["symbol_label"] = plot_df["coin_id"].apply(get_coin_symbol)

    fig = go.Figure()

    unique_coins = plot_df["coin_id"].unique()

    for coin_id in unique_coins:
        coin_data = plot_df[plot_df["coin_id"] == coin_id].copy()
        if coin_data.empty:
            continue

        symbol = get_coin_symbol(coin_id)
        name = get_coin_name(coin_id)
        color = EDITORIAL_PALETTE.get(coin_id, "#0F172A")

        if mode == "indexed":
            first_price = coin_data["price_usd"].iloc[0]
            if first_price > 0:
                coin_data["y_val"] = (coin_data["price_usd"] / first_price) * 100.0
            else:
                coin_data["y_val"] = 100.0
            
            hovertemplate = (
                f"<b>{name} ({symbol})</b><br>"
                "Time: %{x|%b %d, %H:%M UTC}<br>"
                "Indexed Value: %{y:.1f}<br>"
                "<extra></extra>"
            )
        else:
            coin_data["y_val"] = coin_data["price_usd"]
            hovertemplate = (
                f"<b>{name} ({symbol})</b><br>"
                "Time: %{x|%b %d, %H:%M UTC}<br>"
                "Price: $%{y:,.2f}<br>"
                "<extra></extra>"
            )

        fig.add_trace(go.Scatter(
            x=coin_data["pulled_at"],
            y=coin_data["y_val"],
            mode="lines",
            name=f"{symbol} ({name})",
            line={"width": 2.2, "color": color},
            hovertemplate=hovertemplate
        ))

    if mode == "indexed":
        fig.update_yaxes(title=None, ticksuffix="")
        title = "Relative Asset Performance (Indexed to 100)"
    else:
        fig.update_yaxes(title=None, tickprefix="$")
        title = "Absolute USD Price History"

    fig.update_xaxes(title=None)
    return apply_editorial_chart_layout(fig, title=title, height=440)


def create_performance_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create horizontal zero-baseline bar chart for 24h percentage change."""
    if df.empty:
        fig = go.Figure()
        return apply_editorial_chart_layout(fig, height=360)

    plot_df = df.sort_values(by="change_24h_pct", ascending=True).copy()
    plot_df["color"] = plot_df["change_24h_pct"].apply(lambda x: "#16A34A" if x >= 0 else "#DC2626")
    plot_df["formatted_text"] = plot_df["change_24h_pct"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
    plot_df["asset_label"] = plot_df["coin_id"].apply(lambda c: f"{get_coin_symbol(c)} — {get_coin_name(c)}")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=plot_df["asset_label"],
        x=plot_df["change_24h_pct"],
        orientation="h",
        marker={"color": plot_df["color"]},
        text=plot_df["formatted_text"],
        textposition="outside",
        textfont={"family": "Inter, sans-serif", "size": 11, "color": "#0F172A"},
        hovertemplate="<b>%{y}</b><br>24h Change: %{x:+.2f}%<extra></extra>"
    ))

    fig.update_xaxes(zeroline=True, zerolinecolor="#CBD5E1", zerolinewidth=1.5, title=None, ticksuffix="%")
    fig.update_yaxes(title=None)

    return apply_editorial_chart_layout(fig, title="24-Hour Price Movers (%)", height=380)


def create_market_cap_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create vertical bar chart for market capitalization comparison."""
    if df.empty:
        fig = go.Figure()
        return apply_editorial_chart_layout(fig, height=360)

    plot_df = df.sort_values(by="market_cap_usd", ascending=False).copy()
    plot_df["symbol_label"] = plot_df["coin_id"].apply(get_coin_symbol)
    plot_df["name_label"] = plot_df["coin_id"].apply(get_coin_name)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=plot_df["symbol_label"],
        y=plot_df["market_cap_usd"],
        marker_color="#0F172A",
        hovertemplate="<b>%{x}</b><br>Market Cap: $%{y:,.0f}<extra></extra>"
    ))

    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, tickprefix="$")

    return apply_editorial_chart_layout(fig, title="Market Capitalization (USD)", height=380)


def create_volume_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create vertical bar chart for 24h trading volume comparison."""
    if df.empty:
        fig = go.Figure()
        return apply_editorial_chart_layout(fig, height=360)

    plot_df = df.sort_values(by="volume_24h_usd", ascending=False).copy()
    plot_df["symbol_label"] = plot_df["coin_id"].apply(get_coin_symbol)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=plot_df["symbol_label"],
        y=plot_df["volume_24h_usd"],
        marker_color="#2563EB",
        hovertemplate="<b>%{x}</b><br>24h Volume: $%{y:,.0f}<extra></extra>"
    ))

    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, tickprefix="$")

    return apply_editorial_chart_layout(fig, title="24-Hour Trading Volume (USD)", height=380)
