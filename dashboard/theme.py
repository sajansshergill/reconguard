"""Design tokens shared by app.py and charts.py.

Colors follow the validated dark-mode palette from the repo's dataviz
skill (status quad + first five categorical slots, both re-validated
against the #1a1a19 dark chart surface before use here). Break types map
onto the status quad semantically — `matched` really is "good", a
`value_mismatch` really is a "warning" — this isn't status colors being
repurposed as arbitrary series colors.
"""

# ---------------------------------------------------------------------------
# Surfaces & ink (dark mode)
# ---------------------------------------------------------------------------
PAGE_BG = "#0d0d0d"
SURFACE = "#1a1a19"
SURFACE_RAISED = "#212120"
BORDER = "rgba(255,255,255,0.10)"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#c3c2b7"
TEXT_MUTED = "#898781"
GRIDLINE = "#2c2c2a"

# ---------------------------------------------------------------------------
# Status quad — fixed, never reused for arbitrary series
# ---------------------------------------------------------------------------
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}
# text color to sit on top of each status fill (a badge chip, not a chart mark)
STATUS_TEXT = {
    "good": "#ffffff",
    "warning": "#0b0b0b",
    "serious": "#ffffff",
    "critical": "#ffffff",
}

# Reconciliation break types, mapped to the status they actually represent.
BREAK_STATUS = {
    "matched": "good",
    "value_mismatch": "warning",
    "missing_left": "serious",
    "missing_right": "critical",
}
BREAK_LABEL = {
    "matched": "Matched",
    "value_mismatch": "Value mismatch",
    "missing_left": "Orphan payroll row",
    "missing_right": "Employee not paid",
}
BREAK_ORDER = ["matched", "value_mismatch", "missing_left", "missing_right"]
BREAK_COLOR = {bt: STATUS[BREAK_STATUS[bt]] for bt in BREAK_ORDER}

# ---------------------------------------------------------------------------
# Categorical palette (first 5 slots — departments), validated all-adjacent
# and re-checked for this 5-slot subset against the dark surface.
# ---------------------------------------------------------------------------
CATEGORICAL = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"]
DEPARTMENTS = ["Engineering", "Finance", "Sales", "Operations", "HR"]
DEPT_COLOR = dict(zip(DEPARTMENTS, CATEGORICAL))

ACCENT_GRADIENT = "linear-gradient(90deg, #3987e5 0%, #9085e9 60%, #d55181 100%)"

FONT_STACK = (
    "'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif"
)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT_STACK, color=TEXT_SECONDARY, size=13),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        font=dict(color=TEXT_SECONDARY, size=12), bgcolor="rgba(0,0,0,0)",
    ),
    margin=dict(l=8, r=8, t=48, b=8),
    hoverlabel=dict(bgcolor=SURFACE_RAISED, font=dict(family=FONT_STACK, color=TEXT_PRIMARY)),
    hovermode="x unified",
)
AXIS_STYLE = dict(
    gridcolor=GRIDLINE, gridwidth=1, zeroline=False,
    linecolor=GRIDLINE, tickfont=dict(color=TEXT_MUTED, size=11),
)


def compact_number(n: float) -> str:
    n = float(n)
    for suffix, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= div:
            return f"{n / div:.1f}{suffix}".replace(".0", "")
    return f"{n:,.0f}"


def compact_currency(n: float) -> str:
    return f"${compact_number(n)}"


def base_css() -> str:
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: {FONT_STACK};
}}
.stApp {{
    background: radial-gradient(1200px 600px at 15% -10%, rgba(57,135,229,0.22), rgba(13,13,13,0) 55%),
                radial-gradient(1000px 520px at 92% 0%, rgba(213,81,129,0.16), rgba(13,13,13,0) 50%),
                {PAGE_BG};
}}
#MainMenu, footer, header {{ visibility: hidden; }}

/* ---- hero banner ---- */
.rg-hero {{
    padding: 28px 32px;
    border-radius: 20px;
    background: radial-gradient(120% 160% at 0% 0%, rgba(57,135,229,0.20), rgba(13,13,13,0) 55%),
                {SURFACE};
    border: 1px solid {BORDER};
    margin-bottom: 22px;
    position: relative;
    overflow: hidden;
}}
.rg-hero::before {{
    content: "";
    position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
    background: {ACCENT_GRADIENT};
}}
.rg-hero-title {{
    font-size: 1.9rem; font-weight: 800;
    margin: 0 0 4px 0; letter-spacing: -0.02em;
    background: linear-gradient(90deg, #9fd0ff, #c3b3ff, #ffb3d1);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.rg-hero-sub {{
    font-size: 0.95rem; color: {TEXT_SECONDARY}; margin: 0;
}}
.rg-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 600;
    background: rgba(255,255,255,0.06); color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
}}

