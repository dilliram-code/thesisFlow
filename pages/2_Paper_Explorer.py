"""
Page 2: Paper Explorer for ThesisFlow.
Split-screen academic reading interface:
- Left Panel: Document page navigation, section headers, and full-text context
- Right Panel: Instant mathematical deconstructions, variable tables, and equations active on this page
"""

import streamlit as st
from pathlib import Path
from config import ASSETS_DIR
from utils.file_utils import load_custom_css
from utils.session_utils import init_session_state, get_active_paper, set_active_equation
from components.sidebar import render_sidebar
from components.header import render_header
from components.equation_card import render_equation_card
from database.db import db
from core.pdf_parser import PDFParser

st.set_page_config(page_title="Paper Explorer | ThesisFlow", page_icon="📖", layout="wide")
css = load_custom_css(ASSETS_DIR / "styles.css")
if css:
    st.markdown(css, unsafe_allow_html=True)

init_session_state()
render_sidebar()
render_header()

active_paper = get_active_paper()

if not active_paper:
    st.warning("Please select or upload a research paper first from the Research Library.")
    st.stop()

st.title("📖 Split-Screen Research Paper Explorer")

# Fetch all equations for this paper
paper_eqs = db.get_equations_by_paper(active_paper.id)

# Page Navigator Control
nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
with nav_col1:
    current_page = st.number_input("Page:", min_value=1, max_value=max(active_paper.total_pages, 1), value=1)
with nav_col2:
    st.markdown(f"<div style='margin-top: 10px; color: #94A3B8;'>Navigating {active_paper.total_pages} total pages in <b>{active_paper.title}</b></div>", unsafe_allow_html=True)
with nav_col3:
    eqs_on_page = [e for e in paper_eqs if e.page_number == current_page]
    st.markdown(f"<div style='margin-top: 10px; text-align: right;'><span class='thesisflow-badge'>{len(eqs_on_page)} Equations on Page {current_page}</span></div>", unsafe_allow_html=True)

st.divider()

# Split-screen columns
left_col, right_col = st.columns([1, 1], gap="large")

# LEFT PANEL: Document Page Content
with left_col:
    st.markdown(f"### 📄 Document Page {current_page}")

    # Extract or display cached page text
    pdf_file = Path(active_paper.filepath)
    page_text = ""
    if pdf_file.exists():
        try:
            import pymupdf
            doc = pymupdf.open(str(pdf_file))
            if current_page <= len(doc):
                page_text = doc[current_page - 1].get_text("text") or ""
            doc.close()
        except Exception:
            pass

    if not page_text:
        # Fallback to abstract / description
        page_text = f"Section text for page {current_page} of {active_paper.title}.\n\nAbstract:\n{active_paper.abstract}"

    # Search within current page
    filter_word = st.text_input("🔍 Search within this page:", placeholder="Type a term to highlight...")
    if filter_word:
        highlighted = page_text.replace(filter_word, f"**_{filter_word.upper()}_**")
        st.markdown(f"""
        <div style="background: #0B1120; border: 1px solid #1E293B; border-radius: 8px; padding: 20px; font-size: 0.95rem; line-height: 1.7; color: #CBD5E1; height: 600px; overflow-y: auto; white-space: pre-wrap;">
{highlighted}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #0B1120; border: 1px solid #1E293B; border-radius: 8px; padding: 20px; font-size: 0.95rem; line-height: 1.7; color: #CBD5E1; height: 600px; overflow-y: auto; white-space: pre-wrap;">
{page_text}
        </div>
        """, unsafe_allow_html=True)

# RIGHT PANEL: Mathematical Deconstruction
with right_col:
    st.markdown(f"### 🔬 Mathematical Formulations on Page {current_page}")

    if eqs_on_page:
        for eq in eqs_on_page:
            render_equation_card(eq, paper_title=active_paper.title, allow_playground=True)
    else:
        st.info(f"No specific equations cataloged for Page {current_page}.")
        # Show all equations in the paper as a quick reference
        if paper_eqs:
            st.markdown("#### Other Equations in this Paper:")
            for eq in paper_eqs[:3]:
                render_equation_card(eq, paper_title=active_paper.title, allow_playground=True)

