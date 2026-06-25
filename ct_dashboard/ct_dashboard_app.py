"""
============================================================
ClinicalTrials.gov Phase Analysis Dashboard
Data Source : ClinicalTrials.gov API v2
Stack       : Python · Streamlit · Plotly · Pandas
Author      : Portfolio Project — Nitin Wankhade
============================================================

Run:
    pip install -r requirements.txt
    streamlit run ct_dashboard_app.py
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import io
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClinicalTrials.gov Dashboard",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #F0F4F8 !important; }
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1320px !important;
}
#MainMenu, footer { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1E293B 0%, #0F172A 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #CBD5E1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #F1F5F9 !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #F1F5F9 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stTextInput input::placeholder {
    color: rgba(255,255,255,0.35) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.35) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(37,99,235,0.45) !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }
[data-testid="stSidebar"] .stCaption { color: #475569 !important; }

/* ── KPI cards ── */
.kpi-card {
    background: #ffffff !important;
    border-radius: 14px !important;
    padding: 1.3rem 1rem 1rem !important;
    box-shadow: 0 1px 3px rgba(15,23,42,0.05), 0 4px 20px rgba(15,23,42,0.07) !important;
    border: 1px solid #E2E8F0 !important;
    position: relative !important;
    overflow: hidden !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    text-align: center !important;
}
.kpi-card:hover { transform: translateY(-3px) !important; box-shadow: 0 8px 30px rgba(15,23,42,0.13) !important; }
.kpi-accent { position: absolute !important; top: 0 !important; left: 0 !important; right: 0 !important; height: 4px !important; border-radius: 14px 14px 0 0 !important; }
.kpi-icon { font-size: 1.5rem !important; display: block !important; margin-bottom: 0.5rem !important; }
.kpi-value {
    font-size: 1.85rem !important; font-weight: 800 !important; color: #000000 !important;
    line-height: 1 !important; letter-spacing: -0.02em !important; margin-bottom: 0.3rem !important;
}
.kpi-label {
    font-size: 0.72rem !important; color: #000000 !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.07em !important;
}
.kpi-delta {
    display: inline-block !important; font-size: 0.78rem !important; font-weight: 600 !important;
    padding: 0.15rem 0.55rem !important; border-radius: 20px !important; margin-top: 0.45rem !important;
}
.delta-green  { background: #D1FAE5 !important; color: #065F46 !important; }
.delta-blue   { background: #DBEAFE !important; color: #1E40AF !important; }
.delta-amber  { background: #FEF3C7 !important; color: #92400E !important; }
.delta-red    { background: #FEE2E2 !important; color: #991B1B !important; }

/* ── Dashboard header ── */
.dash-header {
    background: linear-gradient(135deg, #1E3A5F 0%, #1D4ED8 55%, #0EA5E9 100%);
    border-radius: 18px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 24px rgba(29,78,216,0.25);
}
.dash-header h1 {
    font-size: 1.75rem !important; font-weight: 800 !important;
    color: white !important; margin: 0 !important; letter-spacing: -0.02em !important;
}
.dash-header p { font-size: 0.88rem; color: rgba(255,255,255,0.72); margin: 0.4rem 0 0 !important; }
.dash-badge {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 50px;
    padding: 0.4rem 1.1rem;
    font-size: 0.82rem;
    font-weight: 500;
    color: white;
    white-space: nowrap;
}

/* ── Feature cards (landing page) ── */
.feature-card {
    background: white;
    border-radius: 14px;
    padding: 1.6rem 1.3rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 12px rgba(15,23,42,0.06);
    text-align: center;
    height: 100%;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.feature-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(15,23,42,0.11); }
.feature-icon { font-size: 2rem; display: block; margin-bottom: 0.75rem; }
.feature-title { font-size: 1rem; font-weight: 700; color: #1E293B; margin-bottom: 0.4rem; }
.feature-desc { font-size: 0.84rem; color: #64748B; line-height: 1.55; }

/* ── Section titles ── */
.sec-title {
    font-size: 1rem; font-weight: 700; color: #1E293B;
    letter-spacing: -0.01em; margin: 1.2rem 0 0.8rem;
    padding-bottom: 0.5rem; border-bottom: 2px solid #E2E8F0;
}

/* ── Example query pills ── */
.query-pills { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }
.query-pill {
    background: #EFF6FF; border: 1px solid #BFDBFE;
    color: #1D4ED8; border-radius: 20px;
    padding: 0.35rem 0.9rem; font-size: 0.82rem; font-weight: 500;
    display: inline-block;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: white !important;
    border-radius: 12px !important;
    padding: 0.3rem !important;
    border: 1px solid #E2E8F0 !important;
    gap: 0.15rem !important;
    box-shadow: 0 1px 4px rgba(15,23,42,0.05) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    color: #64748B !important;
    padding: 0.45rem 1.1rem !important;
    transition: all 0.15s !important;
    font-size: 0.9rem !important;
}
.stTabs [aria-selected="true"] {
    background: #2563EB !important;
    color: white !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ── Alerts ── */
.stAlert { border-radius: 10px !important; }

/* ── Download buttons ── */
.stDownloadButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover { transform: translateY(-1px) !important; }

/* ── HR ── */
hr { border-color: #E2E8F0 !important; margin: 1.2rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
HEADERS  = {
    "Accept"    : "application/json",
    "User-Agent": "ClinicalTrialsDashboard/1.0 (portfolio project)",
}

PHASE_ORDER  = ["Early Phase 1", "Phase 1", "Phase 1/Phase 2",
                 "Phase 2", "Phase 2/Phase 3", "Phase 3", "Phase 4", "N/A"]
PHASE_COLORS = {
    "Early Phase 1"  : "#BAE6FD",
    "Phase 1"        : "#7DD3FC",
    "Phase 1/Phase 2": "#38BDF8",
    "Phase 2"        : "#34D399",
    "Phase 2/Phase 3": "#10B981",
    "Phase 3"        : "#F59E0B",
    "Phase 4"        : "#EF4444",
    "N/A"            : "#CBD5E1",
}
STATUS_COLORS = {
    "RECRUITING"             : "#10B981",
    "COMPLETED"              : "#2563EB",
    "ACTIVE_NOT_RECRUITING"  : "#F59E0B",
    "NOT_YET_RECRUITING"     : "#38BDF8",
    "TERMINATED"             : "#EF4444",
    "WITHDRAWN"              : "#EC4899",
    "SUSPENDED"              : "#D97706",
    "ENROLLING_BY_INVITATION": "#06B6D4",
    "UNKNOWN"                : "#94A3B8",
}


# ── Chart style helper ────────────────────────────────────────────────────────

def _style(fig: go.Figure, height: int = None, title: str = None) -> go.Figure:
    """Apply consistent visual style to every Plotly figure."""
    layout = dict(
        font          = dict(family="Inter, sans-serif", size=12, color="#374151"),
        plot_bgcolor  = "white",
        paper_bgcolor = "white",
        margin        = dict(t=55 if title else 30, b=20, l=10, r=10),
        hoverlabel    = dict(
            bgcolor    = "white",
            bordercolor= "#E2E8F0",
            font       = dict(family="Inter", size=12, color="#1E293B"),
        ),
        legend = dict(
            bgcolor     = "rgba(255,255,255,0.9)",
            bordercolor = "#E2E8F0",
            borderwidth = 1,
            font        = dict(size=11),
        ),
    )
    if height:
        layout["height"] = height
    if title:
        layout["title"] = dict(
            text = title,
            font = dict(size=14, color="#1E293B"),
            x    = 0.02,
            xanchor = "left",
        )
    fig.update_layout(**layout)
    fig.update_xaxes(
        gridcolor="#F1F5F9", linecolor="#E2E8F0",
        showgrid=True, tickfont=dict(size=11),
    )
    fig.update_yaxes(
        gridcolor="#F1F5F9", linecolor="#E2E8F0",
        showgrid=True, tickfont=dict(size=11),
    )
    return fig


# ── KPI card helper ───────────────────────────────────────────────────────────

_DELTA_MAP = {
    "delta-green" : ("#D1FAE5", "#065F46"),
    "delta-blue"  : ("#DBEAFE", "#1E40AF"),
    "delta-amber" : ("#FEF3C7", "#92400E"),
    "delta-red"   : ("#FEE2E2", "#991B1B"),
}

def render_kpi_row(kpi_data: list) -> None:
    """Render KPI cards inside an isolated iframe — immune to Streamlit theme CSS."""
    cards = ""
    for (icon, label, value, delta, delta_cls, accent) in kpi_data:
        dbg, dfg = _DELTA_MAP.get(delta_cls, ("#DBEAFE", "#1E40AF"))
        delta_html = (
            f'<span style="display:inline-block;margin-top:6px;padding:2px 10px;'
            f'border-radius:20px;font-size:11px;font-weight:600;'
            f'background:{dbg};color:{dfg};">{delta}</span>'
        ) if delta else ""
        cards += f"""
        <div style="background:#fff;border-radius:12px;padding:18px 14px 14px;
                    box-shadow:0 2px 14px rgba(0,0,0,0.09);border:1px solid #e2e8f0;
                    text-align:center;position:relative;overflow:hidden;flex:1;min-width:0;">
            <div style="position:absolute;top:0;left:0;right:0;height:4px;
                        background:{accent};border-radius:12px 12px 0 0;"></div>
            <div style="font-size:26px;margin-bottom:6px;line-height:1;">{icon}</div>
            <div style="font-size:30px;font-weight:800;color:#111111;
                        line-height:1;margin-bottom:6px;">{value}</div>
            <div style="font-size:11px;font-weight:700;color:#333333;
                        text-transform:uppercase;letter-spacing:1px;">{label}</div>
            {delta_html}
        </div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }}
  body {{ background:transparent; padding:4px 2px; }}
  .row {{ display:flex; gap:14px; }}
