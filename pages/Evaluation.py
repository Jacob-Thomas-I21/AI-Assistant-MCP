"""pages/Evaluation.py — Eval suite with skeleton loader, progress bar, table hover, category breakdown."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from evaluation.test_suite import run_all_tests, TEST_CASES

st.set_page_config(page_title="Evaluation — AI Platform", page_icon=None, layout="wide")

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
[data-testid="stSidebarNavLink"] { border-radius:6px !important; font-size:0.82rem !important; font-weight:500 !important; color:#44403c !important; }
[data-testid="stSidebarNavLink"]:hover { background:#f5f5f4 !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] { background:#f0fdf4 !important; color:#15803d !important; }
.stButton > button { font-family:'Inter',sans-serif !important; font-size:0.8rem !important; font-weight:500 !important; background:#1c1917 !important; color:#fafaf9 !important; border:none !important; border-radius:6px !important; padding:0.45rem 1rem !important; transition:background 0.15s !important; }
.stButton > button:hover { background:#292524 !important; color:#fafaf9 !important; }
.stButton > button[kind="primary"] { background:#15803d !important; }
.stButton > button[kind="primary"]:hover { background:#166534 !important; }
[data-testid="stExpander"] { border:1px solid #e7e5e4 !important; border-radius:6px !important; background:#ffffff !important; }
[data-testid="stExpander"] summary { font-family:'Inter',sans-serif !important; font-size:0.8rem !important; font-weight:500 !important; color:#44403c !important; }
#MainMenu, footer, header { visibility:hidden !important; }
[data-testid="stToolbar"] { display:none !important; }
.stDeployButton { display:none !important; }
.stAlert { display:none !important; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#d6d3d1; border-radius:4px; }
hr { border:none; border-top:1px solid #e7e5e4 !important; margin:1.5rem 0 !important; }

/* ── Skeleton pulse animation ── */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}
.skeleton-row { animation: pulse 1.4s ease-in-out infinite; }
</style>
"""
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ── HTML helpers ───────────────────────────────────────────────────────────────
def section_label(text):
    return f'<p style="font-size:0.7rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#a8a29e;margin:0 0 0.6rem;">{text}</p>'

def th(text):
    return f'<th style="padding:0.5rem 0.75rem;text-align:left;font-size:0.62rem;font-weight:600;letter-spacing:0.08em;color:#a8a29e;text-transform:uppercase;">{text}</th>'

def cat_pill(text):
    return (f'<span style="font-size:0.62rem;font-weight:600;letter-spacing:0.06em;'
            f'background:#f5f5f4;color:#57534e;padding:2px 6px;border-radius:3px;'
            f'font-family:\'JetBrains Mono\',monospace;">{text}</span>')

def result_pill(passed):
    text = "PASS" if passed else "FAIL"
    bg   = "#f0fdf4" if passed else "#fef2f2"
    fg   = "#15803d" if passed else "#b91c1c"
    return (f'<span style="font-size:0.62rem;font-weight:600;letter-spacing:0.06em;'
            f'background:{bg};color:{fg};padding:2px 7px;border-radius:3px;'
            f'font-family:\'JetBrains Mono\',monospace;">{text}</span>')

def table_wrap(thead_html, tbody_html):
    return f"""
<div style="background:#fff;border:1px solid #e7e5e4;border-radius:8px;
overflow:hidden;margin-bottom:1.5rem;">
    <table style="width:100%;border-collapse:collapse;">
        <thead>
            <tr style="border-bottom:1px solid #e7e5e4;background:#fafaf9;">
                {thead_html}
            </tr>
        </thead>
        <tbody>{tbody_html}</tbody>
    </table>
</div>"""

def tr_hover(content):
    """Table row with JS hover highlight."""
    return (f'<tr style="border-bottom:1px solid #f5f5f4;" '
            f'onmouseover="this.style.background=\'#fafaf9\'" '
            f'onmouseout="this.style.background=\'transparent\'">'
            f'{content}</tr>')

def td(content, style=""):
    base = "padding:0.65rem 0.75rem;font-size:0.8rem;color:#44403c;"
    return f'<td style="{base}{style}">{content}</td>'

def td_mono(content, color="#78716c"):
    return (f'<td style="padding:0.65rem 0.75rem;font-family:\'JetBrains Mono\',monospace;'
            f'font-size:0.68rem;color:{color};">{content}</td>')

