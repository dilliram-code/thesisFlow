"""
ThesisFlow: The Interactive Math & Physics Research Paper Deconstructer.
Main entry point and scientific dashboard.
"""

import streamlit as st
from pathlib import Path
import os

# Configure Streamlit page layout
st.set_page_config(
    page_title="ThesisFlow | Research Paper Deconstructer",
    page_icon="Ψ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
from config import ASSETS_DIR
from utils.file_utils import load_custom_css
css_content = load_custom_css(ASSETS_DIR / "styles.css")
if css_content:
    st.markdown(css_content, unsafe_allow_html=True)

# Initialize Session and Services
from utils.session_utils import init_session_state, get_active_paper, set_active_paper, set_active_equation
from components.header import render_header
from components.sidebar import render_sidebar
from components.equation_card import render_equation_card
from database.db import db
from services.paper_service import paper_service

init_session_state()
render_sidebar()
render_header()

# Dashboard Content
active_paper = get_active_paper()
all_papers = db.get_all_papers()
all_equations = db.get_all_equations()
all_experiments = db.get_experiments()

# 1. Metric Stat Cards Row
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.markdown(f"""
    <div class="stat-card">
        <span class="stat-value">{len(all_papers)}</span>
        <span class="stat-label">Indexed Papers</span>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class="stat-card">
        <span class="stat-value" style="color: #00E5FF;">{len(all_equations)}</span>
        <span class="stat-label">Cataloged Equations</span>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
    <div class="stat-card">
        <span class="stat-value" style="color: #10B981;">{len(all_experiments)}</span>
        <span class="stat-label">Saved Experiments</span>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    st.markdown("""
    <div class="stat-card">
        <span class="stat-value" style="color: #8B5CF6;">15+</span>
        <span class="stat-label">NIST Constants</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# 2. Main Ingestion & Upload Section
st.subheader("📤 Ingest & Deconstruct Scientific PDF")
with st.container():
    uploaded_file = st.file_uploader(
        "Drop a research paper PDF here to automatically extract equations, variables, and physics models:",
        type=["pdf"],
        help="Supports academic preprints, conference papers, and thesis manuscripts up to 35 MB."
    )

    if uploaded_file is not None:
        if st.button("🚀 Process Research Paper", type="primary"):
            with st.status("Analyzing document structure & mathematical equations...", expanded=True) as status:
                st.write("1. Validating PDF integrity and byte structure...")
                file_bytes = uploaded_file.read()
                try:
                    st.write("2. Extracting textual sections, headers, and page blocks...")
                    st.write("3. Detecting mathematical expressions, operators, and LaTeX syntax...")
                    paper, equations, msg = paper_service.process_uploaded_pdf(file_bytes, uploaded_file.name)
                    st.write("4. Indexing semantic chunks for RAG conversational reasoning...")
                    set_active_paper(paper.id)
                    status.update(label=f"Successfully processed! Extracted {len(equations)} equations.", state="complete", expanded=False)
                    st.success(f"Paper '{paper.title}' is now ready for exploration.")
                    st.rerun()
                except Exception as e:
                    status.update(label="Document processing encountered an issue.", state="error")
                    st.error(f"Error processing PDF: {str(e)}")

st.divider()

# 3. Active Paper Quick Overview & Extracted Equations
if active_paper:
    st.subheader(f"🔬 Equations in Current Paper: {active_paper.title}")
    paper_eqs = db.get_equations_by_paper(active_paper.id)

    if paper_eqs:
        # Category Filter Bar
        categories = ["All"] + sorted(list(set(e.category for e in paper_eqs)))
        filter_col1, filter_col2 = st.columns([2, 2])
        with filter_col1:
            selected_cat = st.selectbox("Filter by Mathematical Domain:", options=categories)
        with filter_col2:
            st.caption(f"Showing {len(paper_eqs)} detected mathematical expressions across {active_paper.total_pages} pages.")

        filtered = paper_eqs if selected_cat == "All" else [e for e in paper_eqs if e.category == selected_cat]

        # Display first 5 equations with pagination or cards
        for eq in filtered[:6]:
            render_equation_card(eq, paper_title=active_paper.title, allow_playground=True)

        if len(filtered) > 6:
            st.info(f"Showing 6 of {len(filtered)} equations. Explore the complete collection in the **Paper Explorer** or **Equation Playground**.")
    else:
        st.info("No mathematical equations identified in this paper yet.")
else:
    # Quick Start Demo Cards
    st.subheader("💡 Or Start with a Pre-Indexed Academic Classic")
    d_col1, d_col2, d_col3 = st.columns(3)

    with d_col1:
        st.markdown("""
        <div class="stat-card" style="height: 100%;">
            <span class="thesisflow-badge" style="width: fit-content;">Special Relativity</span>
            <h4 style="margin: 8px 0; color: #F8FAFC;">Einstein's Electrodynamics</h4>
            <p style="font-size: 0.85rem; color: #94A3B8;">Deconstruct $E = mc^2$, the Lorentz factor $\\gamma$, and relativistic momentum.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore Relativity", key="btn_relativity"):
            p = next((p for p in all_papers if "relativity" in p.filename.lower()), None)
            if p:
                set_active_paper(p.id)
                st.rerun()

    with d_col2:
        st.markdown("""
        <div class="stat-card" style="height: 100%;">
            <span class="thesisflow-badge" style="width: fit-content;">Classical Mechanics</span>
            <h4 style="margin: 8px 0; color: #F8FAFC;">Harmonic Oscillators</h4>
            <p style="font-size: 0.85rem; color: #94A3B8;">Simulate $F=ma$, $x(t)=A\\cos(\\omega t + \\phi)$, and phase space orbits.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore Dynamics", key="btn_dynamics"):
            p = next((p for p in all_papers if "oscillations" in p.filename.lower()), None)
            if p:
                set_active_paper(p.id)
                st.rerun()

    with d_col3:
        st.markdown("""
        <div class="stat-card" style="height: 100%;">
            <span class="thesisflow-badge" style="width: fit-content;">Statistical & Quantum</span>
            <h4 style="margin: 8px 0; color: #F8FAFC;">Probability & Wave Mechanics</h4>
            <p style="font-size: 0.85rem; color: #94A3B8;">Analyze Gaussian density distributions and the time-dependent Schrödinger equation.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore Quantum", key="btn_quantum"):
            p = next((p for p in all_papers if "quantum" in p.filename.lower()), None)
            if p:
                set_active_paper(p.id)
                st.rerun()

