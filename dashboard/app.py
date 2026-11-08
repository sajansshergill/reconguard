"""ReconGuard dashboard — Streamlit UI.

Run with:  streamlit run dashboard/app.py   (from the repo root, or anywhere —
paths are resolved relative to the repo root regardless of cwd).

Reads the local Delta tables written by scripts/run_local.py (see data.py —
no Spark session in this process, so the app itself opens fast). The sidebar
can trigger a real pipeline run as a subprocess when you want fresh data.
"""
import importlib.util
import os
import random
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import charts  # noqa: E402
import data  # noqa: E402
import theme  # noqa: E402

st.set_page_config(
    page_title="ReconGuard", page_icon="🛡️", layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(theme.base_css(), unsafe_allow_html=True)

# The pipeline buttons shell out to scripts/run_local.py, which needs PySpark —
# deliberately not in dashboard/requirements.txt (heavy, needs a JVM, not what a
# hosted read-only demo needs). If it's not installed, degrade the buttons
# honestly rather than let them fail; see docs/gaps.md.
PIPELINE_AVAILABLE = importlib.util.find_spec("pyspark") is not None


# ---------------------------------------------------------------------------
# Cached reads — cleared whenever the sidebar triggers a fresh pipeline run
# ---------------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def cached_summary():
    return data.get_reconciliation_summary()


@st.cache_data(ttl=30, show_spinner=False)
def cached_detail(run_id):
    return data.get_reconciliation_detail(run_id)


@st.cache_data(ttl=30, show_spinner=False)
def cached_headcount():
    return data.get_gold_headcount()


@st.cache_data(ttl=30, show_spinner=False)
def cached_payroll_summary():
    return data.get_gold_payroll_summary()


@st.cache_data(ttl=30, show_spinner=False)
def cached_pii_checks():
    return data.pii_gold_checks()


@st.cache_data(ttl=30, show_spinner=False)
def cached_ingestion_gate():
    return data.ingestion_gate()


@st.cache_data(ttl=30, show_spinner=False)
def cached_policy():
    return data.load_pii_policy()


@st.cache_data(ttl=30, show_spinner=False)
def cached_rules():
    return data.load_rules()


@st.cache_data(ttl=30, show_spinner=False)
def cached_all_detail():
    return data.get_reconciliation_detail(None)


@st.cache_data(ttl=30, show_spinner=False)
def cached_employees():
    return data.get_silver_employees()


# ---------------------------------------------------------------------------
# Small render helpers
# ---------------------------------------------------------------------------
def kpi_tile(label: str, value: str, icon: str = "", delta: float | None = None,
             delta_good_if_negative: bool = True, unit: str = "") -> None:
    delta_html = ""
    if delta is not None and delta != 0:
        direction = "good" if (delta < 0) == delta_good_if_negative else "bad"
        arrow = "↓" if delta < 0 else "↑"
        delta_html = (f'<div class="rg-kpi-delta {direction}">{arrow} '
                       f'{abs(delta):g}{unit} vs prior run</div>')
    elif delta == 0:
        delta_html = '<div class="rg-kpi-delta neutral">→ no change vs prior run</div>'
    st.markdown(
        f'<div class="rg-kpi"><div class="rg-kpi-label">{icon} {label}</div>'
        f'<div class="rg-kpi-value">{value}</div>{delta_html}</div>',
        unsafe_allow_html=True,
    )


def status_badge(passed: bool, true_label: str = "Passing", false_label: str = "Failing") -> str:
    return theme.badge_html("good" if passed else "critical", true_label if passed else false_label)


def section(title: str, caption: str | None = None) -> None:
    st.markdown(f'<div class="rg-section">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="rg-caption">{caption}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.3rem;font-weight:800;color:#fff;">🛡️ ReconGuard</div>'
        '<div style="color:#898781;font-size:0.85rem;margin-bottom:6px;">'
        'Reconciliation & governance dashboard</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("**Pipeline controls**")
    no_pipeline_help = ("Requires a local PySpark environment, not installed in this hosted "
                         "demo. Clone the repo and run `make run` for a live pipeline.")
    run_clicked = st.button(
        "▶️  Run reconciliation", use_container_width=True, type="primary",
        disabled=not PIPELINE_AVAILABLE,
        help=None if PIPELINE_AVAILABLE else no_pipeline_help,
    )
    demo_clicked = st.button(
        "🎲  New demo run", use_container_width=True, disabled=not PIPELINE_AVAILABLE,
        help=(no_pipeline_help if not PIPELINE_AVAILABLE else
              "Regenerates HRIS/payroll data with a random seed and reconciles it — "
              "use this a few times to build up run history for the trend chart."),
    )
    if not PIPELINE_AVAILABLE:
        st.caption("📦 Hosted demo — showing a static seeded snapshot "
                    "(`dashboard/sample_data/`), not a live pipeline run.")

    if run_clicked or demo_clicked:
        env = os.environ.copy()
        if demo_clicked:
            env["LOCAL_DATA_SEED"] = str(random.randint(1, 10_000))
        with st.spinner("Running generate → bronze → silver → reconcile → gold…"):
            proc = subprocess.run(
                [sys.executable, str(data.REPO_ROOT / "scripts" / "run_local.py")],
                cwd=str(data.REPO_ROOT), capture_output=True, text=True,
                timeout=600, env=env,
            )
        if proc.returncode == 0:
            st.cache_data.clear()
            st.sidebar.success("Pipeline run complete.")
            st.rerun()
        else:
            st.sidebar.error("Pipeline run failed — see log below.")
            with st.sidebar.expander("Error log"):
                st.code((proc.stderr or proc.stdout)[-4000:])

    st.divider()
    source_dir = "dashboard/sample_data/" if data.using_sample_data() else "data/"
    st.caption(f"Reading Delta tables from `{source_dir}` — no Spark session in this app; "
               "the buttons above shell out to the real pipeline.")
    st.caption("Unity Catalog enforcement and Power BI/XMLA checks require a live Azure "
               "workspace and aren't available here — see `docs/azure_service_mapping.md`.")


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------
summary = cached_summary()
rules = cached_rules()

if summary is None or summary.empty:
    st.markdown(
        '<div class="rg-hero"><div class="rg-hero-title">🛡️ ReconGuard</div>'
        '<p class="rg-hero-sub">Azure-native data quality & validation for lakehouse '
        'pipelines — reconciliation, PII governance, and report-layer checks, gated in '
        'CI/CD.</p></div>',
        unsafe_allow_html=True,
    )
    empty_sub = (
        'Click <b>▶️ Run reconciliation</b> in the sidebar to generate a sample HRIS + '
        'payroll dataset, run it through bronze → silver → gold, and populate this dashboard.'
        if PIPELINE_AVAILABLE else
        'This hosted demo has no local pipeline and no committed sample data to fall back '
        'on. Clone the repo and run <code>make run</code> to generate data locally.'
    )
    st.markdown(
        '<div class="rg-empty"><div class="rg-empty-emoji">🌱</div>'
        '<div class="rg-empty-title">No pipeline runs yet</div>'
        f'<p class="rg-empty-sub">{empty_sub}</p></div>',
        unsafe_allow_html=True,
    )
    st.stop()


# ---------------------------------------------------------------------------
# Global sidebar filters — every view below reads the filtered frames
# ---------------------------------------------------------------------------
_all_detail_raw = cached_all_detail()
_employees = cached_employees()
if _all_detail_raw is not None and not _all_detail_raw.empty:
    all_detail = _all_detail_raw.copy()
    all_detail["run_ts"] = pd.to_datetime(all_detail["run_ts"])
    if _employees is not None and not _employees.empty and "department" in _employees.columns:
        dept_map = (_employees.drop_duplicates("employee_id")
                    .set_index("employee_id")["department"].to_dict())
        all_detail["department"] = all_detail["employee_id"].map(dept_map)
    else:
        all_detail["department"] = None
    all_detail["department"] = all_detail["department"].fillna("Payroll only")
    all_detail["abs_variance"] = (all_detail["left_value"] - all_detail["right_value"]).abs()
else:
    all_detail = _all_detail_raw

_dept_options = sorted(all_detail["department"].dropna().unique()) if all_detail is not None and not all_detail.empty else []
_max_var = float(all_detail["abs_variance"].max()) if all_detail is not None and not all_detail.empty else 0.0

with st.sidebar:
    st.divider()
    st.markdown("**🎛️ Live filters**")
    st.caption("Every chart, table and KPI on this page re-renders from these.")
    run_count = st.slider("Runs in view (most recent)", 1, max(len(summary), 1),
                          len(summary))
    sel_depts = st.multiselect("Departments", _dept_options, default=_dept_options)
    sel_breaks = st.multiselect(
        "Break types", options=theme.BREAK_ORDER,
        format_func=lambda bt: theme.BREAK_LABEL[bt], default=theme.BREAK_ORDER,
    )
    min_variance = st.slider("Min |pay variance| ($)", 0.0, max(_max_var, 10.0), 0.0, 10.0)
    only_breaks = st.checkbox("Only breaks (hide matched)", value=False)

summary = summary.tail(run_count).reset_index(drop=True)
if not sel_breaks:
    sel_breaks = theme.BREAK_ORDER


def apply_global(detail_df):
    """Apply the sidebar filters to a reconciliation-detail frame."""
    if detail_df is None or detail_df.empty:
        return detail_df
    out = detail_df.copy()
    if "department" not in out.columns and all_detail is not None and not all_detail.empty:
        dm = all_detail.drop_duplicates("employee_id").set_index("employee_id")["department"].to_dict()
        out["department"] = out["employee_id"].map(dm)
    if "abs_variance" not in out.columns:
        out["abs_variance"] = (out["left_value"] - out["right_value"]).abs()
    out = out[out["break_type"].isin(sel_breaks)]
    if sel_depts and "department" in out.columns:
        out = out[out["department"].isin(sel_depts)]
    if min_variance > 0:
        out = out[out["abs_variance"] >= min_variance]
    if only_breaks:
        out = out[out["break_type"] != "matched"]
    return out


# ---------------------------------------------------------------------------
# Hero + KPI row
# ---------------------------------------------------------------------------
latest = summary.iloc[-1]
prior = summary.iloc[-2] if len(summary) > 1 else None
total = int(sum(latest[bt] for bt in theme.BREAK_ORDER))
breaks = total - int(latest["matched"])
match_rate = (latest["matched"] / total * 100) if total else 0.0
pii_checks = cached_pii_checks()
pii_clean = all(r["passed"] for r in pii_checks) if pii_checks else None

breaks_delta = None
match_rate_delta = None
if prior is not None:
    prior_total = int(sum(prior[bt] for bt in theme.BREAK_ORDER))
    prior_breaks = prior_total - int(prior["matched"])
    breaks_delta = breaks - prior_breaks
    prior_rate = (prior["matched"] / prior_total * 100) if prior_total else 0.0
    match_rate_delta = round(match_rate - prior_rate, 1)

sample_pill = (f'<span class="rg-pill" style="border-color:{theme.STATUS["warning"]}66;'
               f'color:{theme.STATUS["warning"]};">📦 Sample data snapshot</span>'
               if data.using_sample_data() else "")
st.markdown(
    f'''<div class="rg-hero">
      <div class="rg-hero-title">🛡️ ReconGuard</div>
      <p class="rg-hero-sub">Payroll ↔ HRIS reconciliation, PII governance, and
      ingestion validation — running locally on OSS Delta + Spark.</p>
      <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;">
        <span class="rg-pill">📅 Pay period {rules["pay_period"]}</span>
        <span class="rg-pill">🕓 Last run {latest["run_ts"]:%b %d, %Y · %H:%M}</span>
        <span class="rg-pill">🧮 {len(summary)} run(s) tracked</span>
        {sample_pill}
      </div>
    </div>''',
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_tile("Records reconciled", f"{total:,}", icon="📊")
with c2:
    kpi_tile("Match rate", f"{match_rate:.1f}%", icon="✅",
              delta=match_rate_delta, delta_good_if_negative=False, unit="pt")
with c3:
    kpi_tile("Breaks detected", f"{breaks:,}", icon="⚠️",
              delta=breaks_delta, delta_good_if_negative=True)
with c4:
    kpi_tile("PII in gold", "Clean" if pii_clean else "Leak found", icon="🔒")
with c5:
    kpi_tile("Runs tracked", f"{len(summary)}", icon="🗂️")

st.write("")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_recon, tab_anim, tab_3d, tab_gov, tab_work = st.tabs(
    ["🔍  Reconciliation", "🎬  Animated breaks", "🧊  3D break space",
     "🔐  Governance & PII", "🧑‍🤝‍🧑  Workforce & payroll"]
)

with tab_anim:
    with st.container(border=True):
        section("🎬 Animated breaks",
                "Native Plotly animation — press ▶ Play and the break composition and the "
                "per-record pay scatter replay run by run. Sidebar filters apply here too.")
        st.plotly_chart(charts.animated_break_chart(summary, sel_breaks),
                        use_container_width=True, config={"displayModeBar": False})
    with st.container(border=True):
        section("Payroll vs expected, animated")
        anim_detail = apply_global(all_detail)
        if anim_detail is not None and not anim_detail.empty:
            st.plotly_chart(charts.animated_pay_scatter(anim_detail),
                            use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No detail rows match the current filters.")

with tab_3d:
    with st.container(border=True):
        section("🧊 3D break space",
                "Drag to rotate, scroll to zoom. Each point is one reconciled record in the "
                "latest run in view: expected pay × payroll gross × absolute variance, "
                "coloured by break type and sized by variance — matched records hug the "
                "floor, mismatches rise out of it.")
        latest_detail = apply_global(
            all_detail[all_detail["run_id"] == latest["run_id"]] if all_detail is not None and not all_detail.empty else all_detail
        )
        if latest_detail is not None and not latest_detail.empty:
            st.plotly_chart(charts.detail_3d_chart(latest_detail),
                            use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No detail rows match the current filters.")
    with st.container(border=True):
        section("Break surface — department × break type")
        surf_detail = apply_global(all_detail)
        surf_fig = charts.break_surface_chart(surf_detail) if surf_detail is not None else None
        if surf_fig is not None:
            st.plotly_chart(surf_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Not enough department coverage in the current filter for a surface.")

with tab_recon:
    with st.container(border=True):
        section("Break trend across runs",
                "Every reconciliation run is appended to the audit table — nothing is "
                "overwritten, so breaks trend over time instead of only showing the latest snapshot.")
        st.plotly_chart(charts.break_trend_chart(summary, sel_breaks), use_container_width=True,
                         config={"displayModeBar": False})

    with st.container(border=True):
        section("Latest run composition")
        st.plotly_chart(charts.break_composition_bar(latest), use_container_width=True,
                         config={"displayModeBar": False})
        st.markdown(
            '<div class="rg-caption">'
            f'{theme.badge_html("good", "Matched")} both systems agree &nbsp; '
            f'{theme.badge_html("warning", "Value mismatch")} gross pay off by more than the tolerance &nbsp; '
            f'{theme.badge_html("serious", "Orphan payroll row")} paid, but no HRIS record &nbsp; '
            f'{theme.badge_html("critical", "Employee not paid")} in HRIS, no payroll row this period'
            '</div>',
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        section("Break detail", "Drill into any run's individual records.")
        run_options = summary.sort_values("run_ts", ascending=False)
        run_labels = {
            row.run_id: f'Run {len(summary) - i} · {row.run_ts:%b %d %H:%M} · '
                        f'{int(sum(getattr(row, bt) for bt in theme.BREAK_ORDER)) - int(row.matched)} break(s)'
            for i, row in enumerate(run_options.itertuples())
        }
        fc1, fc2, fc3 = st.columns([2, 2, 1.4])
        with fc1:
            selected_run = st.selectbox("Run", options=list(run_labels.keys()),
                                         format_func=lambda rid: run_labels[rid])
        with fc2:
            type_filter = st.multiselect(
                "Break type", options=theme.BREAK_ORDER,
                format_func=lambda bt: theme.BREAK_LABEL[bt], default=[],
                placeholder="All break types",
            )
        with fc3:
            search = st.text_input("Employee ID", placeholder="e.g. E00042")

        detail = cached_detail(selected_run)
        if detail is not None and not detail.empty:
            view = apply_global(detail)
            if type_filter:
                view = view[view["break_type"].isin(type_filter)]
            if search:
                view = view[view["employee_id"].astype(str).str.contains(search, case=False, na=False)]
            view = view[["employee_id", "left_value", "right_value", "break_type"]].rename(columns={
                "employee_id": "Employee ID", "left_value": "Payroll gross pay",
                "right_value": "Expected (HRIS)", "break_type": "Status",
            })
            view["Status"] = view["Status"].map(theme.BREAK_LABEL)

            def _style_status(val):
                status = {v: k for k, v in theme.BREAK_LABEL.items()}.get(val)
                color = theme.BREAK_COLOR.get(status, theme.TEXT_MUTED)
                fg = theme.STATUS_TEXT.get(theme.BREAK_STATUS.get(status, "warning"), "#fff")
                return f"background-color:{color}; color:{fg}; font-weight:600; border-radius:6px;"

            styled = view.style.format(
                {"Payroll gross pay": "${:,.2f}", "Expected (HRIS)": "${:,.2f}"}
            ).map(_style_status, subset=["Status"])
            st.dataframe(styled, use_container_width=True, hide_index=True, height=360)
            st.caption(f"{len(view):,} of {len(detail):,} record(s) shown.")
        else:
            st.info("No detail rows for this run.")

with tab_gov:
    gc1, gc2 = st.columns([1, 1])
    with gc1, st.container(border=True):
        section("Sensitive-column policy", "config/pii_policy.yaml — what must be tagged, "
                                            "masked, and kept out of gold.")
        policy = cached_policy()
        for entry in policy["sensitive_columns"]:
            excluded = entry["column"] in policy["excluded_from_gold"]
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:10px 0;border-bottom:1px solid {theme.BORDER};">'
                f'<div><b style="color:{theme.TEXT_PRIMARY}">{entry["column"]}</b>'
                f'<div style="color:{theme.TEXT_MUTED};font-size:0.8rem;">mask: {entry["mask"]}</div></div>'
                f'{theme.badge_html("good" if excluded else "warning", "excluded from gold" if excluded else "not excluded")}'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            '<div class="rg-caption" style="margin-top:10px;">Unity Catalog tag/mask '
            f'{theme.badge_html("warning", "enforcement requires Databricks")} — this panel '
            'checks intent locally; live enforcement is verified against the workspace.</div>',
            unsafe_allow_html=True,
        )

    with gc2, st.container(border=True):
        section("PII-in-gold check", "Real check against the actual local gold Delta tables — "
                                      "not simulated.")
        for r in pii_checks:
            fail_label = "Leaked: " + ", ".join(r["leaked"])
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:10px 0;border-bottom:1px solid {theme.BORDER};">'
                f'<b style="color:{theme.TEXT_PRIMARY}">{r["table"]}</b>'
                f'{status_badge(r["passed"], "Clean", fail_label)}'
                f'</div>',
                unsafe_allow_html=True,
            )
        if not pii_checks:
            st.info("Gold tables not found yet.")

    with st.container(border=True):
        section("Ingestion validation gate", "Schema, completeness, and freshness checks against "
                                              "the current bronze tables (config/expectations.yaml).")
        gate = cached_ingestion_gate()
        gcol1, gcol2 = st.columns(2)
        for col, source_name in ((gcol1, "hris"), (gcol2, "payroll")):
            with col:
                st.markdown(f"**bronze.{source_name}**")
                for check in gate.get(source_name, []):
                    detail_txt = ""
                    if "null_rate" in check:
                        detail_txt = f' <span style="color:{theme.TEXT_MUTED};">'\
                                      f'({check["null_rate"] * 100:.1f}% null)</span>'
                    if "newest" in check:
                        detail_txt = f' <span style="color:{theme.TEXT_MUTED};">'\
                                      f'(newest: {check["newest"]})</span>'
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;align-items:center;'
                        f'padding:8px 0;border-bottom:1px solid {theme.BORDER};">'
                        f'<span style="color:{theme.TEXT_SECONDARY};">{check["check"]}{detail_txt}</span>'
                        f'{status_badge(check["passed"])}</div>',
                        unsafe_allow_html=True,
                    )

with tab_work:
    payroll_summary_df = cached_payroll_summary()
    headcount_df = cached_headcount()
    if headcount_df is not None and not headcount_df.empty and sel_depts:
        headcount_df = headcount_df[headcount_df["department"].isin(sel_depts)]

    if payroll_summary_df is not None and not payroll_summary_df.empty:
        row = payroll_summary_df.iloc[-1]
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            kpi_tile("Employees paid", f'{int(row["employees_paid"]):,}', icon="🧑‍💼")
        with pc2:
            kpi_tile("Total gross pay", f'${row["total_gross"]:,.0f}', icon="💵")
        with pc3:
            kpi_tile("Total net pay", f'${row["total_net"]:,.0f}', icon="💰")
    else:
        st.info("Gold payroll summary not found yet.")

    st.write("")
    wc1, wc2 = st.columns(2)
    with wc1, st.container(border=True):
        section("Headcount by department")
        if headcount_df is not None and not headcount_df.empty:
            st.plotly_chart(charts.headcount_chart(headcount_df), use_container_width=True,
                             config={"displayModeBar": False})
        else:
            st.info("Gold headcount table not found yet.")
    with wc2, st.container(border=True):
        section("Average base salary by department")
        if headcount_df is not None and not headcount_df.empty:
            st.plotly_chart(charts.avg_salary_chart(headcount_df), use_container_width=True,
                             config={"displayModeBar": False})
        else:
            st.info("Gold headcount table not found yet.")
