"""Plotly figure builders for the ReconGuard dashboard.

Every figure applies the shared dark-mode layout/axis tokens from theme.py
and follows the repo's dataviz rules: one axis per chart, a legend whenever
two or more series are on screen (none for one), direct labels used
sparingly (bar tips only), hover on every mark, and — since the 5-department
palette sits in the 6-8 CVD floor band for one adjacent pair — labels ride
every bar as the required secondary encoding rather than relying on hue
alone.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import theme

LABEL_COLOR = {theme.BREAK_LABEL[bt]: theme.BREAK_COLOR[bt] for bt in theme.BREAK_ORDER}


def break_trend_chart(summary_df: pd.DataFrame, break_types=None) -> go.Figure:
    order = [bt for bt in (break_types or theme.BREAK_ORDER) if bt in summary_df.columns]
    df = summary_df.reset_index(drop=True)
    x = [f"Run {i + 1}" for i in range(len(df))]
    hover_ts = df["run_ts"].dt.strftime("%b %d, %Y · %H:%M")

    fig = go.Figure()
    for bt in order:
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


def animated_break_chart(summary_df: pd.DataFrame, break_types=None) -> go.Figure:
    """Run-by-run animated bar chart (Plotly animation_frame)."""
    order = [bt for bt in (break_types or theme.BREAK_ORDER) if bt in summary_df.columns]
    df = summary_df.reset_index(drop=True).copy()
    df["frame"] = [f"Run {i + 1} · {ts:%b %d %H:%M:%S}" for i, ts in enumerate(df["run_ts"])]
    long = df.melt(id_vars="frame", value_vars=order, var_name="break_type", value_name="count")
    long["label"] = long["break_type"].map(theme.BREAK_LABEL)
    ymax = float(long["count"].max()) if not long.empty else 1.0
    fig = px.bar(
        long, x="label", y="count", color="label", animation_frame="frame",
        color_discrete_map=LABEL_COLOR, range_y=[0, ymax * 1.15],
        labels={"label": "Break type", "count": "Records"},
        template="plotly_dark", title="Break composition evolving across runs — press Play",
    )
    fig.update_layout(**theme.PLOTLY_LAYOUT, showlegend=False, height=380)
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 700
    return fig


def animated_pay_scatter(detail_df: pd.DataFrame) -> go.Figure:
    """Animated scatter: payroll gross vs HRIS-expected gross, one frame per run."""
    df = detail_df.dropna(subset=["left_value", "right_value"]).copy()
    df["label"] = df["break_type"].map(theme.BREAK_LABEL)
    df["frame"] = pd.to_datetime(df["run_ts"]).dt.strftime("Run · %b %d %H:%M:%S")
    df["abs_variance"] = (df["left_value"] - df["right_value"]).abs()
    lim = float(max(df["left_value"].max(), df["right_value"].max())) if not df.empty else 1.0
    fig = px.scatter(
        df.sort_values("run_ts"), x="right_value", y="left_value", color="label",
        animation_frame="frame", hover_data=["employee_id"],
        color_discrete_map=LABEL_COLOR, range_x=[0, lim * 1.05], range_y=[0, lim * 1.05],
        labels={"right_value": "Expected (HRIS) $", "left_value": "Payroll gross $", "label": "Status"},
        template="plotly_dark",
    )
    fig.update_layout(**theme.PLOTLY_LAYOUT, height=420)
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 700
    return fig


def detail_3d_chart(detail_df: pd.DataFrame) -> go.Figure:
    """Genuine 3D break space: expected pay x paid pay x |variance|, drag to rotate."""
    df = detail_df.dropna(subset=["left_value", "right_value"]).copy()
    df["label"] = df["break_type"].map(theme.BREAK_LABEL)
    df["abs_variance"] = (df["left_value"] - df["right_value"]).abs()
    df["size"] = np.clip(df["abs_variance"], 4, 60)
    hover = ["employee_id"] + (["department"] if "department" in df.columns else [])
    fig = px.scatter_3d(
        df, x="right_value", y="left_value", z="abs_variance", color="label",
        size="size", size_max=16, opacity=0.85, hover_data=hover,
        color_discrete_map=LABEL_COLOR,
        labels={"right_value": "Expected (HRIS) $", "left_value": "Payroll gross $",
                "abs_variance": "|Variance| $", "label": "Status"},
        template="plotly_dark",
    )
    layout = {k: v for k, v in theme.PLOTLY_LAYOUT.items() if k != "margin"}
    fig.update_layout(
        **layout, height=520,
        scene=dict(
            xaxis=dict(backgroundcolor="rgba(20,24,32,.9)", gridcolor=theme.GRIDLINE),
            yaxis=dict(backgroundcolor="rgba(20,24,32,.9)", gridcolor=theme.GRIDLINE),
            zaxis=dict(backgroundcolor="rgba(20,24,32,.9)", gridcolor=theme.GRIDLINE),
        ),
        margin=dict(l=0, r=0, t=50, b=0),
    )
    return fig


def break_surface_chart(detail_df: pd.DataFrame) -> go.Figure | None:
    """Surface of break counts: department (y) x break type (x) x count (z)."""
    if "department" not in detail_df.columns or detail_df.empty:
        return None
    pivot = (
        detail_df.assign(label=detail_df["break_type"].map(theme.BREAK_LABEL))
        .groupby(["department", "label"]).size().unstack(fill_value=0)
    )
    labels = [theme.BREAK_LABEL[bt] for bt in theme.BREAK_ORDER if theme.BREAK_LABEL[bt] in pivot.columns]
    if pivot.shape[0] < 2 or len(labels) < 2:
        return None
    pivot = pivot[labels]
    fig = go.Figure(data=[go.Surface(
        z=pivot.to_numpy(dtype=float), x=labels, y=list(pivot.index),
        colorscale="Viridis", colorbar=dict(title="Records"),
    )])
    layout = {k: v for k, v in theme.PLOTLY_LAYOUT.items() if k != "margin"}
    fig.update_layout(
        **layout, height=460, template="plotly_dark",
        scene=dict(xaxis_title="Break type", yaxis_title="Department", zaxis_title="Records",
                   camera=dict(eye=dict(x=1.5, y=-1.4, z=0.9))),
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig


def headcount_chart(headcount_df: pd.DataFrame) -> go.Figure:
    return _department_bar(headcount_df, "headcount", lambda v: f"{int(v)}")


def avg_salary_chart(headcount_df: pd.DataFrame) -> go.Figure:
    return _department_bar(headcount_df, "avg_base_salary", theme.compact_currency)
