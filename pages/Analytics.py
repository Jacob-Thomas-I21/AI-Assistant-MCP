"""pages/Analytics.py — Analytics dashboard with tight Plotly, stat cards, empty states."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from feedback.collector import (
    get_stats, get_by_type, get_recent,
    get_satisfaction_over_time, get_confidence_distribution, export_to_csv
)

st.set_page_config(page_title="Analytics — AI Platform", page_icon="", layout="wide")

PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    background-color: #f5f5f4 !important; color: #1c1917 !important;
}
/* ── Content width constraint ── */
[data-testid="stMainBlockContainer"] {
    max-width: 960px !important;
    margin: 0 auto !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e7e5e4 !important; }
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; color: #57534e !important; font-size: 0.8rem !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color: #1c1917 !important; font-size: 0.85rem !important; font-weight: 600 !important; }
[data-testid="stSidebarNavLink"] { border-radius:6px !important; font-size:0.82rem !important; font-weight:500 !important; color:#44403c !important; transition: background 0.12s !important; }
[data-testid="stSidebarNavLink"]:hover { background:#f5f5f4 !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] { background:#f0fdf4 !important; color:#15803d !important; }
.stButton > button { font-family:'Inter',sans-serif !important; font-size:0.8rem !important; font-weight:500 !important; background:#1c1917 !important; color:#fafaf9 !important; border:none !important; border-radius:6px !important; padding:0.45rem 1rem !important; transition:background 0.12s !important; }
.stButton > button:hover { background:#292524 !important; color:#fafaf9 !important; }
#MainMenu, footer, header { visibility:hidden !important; }
[data-testid="stToolbar"] { display:none !important; }
.stDeployButton { display:none !important; }
.stAlert { display:none !important; }
[data-testid="stDataFrame"] { border:1px solid #e7e5e4 !important; border-radius:6px !important; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#d6d3d1; border-radius:4px; }
hr { border:none; border-top:1px solid #e7e5e4 !important; margin:1.5rem 0 !important; }
</style>
"""
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ── Plotly theme — tight axes, no titles, white bg ─────────────────────────────
PLOTLY_THEME = {
    "paper_bgcolor": "#ffffff",
    "plot_bgcolor":  "#ffffff",
    "font": {"family": "Inter, system-ui, sans-serif", "color": "#1c1917", "size": 11},
    "xaxis": {
        "gridcolor": "#f5f5f4", "linecolor": "#e7e5e4",
        "tickfont": {"size": 10, "color": "#78716c"},
        "title": {"text": ""},
    },
    "yaxis": {
        "gridcolor": "#f5f5f4", "linecolor": "#e7e5e4",
        "tickfont": {"size": 10, "color": "#78716c"},
        "title": {"text": ""},
    },
    "margin": {"t": 8, "b": 24, "l": 24, "r": 8},
}

# ── HTML helpers ───────────────────────────────────────────────────────────────
def section_label(text):
    return f'<p style="font-size:0.7rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#a8a29e;margin:0 0 0.6rem;">{text}</p>'

def stat_card(value, label, sub=None):
    sub_html = f'<p style="font-size:0.68rem;color:#a8a29e;margin:0.2rem 0 0;">{sub}</p>' if sub else ""
    return f"""
<div style="background:#fff;border:1px solid #e7e5e4;border-radius:8px;padding:1.1rem 1.25rem;">
    <p style="font-size:0.62rem;font-weight:600;letter-spacing:0.08em;color:#a8a29e;
    text-transform:uppercase;margin:0 0 0.4rem;">{label}</p>
    <p style="font-size:1.55rem;font-weight:600;letter-spacing:-0.03em;color:#1c1917;
    margin:0;font-family:'JetBrains Mono',monospace;">{value}</p>
    {sub_html}
</div>"""

def empty_state(msg, cta=None):
    cta_html = f'<p style="font-size:0.75rem;color:#78716c;margin:0.5rem 0 0;">{cta}</p>' if cta else ""
    return f"""
<div style="border:1px dashed #d6d3d1;border-radius:8px;padding:2rem;text-align:center;margin:0.5rem 0;">
    <p style="font-size:0.8rem;font-weight:500;color:#44403c;margin:0 0 0.2rem;">{msg}</p>
    {cta_html}
</div>"""

def chart_label(text):
    return f'<p style="font-size:0.75rem;font-weight:600;color:#1c1917;margin:0 0 0.6rem;letter-spacing:-0.01em;">{text}</p>'

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:1.75rem 0 1.25rem;border-bottom:1px solid #e7e5e4;margin-bottom:1.5rem;
display:flex;align-items:center;justify-content:space-between;">
    <div>
        <h1 style="font-size:1.25rem;font-weight:600;letter-spacing:-0.02em;color:#1c1917;margin:0 0 0.25rem;">Analytics</h1>
        <p style="font-size:0.8rem;color:#78716c;margin:0;">Feedback and usage data from all chat sessions.</p>
    </div>
