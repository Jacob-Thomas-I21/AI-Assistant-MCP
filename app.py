"""app.py — Entry point and landing page."""
import streamlit as st

st.set_page_config(
    page_title="AI Assessment Platform",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    background-color: #f5f5f4 !important;
    color: #1c1917 !important;
}
[data-testid="stMainBlockContainer"] {
    max-width: 900px !important;
    margin: 0 auto !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e7e5e4 !important; }
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; color: #57534e !important; font-size: 0.8rem !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color: #1c1917 !important; font-size: 0.85rem !important; font-weight: 600 !important; }
[data-testid="stSidebarNavLink"] { border-radius:6px !important; font-size:0.82rem !important; font-weight:500 !important; color:#44403c !important; transition: background 0.12s, color 0.12s !important; }
[data-testid="stSidebarNavLink"]:hover { background:#f5f5f4 !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] { background:#f0fdf4 !important; color:#15803d !important; }
.stButton > button { font-family:'Inter',sans-serif !important; font-size:0.8rem !important; font-weight:500 !important; background:#1c1917 !important; color:#fafaf9 !important; border:none !important; border-radius:6px !important; padding:0.45rem 1rem !important; transition:background 0.12s !important; }
.stButton > button:hover { background:#292524 !important; color:#fafaf9 !important; }
#MainMenu, footer, header { visibility:hidden !important; }
[data-testid="stToolbar"] { display:none !important; }
.stDeployButton { display:none !important; }
.stAlert { display:none !important; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#d6d3d1; border-radius:4px; }
hr { border:none; border-top:1px solid #e7e5e4 !important; margin:1.5rem 0 !important; }
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### AI Assessment Platform")
    st.markdown("---")
    st.markdown("""
**Pages**
- Chat — query the assistant
- Analytics — feedback and usage data
- Evaluation — automated test suite

---
**Indexed sources**
- Leave policy
- Procurement process
- Shipment escalation SOP
- Branch performance CSV

**Live tools**
- Weather API
- Currency converter
    """)
    st.markdown("---")
    st.caption("LangChain · ChromaDB · MCP · Streamlit")

st.markdown("""
<div style="padding:2.5rem 0 2rem;border-bottom:1px solid #e7e5e4;margin-bottom:2rem;">
    <p style="font-size:0.65rem;font-weight:600;letter-spacing:0.1em;color:#a8a29e;
    text-transform:uppercase;margin:0 0 0.5rem;">Sutra.AI — Assessment Demo</p>
    <h1 style="font-size:1.75rem;font-weight:600;letter-spacing:-0.03em;color:#1c1917;margin:0 0 0.5rem;">
        AI Assistant Platform
    </h1>
    <p style="font-size:0.875rem;color:#78716c;line-height:1.65;max-width:520px;margin:0;">
        A multi-agent system for document Q&A, structured data analysis, and real-time tool
        calling — with query routing, guardrails, and an automated evaluation suite.
    </p>
</div>

<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;
background:#e7e5e4;border:1px solid #e7e5e4;border-radius:8px;overflow:hidden;margin-bottom:1.5rem;">
    <div style="background:#fff;padding:1.25rem 1.5rem;">
        <p style="font-size:0.62rem;font-weight:600;letter-spacing:0.1em;color:#a8a29e;
        text-transform:uppercase;margin:0 0 0.5rem;">Capability 01</p>
        <p style="font-size:0.875rem;font-weight:600;color:#1c1917;margin:0 0 0.35rem;">Document Q&A</p>
        <p style="font-size:0.78rem;color:#78716c;line-height:1.55;margin:0;">
            RAG pipeline with source citations and retrieval confidence scoring via ChromaDB.
        </p>
    </div>
    <div style="background:#fff;padding:1.25rem 1.5rem;">
        <p style="font-size:0.62rem;font-weight:600;letter-spacing:0.1em;color:#a8a29e;
        text-transform:uppercase;margin:0 0 0.5rem;">Capability 02</p>
        <p style="font-size:0.875rem;font-weight:600;color:#1c1917;margin:0 0 0.35rem;">Data analysis</p>
        <p style="font-size:0.78rem;color:#78716c;line-height:1.55;margin:0;">
            Dynamic pandas agent interprets natural language queries against branch performance data.
        </p>
    </div>
    <div style="background:#fff;padding:1.25rem 1.5rem;">
        <p style="font-size:0.62rem;font-weight:600;letter-spacing:0.1em;color:#a8a29e;
        text-transform:uppercase;margin:0 0 0.5rem;">Capability 03</p>
        <p style="font-size:0.875rem;font-weight:600;color:#1c1917;margin:0 0 0.35rem;">Tool calling</p>
        <p style="font-size:0.78rem;color:#78716c;line-height:1.55;margin:0;">
            Live weather and currency APIs via MCP server, routed by the query classifier.
        </p>
    </div>
</div>

<div style="background:#fff;border:1px solid #e7e5e4;border-radius:8px;padding:1.25rem 1.5rem;">
    <p style="font-size:0.62rem;font-weight:600;letter-spacing:0.1em;color:#a8a29e;
    text-transform:uppercase;margin:0 0 1rem;">System architecture</p>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2rem;">
        <div>
            <p style="font-size:0.78rem;font-weight:600;color:#1c1917;margin:0 0 0.3rem;">Query router</p>
            <p style="font-size:0.75rem;color:#78716c;line-height:1.55;margin:0;">
                Keyword and embedding classifier routes each query to the right agent before any LLM call.
            </p>
        </div>
        <div>
            <p style="font-size:0.78rem;font-weight:600;color:#1c1917;margin:0 0 0.3rem;">Guardrails</p>
            <p style="font-size:0.75rem;color:#78716c;line-height:1.55;margin:0;">
                Prompt injection detection runs before routing on every incoming query.
            </p>
        </div>
        <div>
            <p style="font-size:0.78rem;font-weight:600;color:#1c1917;margin:0 0 0.3rem;">Evaluation suite</p>
            <p style="font-size:0.75rem;color:#78716c;line-height:1.55;margin:0;">
                8-test automated benchmark covering all query types, confidence thresholds, and edge cases.
            </p>
        </div>
    </div>
</div>

<p style="font-size:0.75rem;color:#a8a29e;margin-top:1.25rem;">
    Use the sidebar to navigate to Chat, Analytics, or Evaluation.
</p>
""", unsafe_allow_html=True)