</style>
</head><body>
<div class="row">{cards}</div>
</body></html>"""
    components.html(html, height=175, scrolling=False)


# ── API functions ─────────────────────────────────────────────────────────────

def fetch_studies(
    condition   : str  = "",
    intervention: str  = "",
    sponsor     : str  = "",
    phases      : list = None,
    statuses    : list = None,
    study_type  : str  = "ALL",
    max_results : int  = 200,
) -> list[dict]:
    """Query ClinicalTrials.gov API v2 with pagination."""
    params = {
        "pageSize"  : min(max_results, 1000),
        "countTotal": "true",
        "format"    : "json",
    }
    if condition:    params["query.cond"] = condition
    if intervention: params["query.intr"] = intervention
    if sponsor:      params["query.lead"] = sponsor
    if phases:       params["filter.phase"] = "|".join(phases)
    if statuses:     params["filter.overallStatus"] = "|".join(statuses)
    if study_type != "ALL":
        params["filter.studyType"] = study_type

    all_studies = []
    page_token  = None
    fetched     = 0

    progress = st.progress(0, text="Fetching studies from ClinicalTrials.gov...")

    while fetched < max_results:
        if page_token:
            params["pageToken"] = page_token
        else:
            params.pop("pageToken", None)

        try:
            r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.HTTPError:
            st.error(f"API Error {r.status_code}: {r.text[:300]}")
            break
        except Exception as e:
            st.error(f"Request failed: {e}")
            break

        studies = data.get("studies", [])
        if not studies:
            break

        all_studies.extend(studies)
        fetched     += len(studies)
        total_count  = data.get("totalCount", fetched)
        page_token   = data.get("nextPageToken")

        pct = min(fetched / max_results, 1.0)
        progress.progress(pct, text=f"Fetched {fetched:,} / {min(max_results, total_count):,} studies...")

        if not page_token or fetched >= max_results:
            break
        time.sleep(0.3)

    progress.empty()
    return all_studies[:max_results]


# ── Data parsing ──────────────────────────────────────────────────────────────

def _get(d: dict, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default if k == keys[-1] else {})
    return d


def parse_phase(phases: list) -> str:
    if not phases:
        return "N/A"
    mapping = {
        "PHASE1"      : "Phase 1",
        "PHASE2"      : "Phase 2",
        "PHASE3"      : "Phase 3",
        "PHASE4"      : "Phase 4",
        "EARLY_PHASE1": "Early Phase 1",
        "NA"          : "N/A",
    }
    mapped = [mapping.get(p, p) for p in phases]
    return mapped[0] if len(mapped) == 1 else "/".join(mapped)


def parse_date(date_str: str) -> pd.Timestamp | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return pd.to_datetime(date_str, format=fmt)
        except Exception:
            pass
    return None


def studies_to_df(studies: list[dict]) -> pd.DataFrame:
    rows = []
    for s in studies:
        ps = s.get("protocolSection", {})

        ident   = ps.get("identificationModule", {})
        status  = ps.get("statusModule", {})
        design  = ps.get("designModule", {})
        sponsor = ps.get("sponsorCollaboratorsModule", {})
        cond    = ps.get("conditionsModule", {})
        arms    = ps.get("armsInterventionsModule", {})
        locs    = ps.get("contactsLocationsModule", {})

        phases_raw  = design.get("phases", [])
        phase_str   = parse_phase(phases_raw)
        enroll_info = design.get("enrollmentInfo", {})
        enrollment  = enroll_info.get("count")
        enroll_type = enroll_info.get("type", "")

        start_raw  = _get(status, "startDateStruct", "date", default="")
        pcd_raw    = _get(status, "primaryCompletionDateStruct", "date", default="")
        start_date = parse_date(start_raw)
        pcd        = parse_date(pcd_raw)

        locations  = locs.get("locations", [])
        countries  = list({loc.get("country", "") for loc in locations if loc.get("country")})

        interventions = arms.get("interventions", [])
        intr_names    = [i.get("name", "") for i in interventions]
        intr_types    = list({i.get("type", "") for i in interventions})

        rows.append({
            "nct_id"           : ident.get("nctId", ""),
            "title"            : ident.get("briefTitle", ident.get("officialTitle", "")),
            "status"           : status.get("overallStatus", "UNKNOWN"),
            "phase"            : phase_str,
            "study_type"       : design.get("studyType", ""),
            "enrollment"       : enrollment,
            "enrollment_type"  : enroll_type,
            "start_date"       : start_date,
            "primary_completion": pcd,
            "start_year"       : start_date.year if start_date else None,
            "lead_sponsor"     : _get(sponsor, "leadSponsor", "name", default="Unknown"),
            "sponsor_class"    : _get(sponsor, "leadSponsor", "class", default=""),
            "conditions"       : ", ".join(cond.get("conditions", [])[:3]),
            "interventions"    : ", ".join(intr_names[:3]),
            "intervention_types": ", ".join(intr_types),
            "countries"        : ", ".join(countries[:5]),
            "country_count"    : len(countries),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["enrollment"] = pd.to_numeric(df["enrollment"], errors="coerce")
    return df


# ── Chart helpers ─────────────────────────────────────────────────────────────

def chart_phase_distribution(df: pd.DataFrame) -> go.Figure:
    counts = (
        df["phase"]
        .value_counts()
        .reindex([p for p in PHASE_ORDER if p in df["phase"].unique()])
        .dropna()
        .reset_index()
    )
    counts.columns = ["phase", "count"]

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        subplot_titles=("Phase Share", "Trial Count by Phase"),
    )
    fig.add_trace(
        go.Pie(
            labels=counts["phase"], values=counts["count"],
            marker_colors=[PHASE_COLORS.get(p, "#888") for p in counts["phase"]],
            hole=0.45, textposition="outside",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
            marker=dict(line=dict(color="white", width=2)),
        ), row=1, col=1,
    )
    fig.add_trace(
        go.Bar(
            x=counts["phase"], y=counts["count"],
            marker_color=[PHASE_COLORS.get(p, "#888") for p in counts["phase"]],
            marker=dict(line=dict(color="white", width=1), cornerradius=6),
            text=counts["count"], textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y} trials<extra></extra>",
        ), row=1, col=2,
    )
    _style(fig, height=420)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(tickangle=-30, row=1, col=2)
    return fig


def chart_status_breakdown(df: pd.DataFrame) -> go.Figure:
    counts = df["status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)

    fig = px.bar(
        counts.head(10), x="count", y="status",
        orientation="h", text="pct",
        color="status", color_discrete_map=STATUS_COLORS,
        labels={"count": "Number of Trials", "status": ""},
        height=400,
    )
    fig.update_traces(
        texttemplate="%{text}%",
        textposition="outside",
        marker=dict(line=dict(color="white", width=1), cornerradius=4),
    )
    _style(fig, title="Trial Status Breakdown")
    fig.update_layout(
        showlegend=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(t=55, b=20, r=70),
    )
    return fig


def chart_enrollment_over_time(df: pd.DataFrame) -> go.Figure:
    by_year = (
        df[df["start_year"].notna() & (df["start_year"] >= 2000) & (df["start_year"] <= 2025)]
        .groupby("start_year")
        .agg(
            trial_count     =("nct_id",     "count"),
            avg_enrollment  =("enrollment", "mean"),
        )
        .reset_index()
    )
    by_year["avg_enrollment"] = by_year["avg_enrollment"].round(0)

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Trials Started per Year", "Average Enrollment per Year"),
        shared_xaxes=True, vertical_spacing=0.14,
    )
    fig.add_trace(
        go.Bar(
            x=by_year["start_year"], y=by_year["trial_count"],
            marker=dict(color="#2563EB", cornerradius=4,
                        line=dict(color="white", width=1)),
            name="Trials",
            hovertemplate="<b>%{x}</b><br>Trials: %{y}<extra></extra>",
        ), row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=by_year["start_year"], y=by_year["avg_enrollment"],
            mode="lines+markers",
            line=dict(color="#F59E0B", width=2.5),
            marker=dict(size=7, color="#F59E0B",
                        line=dict(color="white", width=2)),
            name="Avg Enrollment",
            hovertemplate="<b>%{x}</b><br>Avg enrollment: %{y:,.0f}<extra></extra>",
            fill="tozeroy",
            fillcolor="rgba(245,158,11,0.08)",
        ), row=2, col=1,
    )
    _style(fig, height=500)
    fig.update_layout(showlegend=False)
    return fig


def chart_top_sponsors(df: pd.DataFrame) -> go.Figure:
    top = (
        df.groupby("lead_sponsor")
        .agg(trials=("nct_id", "count"))
        .sort_values("trials", ascending=False)
        .head(15)
        .reset_index()
    )
    fig = px.bar(
        top, x="trials", y="lead_sponsor",
        orientation="h", text="trials",
        color="trials",
        color_continuous_scale=[[0, "#BAE6FD"], [0.5, "#2563EB"], [1, "#1E3A5F"]],
        labels={"trials": "Number of Trials", "lead_sponsor": ""},
        height=500,
    )
    fig.update_traces(
        textposition="outside",
        marker=dict(line=dict(color="white", width=1), cornerradius=4),
    )
    _style(fig, title="Top 15 Lead Sponsors by Trial Count")
    fig.update_layout(
        showlegend=False, coloraxis_showscale=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(t=55, b=20, r=70),
    )
    return fig


def chart_phase_x_status(df: pd.DataFrame) -> go.Figure:
    pivot = (
        df.groupby(["phase", "status"])
        .size()
        .reset_index(name="count")
    )
    pivot = pivot[pivot["phase"].isin(PHASE_ORDER)]
    fig = px.bar(
        pivot, x="phase", y="count",
        color="status", color_discrete_map=STATUS_COLORS,
        labels={"count": "Trials", "phase": "Phase", "status": "Status"},
        height=420,
        category_orders={"phase": PHASE_ORDER},
    )
    fig.update_traces(marker=dict(line=dict(color="white", width=0.5)))
    _style(fig, title="Phase × Status Mix")
    fig.update_layout(xaxis_tickangle=-30, legend=dict(orientation="v"))
    return fig


def chart_sponsor_class(df: pd.DataFrame) -> go.Figure:
    class_map = {
        "INDUSTRY" : "Industry",
        "NIH"      : "NIH",
        "FED"      : "Federal",
        "OTHER_GOV": "Other Gov",
        "INDIV"    : "Individual",
        "NETWORK"  : "Network",
        "AMBIG"    : "Ambiguous",
        "UNKNOWN"  : "Unknown",
        ""         : "Unknown",
    }
    df2 = df.copy()
    df2["sponsor_type"] = df2["sponsor_class"].map(class_map).fillna("Other")
    counts = df2["sponsor_type"].value_counts().reset_index()
    counts.columns = ["type", "count"]

    fig = px.pie(
        counts, values="count", names="type",
        hole=0.48,
        color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B", "#EF4444",
                                  "#8B5CF6", "#06B6D4", "#EC4899"],
        height=400,
    )
    fig.update_traces(
        textposition="outside", textinfo="percent+label",
        marker=dict(line=dict(color="white", width=2)),
    )
    _style(fig, title="Sponsor Type Distribution")
    fig.update_layout(showlegend=False)
    return fig


# ── Excel export ──────────────────────────────────────────────────────────────

def to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    display_cols = [
        "nct_id", "title", "phase", "status", "enrollment",
        "start_date", "primary_completion",
        "lead_sponsor", "conditions", "interventions", "countries",
    ]
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df[display_cols].to_excel(writer, sheet_name="All Trials", index=False)

        phase_sum = df["phase"].value_counts().reset_index()
        phase_sum.columns = ["Phase", "Count"]
        phase_sum.to_excel(writer, sheet_name="Phase Summary", index=False)

        status_sum = df["status"].value_counts().reset_index()
        status_sum.columns = ["Status", "Count"]
        status_sum.to_excel(writer, sheet_name="Status Summary", index=False)

        top_sp = (
            df.groupby("lead_sponsor")["nct_id"].count()
            .reset_index().rename(columns={"nct_id": "Trial Count"})
            .sort_values("Trial Count", ascending=False)
            .head(50)
        )
        top_sp.to_excel(writer, sheet_name="Top Sponsors", index=False)

        for sheet in writer.sheets.values():
            for col in sheet.columns:
                w = max(len(str(c.value or "")) for c in col)
                sheet.column_dimensions[col[0].column_letter].width = min(w + 4, 50)

    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
#  Streamlit UI
# ══════════════════════════════════════════════════════════════════════════════

def main():

    # ── Gradient header ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="dash-header">
        <div>
            <h1>🧬 ClinicalTrials.gov Dashboard</h1>
            <p>Real-time Pharma R&D Intelligence · ClinicalTrials.gov API v2</p>
        </div>
        <div class="dash-badge">Portfolio · Nitin Wankhade</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🔍 Search")

        condition    = st.text_input("Disease / Condition",  placeholder="e.g. Diabetes, Lupus")
        intervention = st.text_input("Drug / Intervention",  placeholder="e.g. Metformin, Keytruda")
        sponsor      = st.text_input("Lead Sponsor",          placeholder="e.g. Pfizer, NIH")

        st.markdown("---")
        st.markdown("### Filters")

        phase_options = {
            "Early Phase 1": "EARLY_PHASE1",
            "Phase 1"      : "PHASE1",
            "Phase 2"      : "PHASE2",
            "Phase 3"      : "PHASE3",
            "Phase 4"      : "PHASE4",
            "N/A"          : "NA",
        }
        selected_phases = st.multiselect(
            "Phase", options=list(phase_options.keys()), default=[]
        )

        status_options = {
            "Recruiting"             : "RECRUITING",
            "Completed"              : "COMPLETED",
            "Active, not recruiting" : "ACTIVE_NOT_RECRUITING",
            "Not yet recruiting"     : "NOT_YET_RECRUITING",
            "Terminated"             : "TERMINATED",
            "Withdrawn"              : "WITHDRAWN",
            "Suspended"              : "SUSPENDED",
        }
        selected_statuses = st.multiselect(
            "Overall Status", options=list(status_options.keys()), default=[]
        )

        study_type = st.selectbox(
            "Study Type",
            options=["ALL", "INTERVENTIONAL", "OBSERVATIONAL"],
            index=0,
        )

        max_results = st.slider(
            "Max Results", min_value=50, max_value=1000, value=200, step=50
        )

        st.markdown("---")
        search_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

        st.markdown("---")
        st.caption("📌 Data: ClinicalTrials.gov · API v2")
        st.caption("🔬 Portfolio Project · Nitin Wankhade")

    # ── Landing page ───────────────────────────────────────────────────────────
    if not search_btn:
        features = [
            ("📊", "Phase Analysis",    "Visualize trial distribution across all clinical phases with interactive charts."),
            ("📈", "Trend Intelligence","Track trial volumes and enrollment patterns over time since 2000."),
            ("🏢", "Sponsor Insights",  "Identify top industry sponsors, NIH leaders, and institutional players."),
            ("🗺️", "Status & Mix",      "Understand recruiting vs completed vs terminated trial landscapes."),
        ]
        cols = st.columns(4)
        for col, (icon, title, desc) in zip(cols, features):
            with col:
                st.markdown(f"""
                <div class="feature-card">
                    <span class="feature-icon">{icon}</span>
                    <div class="feature-title">{title}</div>
                    <div class="feature-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:white;border-radius:14px;padding:1.5rem 1.75rem;
                    border:1px solid #E2E8F0;box-shadow:0 2px 12px rgba(15,23,42,0.06);">
            <div style="font-size:0.95rem;font-weight:700;color:#1E293B;margin-bottom:0.75rem;">
                💡 Example Queries — try one in the sidebar
            </div>
            <div class="query-pills">
                <span class="query-pill">🔬 Condition: Lupus Nephritis</span>
                <span class="query-pill">💊 Drug: Pembrolizumab</span>
                <span class="query-pill">🏢 Sponsor: Novartis</span>
                <span class="query-pill">🔬 Condition: Type 2 Diabetes</span>
                <span class="query-pill">💊 Drug: Ozempic</span>
                <span class="query-pill">🏢 Sponsor: Pfizer</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Validate ───────────────────────────────────────────────────────────────
    if not any([condition, intervention, sponsor]):
        st.error("Please enter at least one search term (Condition, Drug, or Sponsor).")
        return

    # ── Fetch data ─────────────────────────────────────────────────────────────
    phases_api   = [phase_options[p]   for p in selected_phases]   if selected_phases   else None
    statuses_api = [status_options[s]  for s in selected_statuses] if selected_statuses else None

    with st.spinner("Querying ClinicalTrials.gov API v2..."):
        raw = fetch_studies(
            condition    = condition,
            intervention = intervention,
            sponsor      = sponsor,
            phases       = phases_api,
            statuses     = statuses_api,
            study_type   = study_type,
            max_results  = max_results,
        )

    if not raw:
        st.warning("No studies found. Try different search terms or remove some filters.")
        return

    df = studies_to_df(raw)
    if df.empty:
        st.warning("Data fetched but could not be parsed. Please try again.")
        return

    st.success(f"✅ Loaded **{len(df):,}** clinical trials.")

    # ── KPI Cards ──────────────────────────────────────────────────────────────
    total      = len(df)
    recruiting = int((df["status"] == "RECRUITING").sum())
    completed  = int((df["status"] == "COMPLETED").sum())
    terminated = int((df["status"] == "TERMINATED").sum())
    med_enroll = df["enrollment"].median()
    top_phase  = df["phase"].mode()[0] if not df["phase"].empty else "N/A"

    rec_pct  = f"{recruiting / total * 100:.0f}% of total"
    comp_pct = f"{completed  / total * 100:.0f}% of total"
    term_pct = f"{terminated / total * 100:.0f}% of total"
    med_str  = f"{int(med_enroll):,}" if not np.isnan(med_enroll) else "N/A"

    kpi_data = [
        ("🔬", "Total Trials",     f"{total:,}",     "",        "delta-blue",  "#2563EB"),
        ("🟢", "Recruiting",        f"{recruiting:,}", rec_pct,  "delta-green", "#10B981"),
        ("✅", "Completed",         f"{completed:,}",  comp_pct, "delta-blue",  "#2563EB"),
        ("⚠️", "Terminated",        f"{terminated:,}", term_pct, "delta-red",   "#EF4444"),
        ("📐", "Median Enrollment", med_str,           top_phase, "delta-amber", "#F59E0B"),
    ]
    render_kpi_row(kpi_data)

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊  Phase Analysis",
        "📈  Trends Over Time",
        "🏢  Sponsors",
        "🗺️  Status & Mix",
        "📋  Data Table",
    ])

    # ── Tab 1: Phase Analysis ──────────────────────────────────────────────────
    with tab1:
        st.plotly_chart(chart_phase_distribution(df), use_container_width=True)

        col1, col2 = st.columns([3, 2])
        with col1:
            st.plotly_chart(chart_phase_x_status(df), use_container_width=True)
        with col2:
            st.markdown('<div class="sec-title">Phase Statistics</div>', unsafe_allow_html=True)
            phase_stats = (
                df.groupby("phase")
                .agg(
                    count       =("nct_id",     "count"),
                    avg_enroll  =("enrollment", "mean"),
                    total_enroll=("enrollment", "sum"),
                )
                .reset_index()
            )
            phase_stats["avg_enroll"]   = phase_stats["avg_enroll"].round(0).fillna(0).astype(int)
            phase_stats["total_enroll"] = phase_stats["total_enroll"].fillna(0).astype(int)
            phase_stats.columns = ["Phase", "# Trials", "Avg Enrollment", "Total Enrollment"]
            st.dataframe(phase_stats, use_container_width=True, hide_index=True, height=380)

    # ── Tab 2: Trends ──────────────────────────────────────────────────────────
    with tab2:
        st.plotly_chart(chart_enrollment_over_time(df), use_container_width=True)

        st.markdown('<div class="sec-title">Phase Mix Over Time</div>', unsafe_allow_html=True)
        phase_trend = (
            df[df["start_year"].notna() & (df["start_year"] >= 2005)]
            .groupby(["start_year", "phase"])
            .size()
            .reset_index(name="count")
        )
        fig_trend = px.area(
            phase_trend, x="start_year", y="count",
            color="phase", color_discrete_map=PHASE_COLORS,
            labels={"start_year": "Start Year", "count": "Trial Count", "phase": "Phase"},
            height=380,
            category_orders={"phase": PHASE_ORDER},
        )
        _style(fig_trend)
        st.plotly_chart(fig_trend, use_container_width=True)

    # ── Tab 3: Sponsors ────────────────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(chart_top_sponsors(df), use_container_width=True)
        with col2:
            st.plotly_chart(chart_sponsor_class(df), use_container_width=True)

        st.markdown('<div class="sec-title">Sponsor Leaderboard</div>', unsafe_allow_html=True)
        sponsor_lb = (
            df.groupby("lead_sponsor")
            .agg(
                trials          =("nct_id",     "count"),
                avg_enrollment  =("enrollment", "mean"),
                total_enrollment=("enrollment", "sum"),
                phases          =("phase",      lambda x: ", ".join(sorted(x.unique()))),
            )
            .sort_values("trials", ascending=False)
            .head(30)
            .reset_index()
        )
        sponsor_lb["avg_enrollment"]   = sponsor_lb["avg_enrollment"].round(0).fillna(0).astype(int)
        sponsor_lb["total_enrollment"] = sponsor_lb["total_enrollment"].fillna(0).astype(int)
        sponsor_lb.columns = ["Sponsor", "Trials", "Avg Enrollment", "Total Enrollment", "Phases"]
        st.dataframe(sponsor_lb, use_container_width=True, hide_index=True)

    # ── Tab 4: Status & Mix ────────────────────────────────────────────────────
    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_status_breakdown(df), use_container_width=True)
        with col2:
            type_counts = df["study_type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            fig_type = px.pie(
                type_counts, values="count", names="type",
                hole=0.48,
                color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B"],
                height=400,
            )
            fig_type.update_traces(
                textposition="outside", textinfo="percent+label",
                marker=dict(line=dict(color="white", width=2)),
            )
            _style(fig_type, title="Study Type Distribution")
            fig_type.update_layout(showlegend=False)
            st.plotly_chart(fig_type, use_container_width=True)

        st.markdown('<div class="sec-title">Enrollment Size Distribution</div>', unsafe_allow_html=True)
        enroll_df = df[df["enrollment"].notna() & (df["enrollment"] > 0) & (df["enrollment"] < 50000)]
        fig_enroll = px.histogram(
            enroll_df, x="enrollment", color="phase",
            color_discrete_map=PHASE_COLORS,
            nbins=40, log_y=True,
            labels={"enrollment": "Enrollment Count"},
            height=360,
        )
        _style(fig_enroll, title="Enrollment Distribution (log scale, capped at 50k)")
        st.plotly_chart(fig_enroll, use_container_width=True)

    # ── Tab 5: Data Table ──────────────────────────────────────────────────────
    with tab5:
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            phase_filter = st.multiselect(
                "Filter by Phase", options=sorted(df["phase"].unique()), default=[]
            )
        with fc2:
            status_filter = st.multiselect(
                "Filter by Status", options=sorted(df["status"].unique()), default=[]
            )
        with fc3:
            search_term = st.text_input("Search title / NCT ID", "")

        filtered = df.copy()
        if phase_filter:
            filtered = filtered[filtered["phase"].isin(phase_filter)]
        if status_filter:
            filtered = filtered[filtered["status"].isin(status_filter)]
        if search_term:
            mask = (
                filtered["title"].str.contains(search_term, case=False, na=False)
                | filtered["nct_id"].str.contains(search_term, case=False, na=False)
            )
            filtered = filtered[mask]

        st.caption(f"Showing **{len(filtered):,}** of **{len(df):,}** studies")

        display_cols = [
            "nct_id", "title", "phase", "status", "enrollment",
            "start_date", "lead_sponsor", "conditions",
        ]
        st.dataframe(
            filtered[display_cols].rename(columns={
                "nct_id"      : "NCT ID",
                "title"       : "Title",
                "phase"       : "Phase",
                "status"      : "Status",
                "enrollment"  : "Enrollment",
                "start_date"  : "Start Date",
                "lead_sponsor": "Lead Sponsor",
                "conditions"  : "Conditions",
            }),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

        st.divider()
        col_exp1, col_exp2 = st.columns(2)
        fname_base = condition or intervention or sponsor or "results"
        with col_exp1:
            st.download_button(
                label="📥 Download Excel",
                data=to_excel(filtered),
                file_name=f"ClinicalTrials_{fname_base}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col_exp2:
            st.download_button(
                label="📥 Download CSV",
                data=filtered[display_cols].to_csv(index=False).encode("utf-8"),
                file_name=f"ClinicalTrials_{fname_base}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