</div>
""", unsafe_allow_html=True)

if st.button("Refresh"):
    st.rerun()

st.markdown("---")

# ── Stat cards ─────────────────────────────────────────────────────────────────
stats = get_stats()
c1, c2, c3, c4, c5 = st.columns(5)
for col, (val, label, sub) in zip(
    [c1, c2, c3, c4, c5],
    [
        (str(stats["total"]),              "Total queries",  None),
        (f"{stats['satisfaction_rate']}%", "Satisfaction",   "helpful / rated"),
        (str(stats["helpful"]),            "Helpful",        None),
        (str(stats["not_helpful"]),        "Not helpful",    None),
        (f"{stats['avg_confidence']:.2f}", "Avg confidence", "0 – 1 scale"),
    ]
):
    with col:
        st.markdown(stat_card(val, label, sub), unsafe_allow_html=True)

st.markdown("---")

# ── Charts ─────────────────────────────────────────────────────────────────────
cl, cr = st.columns(2)

with cl:
    st.markdown(chart_label("Queries by type"), unsafe_allow_html=True)
    type_data = get_by_type()
    if type_data:
        df_t = pd.DataFrame(type_data)
        colors = {
            "document": "#3b82f6", "data": "#22c55e",
            "tool": "#f97316", "unknown": "#a8a29e", "blocked": "#ef4444"
        }
        fig = px.bar(df_t, x="query_type", y="count", color="query_type",
                     color_discrete_map=colors, labels={"query_type": "", "count": ""})
        fig.update_layout(**PLOTLY_THEME, showlegend=False, height=240)
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(empty_state(
            "No queries recorded yet.",
            "Go to Chat and ask a question to see data here."
        ), unsafe_allow_html=True)

with cr:
    st.markdown(chart_label("Confidence distribution"), unsafe_allow_html=True)
    conf_data = get_confidence_distribution()
    if any(d["count"] > 0 for d in conf_data):
        df_c = pd.DataFrame(conf_data)
        colors_c = {
            "high (>0.7)": "#22c55e", "medium (0.5-0.7)": "#eab308",
            "low (0.35-0.5)": "#f97316", "insufficient (<0.35)": "#ef4444"
        }
        fig2 = px.bar(df_c, x="bucket", y="count", color="bucket",
                      color_discrete_map=colors_c, labels={"bucket": "", "count": ""})
        fig2.update_layout(**PLOTLY_THEME, showlegend=False, height=240)
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.markdown(empty_state(
            "No confidence data yet.",
            "Document queries generate confidence scores."
        ), unsafe_allow_html=True)

# ── Satisfaction trend ─────────────────────────────────────────────────────────
st.markdown(chart_label("Satisfaction over time"), unsafe_allow_html=True)
sat_data = get_satisfaction_over_time()
if len(sat_data) >= 2:
    df_s = pd.DataFrame(sat_data)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df_s["date"], y=df_s["satisfaction"], mode="lines+markers",
        line={"color": "#3b82f6", "width": 1.5},
        marker={"size": 4, "color": "#3b82f6"},
    ))
    fig3.update_layout(
        **PLOTLY_THEME, height=200,
        yaxis={"range": [0, 100], "gridcolor": "#f5f5f4",
               "tickfont": {"size": 10, "color": "#78716c"}, "title": {"text": ""}},
    )
    st.plotly_chart(fig3, use_container_width=True)
elif len(sat_data) == 1:
    st.markdown(f'<p style="font-size:0.8rem;color:#78716c;padding:0.5rem 0;">One day of data — {sat_data[0]["satisfaction"]}% satisfaction.</p>', unsafe_allow_html=True)
else:
    st.markdown(empty_state(
        "Not enough data for a trend yet.",
        "Rate at least two responses in Chat across different days."
    ), unsafe_allow_html=True)

st.markdown("---")

# ── Recent feedback table ──────────────────────────────────────────────────────
st.markdown(chart_label("Recent feedback"), unsafe_allow_html=True)
recent = get_recent(20)
if recent:
    df_r = pd.DataFrame(recent)
    cols = ["timestamp", "query_type", "rating", "confidence", "query"]
    df_d = df_r[[c for c in cols if c in df_r.columns]].rename(columns={
        "timestamp": "Time", "query_type": "Type", "rating": "Rating",
        "confidence": "Confidence", "query": "Query"
    })
    if "Query" in df_d.columns:
        df_d["Query"] = df_d["Query"].str[:80]
    st.dataframe(df_d, use_container_width=True, hide_index=True)
    csv_str = export_to_csv()
    if csv_str:
        st.download_button("Export as CSV", data=csv_str, file_name="feedback.csv", mime="text/csv")
else:
    st.markdown(empty_state(
        "No feedback recorded yet.",
        "Use the helpful / not helpful buttons after each response in Chat."
    ), unsafe_allow_html=True)