# ── Skeleton loader for eval in progress ──────────────────────────────────────
SKELETON_ROWS = ""
for i in range(1, 9):
    SKELETON_ROWS += f"""
<tr style="border-bottom:1px solid #f5f5f4;" class="skeleton-row"
style="animation-delay:{i * 0.07}s">
    <td style="padding:0.65rem 0.75rem;">
        <span style="display:inline-block;width:20px;height:10px;background:#e7e5e4;border-radius:3px;"></span>
    </td>
    <td style="padding:0.65rem 0.75rem;">
        <span style="display:inline-block;width:60px;height:10px;background:#e7e5e4;border-radius:3px;"></span>
    </td>
    <td style="padding:0.65rem 0.75rem;">
        <span style="display:inline-block;width:{140 + (i * 17) % 80}px;height:10px;background:#e7e5e4;border-radius:3px;"></span>
    </td>
    <td style="padding:0.65rem 0.75rem;">
        <span style="display:inline-block;width:50px;height:10px;background:#e7e5e4;border-radius:3px;"></span>
    </td>
    <td style="padding:0.65rem 0.75rem;">
        <span style="display:inline-block;width:50px;height:10px;background:#e7e5e4;border-radius:3px;"></span>
    </td>
    <td style="padding:0.65rem 0.75rem;">
        <span style="display:inline-block;width:36px;height:10px;background:#e7e5e4;border-radius:3px;"></span>
    </td>
</tr>"""

SKELETON_TABLE = table_wrap(
    th("#") + th("Category") + th("Question") + th("Expected") + th("Actual") + th("Result"),
    SKELETON_ROWS
)

# ── Progress bar ───────────────────────────────────────────────────────────────
def progress_bar(passed, total):
    pct = round(passed / total * 100) if total else 0
    bar_color = "#15803d" if pct >= 75 else "#ef4444"
    verdict = "PASS" if pct >= 75 else "FAIL"
    verdict_bg = "#f0fdf4" if pct >= 75 else "#fef2f2"
    verdict_fg = "#15803d" if pct >= 75 else "#b91c1c"
    return f"""
<div style="background:#fff;border:1px solid #e7e5e4;border-radius:8px;
padding:1.25rem 1.5rem;margin-bottom:1.5rem;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
        <div style="display:flex;align-items:baseline;gap:0.5rem;">
            <span style="font-size:1.5rem;font-weight:600;letter-spacing:-0.03em;
            font-family:'JetBrains Mono',monospace;color:#1c1917;">{passed}/{total}</span>
            <span style="font-size:0.78rem;color:#78716c;">tests passed</span>
        </div>
        <span style="font-size:0.65rem;font-weight:600;letter-spacing:0.06em;
        background:{verdict_bg};color:{verdict_fg};padding:3px 9px;border-radius:4px;
        font-family:'JetBrains Mono',monospace;">{verdict} — {pct}%</span>
    </div>
    <div style="background:#f5f5f4;border-radius:999px;height:5px;overflow:hidden;">
        <div style="background:{bar_color};height:100%;width:{pct}%;
        border-radius:999px;transition:width 0.4s ease;"></div>
    </div>
</div>"""

# ── Category breakdown bar ─────────────────────────────────────────────────────
def category_breakdown(results):
    categories = {}
    for r in results:
        cat = r["category"].split(" ")[0]
        if cat not in categories:
            categories[cat] = {"passed": 0, "total": 0}
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1

    items = ""
    for cat, data in categories.items():
        rate = round(data["passed"] / data["total"] * 100)
        bar_color = "#15803d" if rate >= 75 else "#ef4444"
        score_color = "#15803d" if rate >= 75 else "#b91c1c"
        items += f"""
<div style="flex:1;min-width:120px;">
    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:0.4rem;">
        <span style="font-size:0.7rem;font-weight:600;color:#44403c;">{cat}</span>
        <span style="font-size:0.68rem;font-family:'JetBrains Mono',monospace;
        color:{score_color};">{data['passed']}/{data['total']}</span>
    </div>
    <div style="background:#f5f5f4;border-radius:999px;height:4px;overflow:hidden;">
        <div style="background:{bar_color};height:100%;width:{rate}%;border-radius:999px;"></div>
    </div>
</div>"""

    return f"""
<div style="background:#fff;border:1px solid #e7e5e4;border-radius:8px;
padding:1.25rem 1.5rem;margin-bottom:1rem;">
    <p style="font-size:0.62rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;
    color:#a8a29e;margin:0 0 1rem;">By category</p>
    <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">{items}</div>
</div>"""

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:1.75rem 0 1.25rem;border-bottom:1px solid #e7e5e4;margin-bottom:1.5rem;">
    <h1 style="font-size:1.25rem;font-weight:600;letter-spacing:-0.02em;color:#1c1917;margin:0 0 0.25rem;">Evaluation</h1>
    <p style="font-size:0.8rem;color:#78716c;margin:0;">Automated benchmark across all query types and edge cases.</p>
