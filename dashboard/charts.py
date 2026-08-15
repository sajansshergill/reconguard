"""Plotly figure builders for the ReconGuard dashboard.

Every figure applies the shared dark-mode layout/axis tokens from theme.py
and follows the repo's dataviz rules: one axis per chart, a legend whenever
two or more series are on screen (none for one), direct labels used
sparingly (bar tips only), hover on every mark, and — since the 5-department
palette sits in the 6-8 CVD floor band for one adjacent pair — labels ride
every bar as the required secondary encoding rather than relying on hue
alone.
"""
import pandas as pd
import plotly.graph_objects as go

import theme


def break_trend_chart(summary_df: pd.DataFrame) -> go.Figure:
    df = summary_df.reset_index(drop=True)
    x = [f"Run {i + 1}" for i in range(len(df))]
    hover_ts = df["run_ts"].dt.strftime("%b %d, %Y · %H:%M")

    fig = go.Figure()
    for bt in theme.BREAK_ORDER:
        fig.add_bar(
            x=x, y=df[bt], name=theme.BREAK_LABEL[bt],
            marker_color=theme.BREAK_COLOR[bt], marker_line_width=0,
            customdata=hover_ts,
            hovertemplate=(
                f"<b>{theme.BREAK_LABEL[bt]}</b><br>"
                "%{customdata}<br>%{y} record(s)<extra></extra>"
            ),
        )
    fig.update_layout(
        **theme.PLOTLY_LAYOUT,
        barmode="stack", bargap=0.35,
        height=340,
        yaxis=dict(title="Records", **theme.AXIS_STYLE),
        xaxis=dict(**theme.AXIS_STYLE),
    )
    return fig


def break_composition_bar(latest: pd.Series) -> go.Figure:
    """A single horizontal 100%-stacked bar: this run's break composition."""
    total = sum(latest[bt] for bt in theme.BREAK_ORDER) or 1
    fig = go.Figure()
    for bt in theme.BREAK_ORDER:
        val = int(latest[bt])
        pct = val / total * 100
        fig.add_bar(
            y=["Latest run"], x=[val], name=theme.BREAK_LABEL[bt],
            orientation="h", marker_color=theme.BREAK_COLOR[bt], marker_line_width=0,
            text=f"{val} ({pct:.0f}%)" if pct >= 6 else "",
            textposition="inside", insidetextanchor="middle",
            textfont=dict(
                color=theme.STATUS_TEXT[theme.BREAK_STATUS[bt]], size=12, family=theme.FONT_STACK,
            ),
            hovertemplate=f"<b>{theme.BREAK_LABEL[bt]}</b><br>%{{x}} ({pct:.1f}%)<extra></extra>",
        )
    layout = {**theme.PLOTLY_LAYOUT, "margin": dict(l=8, r=8, t=8, b=8)}
    fig.update_layout(
        **layout,
        barmode="stack", height=120,
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def _department_bar(df: pd.DataFrame, value_col: str, label_fmt) -> go.Figure:
    df = df.sort_values(value_col, ascending=False).reset_index(drop=True)
    colors = [theme.DEPT_COLOR.get(d, theme.CATEGORICAL[0]) for d in df["department"]]
    fig = go.Figure(
        go.Bar(
            x=df["department"], y=df[value_col],
            marker_color=colors, marker_line_width=0,
            text=[label_fmt(v) for v in df[value_col]], textposition="outside",
            textfont=dict(color=theme.TEXT_PRIMARY, size=12, family=theme.FONT_STACK),
            hovertemplate="<b>%{x}</b><br>" + f"{value_col.replace('_', ' ')}: " + "%{text}<extra></extra>",
            showlegend=False,
        )
    )
    x_axis_style = {**theme.AXIS_STYLE, "gridcolor": "rgba(0,0,0,0)"}
    fig.update_layout(
        **theme.PLOTLY_LAYOUT,
        height=340, bargap=0.45,
        yaxis=dict(**theme.AXIS_STYLE, showticklabels=False),
        xaxis=dict(**x_axis_style),
    )
    return fig


def headcount_chart(headcount_df: pd.DataFrame) -> go.Figure:
    return _department_bar(headcount_df, "headcount", lambda v: f"{int(v)}")


def avg_salary_chart(headcount_df: pd.DataFrame) -> go.Figure:
    return _department_bar(headcount_df, "avg_base_salary", theme.compact_currency)
