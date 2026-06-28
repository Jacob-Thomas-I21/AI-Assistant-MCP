"""pages/Chat.py — Chat with streaming, empty state, ts badge, score colours, content width."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from agents.router import classify_query
from agents.rag_agent import run_rag_agent
from agents.data_agent import run_data_agent
from agents.tool_agent import run_tool_agent
from guardrails.injection import check_injection, get_injection_response
from feedback.collector import save_feedback

st.set_page_config(page_title="Chat — AI Platform", page_icon=None, layout="wide")

PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    background-color: #f5f5f4 !important;
    color: #1c1917 !important;
}

/* ── Content width constraint ── */
[data-testid="stMainBlockContainer"] {
    max-width: 860px !important;
    margin: 0 auto !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e7e5e4 !important; }
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; color: #57534e !important; font-size: 0.8rem !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {
    color: #1c1917 !important; font-size: 0.85rem !important; font-weight: 600 !important;
}
[data-testid="stSidebarNavLink"] {
    border-radius: 6px !important; font-size: 0.82rem !important;
    font-weight: 500 !important; color: #44403c !important;
    transition: background 0.12s, color 0.12s !important;
}
[data-testid="stSidebarNavLink"]:hover { background: #f5f5f4 !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] { background: #f0fdf4 !important; color: #15803d !important; }

/* ── Main action buttons (e.g. Clear conversation) ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important; font-size: 0.8rem !important;
    font-weight: 500 !important; background: #1c1917 !important; color: #fafaf9 !important;
    border: none !important; border-radius: 6px !important; padding: 0.45rem 1rem !important;
    transition: background 0.12s !important; cursor: pointer !important;
}
.stButton > button:hover { background: #292524 !important; color: #fafaf9 !important; }

/* ── Sidebar example query buttons — white bg, black text ── */
[data-testid="stSidebar"] .stButton > button {
    background: #ffffff !important;
    color: #1c1917 !important;
    border: 1px solid #e7e5e4 !important;
    border-radius: 6px !important;
    font-size: 0.78rem !important;
    font-weight: 400 !important;
    text-align: left !important;
    padding: 0.4rem 0.75rem !important;
    transition: background 0.12s, border-color 0.12s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #f5f5f4 !important;
    color: #1c1917 !important;
    border-color: #d6d3d1 !important;
}

/* ── Chat ── */
[data-testid="stChatInput"] { border: 1px solid #d6d3d1 !important; border-radius: 8px !important; background: #ffffff !important; }
[data-testid="stChatInput"] textarea { font-family: 'Inter', sans-serif !important; font-size: 0.875rem !important; color: #1c1917 !important; }
[data-testid="stChatMessage"] { background: transparent !important; padding: 0.25rem 0 !important; }
[data-testid="stChatMessage"] p { font-family: 'Inter', sans-serif !important; font-size: 0.875rem !important; line-height: 1.7 !important; color: #1c1917 !important; }

/* ── Expander ── */
[data-testid="stExpander"] { border: 1px solid #e7e5e4 !important; border-radius: 6px !important; background: #ffffff !important; }
[data-testid="stExpander"] summary { font-family: 'Inter', sans-serif !important; font-size: 0.8rem !important; font-weight: 500 !important; color: #44403c !important; }

/* ── Chrome ── */
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none !important; }
.stAlert { display: none !important; }
[data-testid="stSpinner"] p { font-family: 'Inter', sans-serif !important; font-size: 0.8rem !important; color: #78716c !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d6d3d1; border-radius: 4px; }
hr { border: none; border-top: 1px solid #e7e5e4 !important; margin: 1.5rem 0 !important; }
</style>
"""
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
TYPE_META = {
    "document": ("DOC",     "#eff6ff", "#1d4ed8"),
    "data":     ("DATA",    "#f0fdf4", "#15803d"),
    "tool":     ("TOOL",    "#fff7ed", "#c2410c"),
    "blocked":  ("BLOCKED", "#fef2f2", "#b91c1c"),
    "unknown":  ("?",       "#fafaf9", "#78716c"),
}
CONF_META = {
    "high":   ("#f0fdf4", "#15803d"),
    "medium": ("#fefce8", "#a16207"),
    "low":    ("#fef2f2", "#b91c1c"),
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def score_color(score):
    if score >= 0.7: return "#15803d"
    if score >= 0.5: return "#a16207"
    return "#b91c1c"

def type_badge(qt):
    label, bg, fg = TYPE_META.get(qt, ("?", "#fafaf9", "#78716c"))
    return (f'<span style="display:inline-block;padding:2px 7px;border-radius:4px;'
            f'font-size:0.65rem;font-weight:600;letter-spacing:0.06em;'
            f'background:{bg};color:{fg};font-family:\'JetBrains Mono\',monospace;">{label}</span>')

def conf_badge(label, score):
    if not label or label in ("no_docs", ""):
        return ""
    bg, fg = CONF_META.get(label, ("#fafaf9", "#78716c"))
    return (f'<span style="display:inline-block;padding:2px 7px;border-radius:4px;'
            f'font-size:0.65rem;font-weight:500;letter-spacing:0.04em;'
            f'background:{bg};color:{fg};margin-left:6px;">confidence {score:.0%}</span>')

def ts_badge():
    """Monospace timestamp — logged system feel."""
    ts = datetime.now().strftime("%H:%M:%S")
    return (f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;'
            f'color:#a8a29e;margin-left:8px;">{ts}</span>')

def render_meta(result):
    """Render badges + expandable panels under a response."""
    badges = type_badge(result["query_type"])
    if result.get("confidence_label"):
        badges += conf_badge(result["confidence_label"], result["confidence"])
    badges += ts_badge()
    st.markdown(badges, unsafe_allow_html=True)

    # Sources — score colour-coded
    if result.get("sources"):
        with st.expander(f"Sources ({len(result['sources'])})"):
            for src in result["sources"]:
                sc = score_color(src["score"])
                st.markdown(f"""
<div style="padding:0.55rem 0.875rem;border-left:2px solid #e7e5e4;margin-bottom:0.5rem;
font-size:0.78rem;" onmouseover="this.style.background='#fafaf9'"
onmouseout="this.style.background='transparent'">
    <span style="font-weight:600;color:#1c1917;">{src['file']}</span>
    <span style="color:#78716c;"> — {src['section']}</span>
    <span style="float:right;font-family:'JetBrains Mono',monospace;
    font-size:0.68rem;color:{sc};">score {src['score']:.2f}</span>
</div>""", unsafe_allow_html=True)

    # Tool output — monospace panel
    if result.get("tool_output"):
        with st.expander(f"Tool — {result['tool_name']}"):
            st.markdown(f"""
<div style="background:#fafaf9;border:1px solid #e7e5e4;border-radius:6px;padding:0.75rem 1rem;
font-size:0.78rem;font-family:'JetBrains Mono',monospace;line-height:1.7;">
<span style="color:#a8a29e;">input</span><br>
<span style="color:#1c1917;">{result['tool_input']}</span><br><br>
<span style="color:#a8a29e;">output</span><br>
<span style="color:#1c1917;">{result['tool_output']}</span>
</div>""", unsafe_allow_html=True)

    # Generated code
    if result.get("code"):
        with st.expander("Generated pandas code"):
            st.code(result["code"], language="python")

def stream_text(text):
    """Word-by-word generator for st.write_stream — typewriter effect."""
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(0.018)

def process_query(query):
    is_injection, _ = check_injection(query)
    if is_injection:
        return {"response": get_injection_response(), "query_type": "blocked",
                "confidence": 0.0, "confidence_label": "", "sources": [],
                "tool_name": None, "tool_input": None, "tool_output": None, "code": None}
    qt = classify_query(query)
    if qt == "document":
        r = run_rag_agent(query)
        return {"response": r["response"], "query_type": "document",
                "confidence": r["confidence"], "confidence_label": r["confidence_label"],
                "sources": r["sources"], "tool_name": None, "tool_input": None,
                "tool_output": None, "code": None}
    elif qt == "data":
        r = run_data_agent(query)
        return {"response": r["response"], "query_type": "data",
                "confidence": 1.0, "confidence_label": "high", "sources": [],
                "tool_name": None, "tool_input": None, "tool_output": None, "code": r.get("code")}
    elif qt == "tool":
        r = run_tool_agent(query)
        return {"response": r["response"], "query_type": "tool",
                "confidence": 1.0, "confidence_label": "high", "sources": [],
                "tool_name": r.get("tool_name"), "tool_input": r.get("tool_input"),
                "tool_output": r.get("tool_output"), "code": None}
    return {"response": "That query type isn't supported. Try asking about company policies, branch data, or weather and currency.",
            "query_type": "unknown", "confidence": 0.0, "confidence_label": "",
            "sources": [], "tool_name": None, "tool_input": None, "tool_output": None, "code": None}

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_feedback" not in st.session_state:
    st.session_state.pending_feedback = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Example queries")
    st.markdown("**Document**")
    for ex in ["What is the leave approval process?",
                "Who approves procurement above $10,000?",
                "Escalation path for delayed shipments?"]:
        if st.button(ex, key=f"ex_{ex[:18]}", use_container_width=True):
            st.session_state["prefill"] = ex
    st.markdown("**Data**")
    for ex in ["Which branch has the highest revenue?",
                "Show top 3 branches by orders"]:
        if st.button(ex, key=f"ex_{ex[:18]}", use_container_width=True):
            st.session_state["prefill"] = ex
    st.markdown("**Tools**")
    for ex in ["What is the weather in Mumbai?", "Convert 100 USD to INR"]:
        if st.button(ex, key=f"ex_{ex[:18]}", use_container_width=True):
            st.session_state["prefill"] = ex
    st.markdown("---")
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_feedback = None
        st.rerun()

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:1.75rem 0 1.25rem;border-bottom:1px solid #e7e5e4;margin-bottom:1.5rem;">
    <h1 style="font-size:1.25rem;font-weight:600;letter-spacing:-0.02em;color:#1c1917;margin-bottom:0.25rem;">Chat</h1>
    <p style="font-size:0.8rem;color:#78716c;">Ask about company policies, branch data, or use real-time tools.</p>
</div>
""", unsafe_allow_html=True)

# ── Empty state ────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
<div style="border:1px dashed #d6d3d1;border-radius:8px;padding:2.5rem 2rem;
text-align:center;margin:2rem 0;">
    <p style="font-size:0.875rem;font-weight:500;color:#44403c;margin:0 0 0.35rem;">
        No messages yet
    </p>
    <p style="font-size:0.8rem;color:#a8a29e;margin:0;">
        Use the example queries in the sidebar or type a question below.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Chat history ───────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "meta" in msg:
            render_meta(msg["meta"])

# ── Feedback row ───────────────────────────────────────────────────────────────
if st.session_state.pending_feedback:
    pf = st.session_state.pending_feedback
    st.markdown("""
<p style="font-size:0.75rem;color:#a8a29e;margin:0.5rem 0 0.4rem;
border-top:1px solid #e7e5e4;padding-top:0.75rem;">Was this response helpful?</p>
""", unsafe_allow_html=True)
    c1, c2, _ = st.columns([1, 1, 8])
    with c1:
        if st.button("Helpful", key="fb_y"):
            save_feedback(pf["query"], pf["response"], pf["query_type"], pf["confidence"], "helpful")
            st.session_state.pending_feedback = None
            st.rerun()
    with c2:
        if st.button("Not helpful", key="fb_n"):
            save_feedback(pf["query"], pf["response"], pf["query_type"], pf["confidence"], "not_helpful")
            st.session_state.pending_feedback = None
            st.rerun()

# ── Input ──────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
query = st.chat_input("Ask about policies, branch data, or tools...") or prefill

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = process_query(query)
        # ── Streaming typewriter response ──
        st.write_stream(stream_text(result["response"]))
        render_meta(result)

    st.session_state.messages.append({
        "role": "assistant", "content": result["response"], "meta": result
    })
    st.session_state.pending_feedback = {
        "query": query, "response": result["response"],
        "query_type": result["query_type"], "confidence": result["confidence"]
    }
    st.rerun()