</div>
""", unsafe_allow_html=True)

# ── Test suite preview ─────────────────────────────────────────────────────────
st.markdown(section_label(f"Test suite — {len(TEST_CASES)} cases"), unsafe_allow_html=True)

preview_rows = ""
for c in TEST_CASES:
    preview_rows += tr_hover(
        td_mono(f"{c['id']:02d}", "#a8a29e") +
        td(cat_pill(c["category"])) +
        td(c["question"])
    )
st.markdown(
    table_wrap(th("#") + th("Category") + th("Question"), preview_rows),
    unsafe_allow_html=True
)

st.markdown("---")

# ── Run section ────────────────────────────────────────────────────────────────
st.markdown(section_label("Run evaluation"), unsafe_allow_html=True)
st.markdown('<p style="font-size:0.8rem;color:#78716c;margin:0 0 0.75rem;">Makes 8 LLM calls. Takes approximately 30–60 seconds.</p>', unsafe_allow_html=True)

if "eval_results" not in st.session_state:
    st.session_state.eval_results = None
if "eval_running" not in st.session_state:
    st.session_state.eval_running = False

if st.button("Run all 8 tests", type="primary"):
    st.session_state.eval_running = True
    # Show skeleton while running
    st.markdown(section_label("Results"), unsafe_allow_html=True)
    skel_placeholder = st.empty()
    skel_placeholder.markdown(SKELETON_TABLE, unsafe_allow_html=True)
    try:
        results = run_all_tests()
        st.session_state.eval_results = results
        st.session_state.eval_running = False
    except Exception as e:
        st.session_state.eval_running = False
        st.markdown(
            f'<div style="padding:0.75rem 1rem;background:#fef2f2;border:1px solid #fecaca;'
            f'border-radius:6px;font-size:0.8rem;color:#b91c1c;">Evaluation failed: {e}</div>',
            unsafe_allow_html=True
        )
        st.stop()
    skel_placeholder.empty()
    st.rerun()

# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.eval_results:
    results = st.session_state.eval_results
    passed  = sum(1 for r in results if r["passed"])
    total   = len(results)

    st.markdown("---")

    # Progress bar + verdict
    st.markdown(progress_bar(passed, total), unsafe_allow_html=True)

    # Category breakdown
    st.markdown(category_breakdown(results), unsafe_allow_html=True)

    st.markdown("---")

    # Full results table with hover rows
    st.markdown(section_label("Results"), unsafe_allow_html=True)
    result_rows = ""
    for r in results:
        result_rows += tr_hover(
            td_mono(f"{r['id']:02d}", "#a8a29e") +
            td(cat_pill(r.get("category", ""))) +
            td(r["question"][:68]) +
            td_mono(r.get("expected_type", "")) +
            td_mono(r.get("actual_type", "")) +
            td(result_pill(r["passed"]))
        )
    st.markdown(
        table_wrap(
            th("#") + th("Category") + th("Question") + th("Expected") + th("Actual") + th("Result"),
            result_rows
        ),
        unsafe_allow_html=True
    )

    # Per-test detail expanders
    st.markdown(section_label("Test details"), unsafe_allow_html=True)
    for r in results:
        border_color = "#22c55e" if r["passed"] else "#ef4444"
        label_bg     = "#f0fdf4" if r["passed"] else "#fef2f2"
        label_fg     = "#15803d" if r["passed"] else "#b91c1c"
        label        = "PASS" if r["passed"] else "FAIL"

        with st.expander(f"Test {r['id']:02d} — {r['category']} — {r['question'][:52]}"):
            st.markdown(f"""
<div style="border-left:2px solid {border_color};padding:0 0 0 1rem;margin-bottom:0.75rem;">
    <div style="display:flex;gap:0.5rem;align-items:center;margin-bottom:0.6rem;">
        <span style="font-size:0.62rem;font-weight:600;letter-spacing:0.06em;
        background:{label_bg};color:{label_fg};padding:2px 7px;border-radius:3px;
        font-family:'JetBrains Mono',monospace;">{label}</span>
        <span style="font-size:0.75rem;color:#78716c;font-family:'JetBrains Mono',monospace;">
        classified as <strong style="color:#1c1917;">{r.get('actual_type','N/A')}</strong></span>
    </div>
    <p style="font-size:0.78rem;color:#44403c;line-height:1.6;margin:0 0 0.4rem;">
        <strong style="color:#1c1917;font-weight:600;">Analysis:</strong> {r['analysis']}
    </p>
    <p style="font-size:0.72rem;color:#a8a29e;margin:0;">
        Keywords matched: {', '.join(r.get('keywords_found', [])) or 'none'}
    </p>
</div>
<div style="background:#fafaf9;border:1px solid #e7e5e4;border-radius:6px;
padding:0.75rem 1rem;font-size:0.78rem;color:#44403c;line-height:1.65;">
{r['actual'][:420]}{'...' if len(r['actual']) > 420 else ''}
</div>
""", unsafe_allow_html=True)
