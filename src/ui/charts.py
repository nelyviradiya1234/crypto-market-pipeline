"""Restyled Plotly visualization functions for Editorial Financial presentation."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Editorial Palette
EDITORIAL_PALETTE = [
    "#0F172A",  # Dark Slate / BTC
    "#2563EB",  # Royal Blue / ETH
    "#16A34A",  # Emerald / SOL
    "#D97706",  # Amber / BNB
    "#8B5CF6",  # Purple / XRP
    "#EC4899",  # Pink / ADA
    "#14B8A6",  # Teal / DOGE
    "#F97316",  # Orange / DOT
]


def apply_editorial_chart_layout(fig, title: str = "", height: int = 420):
    """Apply consistent editorial styling to Plotly figure objects."""
    fig.update_layout(
        title={
            "text": title,
            "font": {"family": "Inter", "size": 15, "color": "#0F172A", "weight": 600},
            "x": 0.0,
            "xanchor": "left"
        } if title else None,
        font={"family": "Inter", "color": "#64748B", "size": 12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin={"l": 10, "r": 10, "t": 35 if title else 10, "b": 20},
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
            "font": {"size": 11, "color": "#0F172A"},
            "title": None
        },
        hoverlabel={
            "bgcolor": "#0F172A",
            "font_size": 12,
            "font_family": "Inter",
            "font_color": "#FFFFFF"
        }
    )
    return fig


def create_editorial_line_chart(df: pd.DataFrame) -> go.Figure:
    """Create a restyled line chart for cryptocurrency price time-series."""
    if df.empty:
        fig = go.Figure()
        return apply_editorial_chart_layout(fig)

    fig = px.line(
        df,
        x="pulled_at",
        y="price_usd",
        color="coin_id",
        color_discrete_sequence=EDITORIAL_PALETTE,
        labels={"pulled_at": "Time (UTC)", "price_usd": "Price (USD)", "coin_id": "Asset"}
    )

    fig.update_traces(line={"width": 2.2})
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, tickprefix="$")

    return apply_editorial_chart_layout(fig, height=440)


def create_performance_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create horizontal zero-baseline bar chart for 24h percentage change."""
    if df.empty:
        return go.Figure()

    plot_df = df.sort_values(by="change_24h_pct", ascending=True).copy()
    plot_df["color"] = plot_df["change_24h_pct"].apply(lambda x: "#16A34A" if x >= 0 else "#DC2626")
    plot_df["formatted_text"] = plot_df["change_24h_pct"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "")
    plot_df["asset_name"] = plot_df["symbol"].str.upper() + " (" + plot_df["coin_id"].str.capitalize() + ")"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=plot_df["asset_name"],
        x=plot_df["change_24h_pct"],
        orientation="h",
        marker={"color": plot_df["color"]},
        text=plot_df["formatted_text"],
        textposition="outside",
        textfont={"family": "Inter", "size": 11, "color": "#0F172A"}
    ))

    fig.update_xaxes(zeroline=True, zerolinecolor="#CBD5E1", zerolinewidth=1.5, title=None)
    fig.update_yaxes(title=None)

    return apply_editorial_chart_layout(fig, height=380)


def create_market_cap_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create restyled vertical bar chart for market capitalization comparison."""
    if df.empty:
        return go.Figure()

    plot_df = df.sort_values(by="market_cap_usd", ascending=False).copy()
    plot_df["asset_label"] = plot_df["symbol"].str.upper()

    fig = px.bar(
        plot_df,
        x="asset_label",
        y="market_cap_usd",
        color_discrete_sequence=["#0F172A"]
    )

    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, tickprefix="$")

    return apply_editorial_chart_layout(fig, height=380)


def create_volume_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create restyled vertical bar chart for 24h trading volume comparison."""
    if df.empty:
        return go.Figure()

    plot_df = df.sort_values(by="volume_24h_usd", ascending=False).copy()
    plot_df["asset_label"] = plot_df["symbol"].str.upper()

    fig = px.bar(
        plot_df,
        x="asset_label",
        y="volume_24h_usd",
        color_discrete_sequence=["#2563EB"]
    )

    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, tickprefix="$")

    return apply_editorial_chart_layout(fig, height=380)