/* ---- KPI tiles ---- */
.rg-kpi {{
    background: linear-gradient(135deg, rgba(57,135,229,0.14), rgba(255,255,255,0.03) 45%, rgba(213,81,129,0.10));
    backdrop-filter: blur(8px);
    border: 1px solid rgba(140,180,255,0.28);
    border-radius: 16px;
    padding: 18px 20px;
    height: 100%;
    box-shadow: 0 8px 28px rgba(0,0,0,0.35);
    transition: border-color 0.15s ease, transform 0.15s ease;
}}
.rg-kpi:hover {{ border-color: rgba(255,255,255,0.22); transform: translateY(-1px); }}
.rg-kpi-label {{
    font-size: 0.78rem; color: {TEXT_MUTED}; font-weight: 500;
    margin-bottom: 8px; display: flex; align-items: center; gap: 6px;
}}
.rg-kpi-value {{
    font-size: 2rem; font-weight: 700; color: {TEXT_PRIMARY};
    line-height: 1.1; letter-spacing: -0.01em;
    font-variant-numeric: proportional-nums;
}}
.rg-kpi-delta {{
    margin-top: 8px; font-size: 0.82rem; font-weight: 600;
    display: inline-flex; align-items: center; gap: 4px;
}}
.rg-kpi-delta.good {{ color: {STATUS['good']}; }}
.rg-kpi-delta.bad {{ color: {STATUS['critical']}; }}
.rg-kpi-delta.neutral {{ color: {TEXT_MUTED}; }}

/* ---- section headers ---- */
.rg-section {{
    font-size: 1.05rem; font-weight: 700; color: {TEXT_PRIMARY};
    margin: 4px 0 2px 0;
}}
.rg-caption {{
    font-size: 0.85rem; color: {TEXT_MUTED}; margin-bottom: 14px;
}}

/* ---- cards: Streamlit's native bordered container (st.container(border=True)) ----
   A hand-rolled <div class="rg-card"> spanning multiple st.markdown() calls doesn't
   work — unsafe_allow_html is parsed as an isolated HTML fragment per call, so an
   opening tag in one call and a closing tag in a later call never actually nest.
   st.container(border=True) is the real DOM element; this just re-skins it. */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {SURFACE};
    border: 1px solid {BORDER} !important;
    border-radius: 16px !important;
    margin-bottom: 18px;
}}
div[data-testid="stVerticalBlockBorderWrapper"] > div {{
    padding: 4px 4px;
}}

/* ---- status badges ---- */
.rg-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 999px; font-size: 0.8rem; font-weight: 700;
}}
.rg-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}

/* ---- empty state ---- */
.rg-empty {{
    text-align: center; padding: 72px 24px;
    background: {SURFACE}; border: 1px dashed {BORDER}; border-radius: 20px;
}}
.rg-empty-emoji {{ font-size: 3rem; margin-bottom: 12px; }}
.rg-empty-title {{ font-size: 1.4rem; font-weight: 700; color: {TEXT_PRIMARY}; margin-bottom: 8px; }}
.rg-empty-sub {{ font-size: 0.95rem; color: {TEXT_SECONDARY}; max-width: 480px; margin: 0 auto; }}

/* ---- sidebar polish ---- */
section[data-testid="stSidebar"] {{
    background: {SURFACE}; border-right: 1px solid {BORDER};
}}
div[data-testid="stMetric"] {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; padding: 12px 16px;
}}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px 10px 0 0; padding: 8px 16px; color: {TEXT_SECONDARY};
}}
.stTabs [aria-selected="true"] {{ color: {TEXT_PRIMARY} !important; }}

/* ---- dataframe ---- */
div[data-testid="stDataFrame"] {{ border-radius: 14px; overflow: hidden; }}
</style>
"""


def badge_html(status: str, label: str) -> str:
    color = STATUS[status]
    return (
        f'<span class="rg-badge" style="background:{color}22;color:{color};'
        f'border:1px solid {color}55;">'
        f'<span class="rg-dot" style="background:{color};"></span>{label}</span>'
    )
