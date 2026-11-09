"""
Page 1: Research Library for ThesisFlow.
Manage, search, inspect, and delete uploaded research papers.
"""

import streamlit as st
from pathlib import Path
from config import ASSETS_DIR
from utils.file_utils import load_custom_css
from utils.session_utils import init_session_state, get_active_paper, set_active_paper
from components.sidebar import render_sidebar
from components.header import render_header
from database.db import db
from services.paper_service import paper_service

st.set_page_config(page_title="Research Library | ThesisFlow", page_icon="📚", layout="wide")
css = load_custom_css(ASSETS_DIR / "styles.css")
if css:
    st.markdown(css, unsafe_allow_html=True)

init_session_state()
render_sidebar()
render_header()

st.title("📚 Academic Research Library")
st.markdown("Organize, review, and search all ingested scientific preprints and dissertations.")

# Search and Filter Toolbar
s_col1, s_col2, s_col3 = st.columns([3, 1, 1])
with s_col1:
    search_query = st.text_input("🔍 Search papers by title, author, or keyword:", placeholder="e.g. Relativity, Harmonic, Schrödinger...")
with s_col2:
    sort_by = st.selectbox("Sort by:", ["Newest First", "Title A-Z", "Most Equations"])
with s_col3:
    st.write("")
    st.write("")
    if st.button("🔄 Reset Demo Papers", help="Re-initializes classical physics demo papers"):
        paper_service.initialize_demo_papers_if_empty()
        st.success("Demo papers refreshed.")
        st.rerun()

papers = db.get_all_papers()

# Filter
if search_query:
    q = search_query.lower()
    papers = [p for p in papers if q in p.title.lower() or q in p.authors.lower() or q in p.abstract.lower()]

# Sort
if sort_by == "Title A-Z":
    papers.sort(key=lambda p: p.title.lower())
elif sort_by == "Most Equations":
    papers.sort(key=lambda p: p.equations_count, reverse=True)

active_paper = get_active_paper()

if not papers:
    st.warning("No papers match your search criteria.")
else:
    st.markdown(f"**Showing {len(papers)} research document(s):**")
    for paper in papers:
        is_active = (active_paper and active_paper.id == paper.id)
        border_color = "#00E5FF" if is_active else "#23314A"

        with st.container():
            st.markdown(f"""
            <div style="background: #141C2E; border: 1px solid {border_color}; border-radius: 10px; padding: 18px; margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h3 style="margin: 0 0 6px 0; color: #F8FAFC; font-size: 1.25rem;">{paper.title}</h3>
                        <p style="margin: 0 0 8px 0; color: #00E5FF; font-size: 0.9rem;">Authors: {paper.authors}</p>
                    </div>
                    <div>
                        {'<span class="thesisflow-badge badge-verified">ACTIVE SELECTION</span>' if is_active else ''}
                    </div>
                </div>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.5; margin-bottom: 12px;">{paper.abstract[:300]}...</p>
                <div style="display: flex; gap: 16px; font-size: 0.8rem; color: #64748B;">
                    <span>📄 <b>{paper.total_pages}</b> Pages</span>
                    <span>∑ <b>{paper.equations_count}</b> Equations Detected</span>
                    <span>📅 Ingested: {paper.uploaded_at[:10]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            b_col1, b_col2, b_col3, b_col4 = st.columns([1.5, 1.5, 1.5, 4])
            with b_col1:
                if not is_active:
                    if st.button("🎯 Set as Active", key=f"set_act_{paper.id}"):
                        set_active_paper(paper.id)
                        st.rerun()
                else:
                    st.button("✓ Currently Active", disabled=True, key=f"act_dis_{paper.id}")

            with b_col2:
                if st.button("📖 Read in Explorer", key=f"exp_{paper.id}"):
                    set_active_paper(paper.id)
                    st.switch_page("pages/2_Paper_Explorer.py")

            with b_col3:
                if st.button("🗑️ Delete", key=f"del_{paper.id}"):
                    db.delete_paper(paper.id)
                    st.success(f"Deleted '{paper.title}'")
                    st.rerun()

