"""
Page 7: Equation Comparison & Model Benchmarking for ThesisFlow.
Compares two or more mathematical formulations side-by-side:
- Mathematical structure and operator differences
- Shared vs. distinct physical variables
- Underlying theoretical assumptions and validity domains
- Derivation linkages (e.g. non-relativistic limits, perturbations)
- Multi-trace comparative Plotly visualizations
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

from config import ASSETS_DIR
from utils.file_utils import load_custom_css
from utils.session_utils import init_session_state, get_active_paper
from components.sidebar import render_sidebar
from components.header import render_header
from database.db import db
from core.mathematical_engine import MathematicalEngine
from core.variable_analyzer import VariableAnalyzer
from services.gemini_service import GeminiService

st.set_page_config(page_title="Equation Comparison | ThesisFlow", page_icon="⚖️", layout="wide")
css = load_custom_css(ASSETS_DIR / "styles.css")
if css:
    st.markdown(css, unsafe_allow_html=True)

init_session_state()
render_sidebar()
render_header()

st.title("⚖️ Mathematical & Physical Equation Comparison")
st.markdown("Benchmark mathematical formulations side-by-side to uncover shared assumptions, parameter scalings, and asymptotic limits.")

active_paper = get_active_paper()
all_equations = db.get_all_equations()

if not all_equations:
    st.warning("No equations available in catalog to compare. Ingest a paper or reload demo papers.")
    st.stop()

# Build selection list
eq_options = {
    eq.id: f"[{eq.eq_id}] {eq.latex[:35]} ({eq.category}) - {eq.section_title}"
    for eq in all_equations
}

c_col1, c_col2 = st.columns(2)
with c_col1:
    st.subheader("Formula A")
    id_a = st.selectbox(
        "Select Primary Equation (A):",
        options=list(eq_options.keys()),
        format_func=lambda x: eq_options[x],
        index=0,
        key="sel_eq_a"
    )

with c_col2:
    st.subheader("Formula B")
    # Default to second equation if available
    default_b_idx = 1 if len(eq_options) > 1 else 0
    id_b = st.selectbox(
        "Select Comparison Equation (B):",
        options=list(eq_options.keys()),
        format_func=lambda x: eq_options[x],
        index=default_b_idx,
        key="sel_eq_b"
    )

eq_a = db.get_equation_by_id(id_a)
eq_b = db.get_equation_by_id(id_b)

if not eq_a or not eq_b:
    st.stop()

st.divider()

# Side-by-side comparison cards
side_a, side_b = st.columns(2)

with side_a:
    st.markdown(f"""
    <div style="background: #141C2E; border: 1px solid #00E5FF; border-radius: 10px; padding: 18px; height: 100%;">
        <div style="display: flex; justify-content: space-between;">
            <span class="thesisflow-badge">{eq_a.eq_id}</span>
            <span class="thesisflow-badge badge-verified">{eq_a.category}</span>
        </div>
        <h3 style="margin: 8px 0; color: #F8FAFC;">{eq_a.section_title}</h3>
        <p style="font-size: 0.8rem; color: #94A3B8;">Page {eq_a.page_number} • Confidence: {int(eq_a.confidence * 100)}%</p>
    </div>
    """, unsafe_allow_html=True)
    st.latex(eq_a.latex)

with side_b:
    st.markdown(f"""
    <div style="background: #141C2E; border: 1px solid #8B5CF6; border-radius: 10px; padding: 18px; height: 100%;">
        <div style="display: flex; justify-content: space-between;">
            <span class="thesisflow-badge badge-purple">{eq_b.eq_id}</span>
            <span class="thesisflow-badge badge-verified">{eq_b.category}</span>
        </div>
        <h3 style="margin: 8px 0; color: #F8FAFC;">{eq_b.section_title}</h3>
        <p style="font-size: 0.8rem; color: #94A3B8;">Page {eq_b.page_number} • Confidence: {int(eq_b.confidence * 100)}%</p>
    </div>
    """, unsafe_allow_html=True)
    st.latex(eq_b.latex)

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 1. Variable Overlap Analysis
st.subheader("🔍 Variable & Symbolic Overlap")
symbols_a = set(v.get("symbol") for v in (eq_a.variables or []))
symbols_b = set(v.get("symbol") for v in (eq_b.variables or []))

shared_symbols = symbols_a.intersection(symbols_b)
unique_a = symbols_a - symbols_b
unique_b = symbols_b - symbols_a

v_col1, v_col2, v_col3 = st.columns(3)
with v_col1:
    st.markdown(f"""
    <div class="stat-card">
        <span class="stat-label">Shared Variables:</span>
        <span class="stat-value" style="color: #10B981; font-size: 1.4rem;">{', '.join(sorted(shared_symbols)) if shared_symbols else 'None'}</span>
        <span style="font-size: 0.75rem; color: #64748B;">Coupled across both formulations</span>
    </div>
    """, unsafe_allow_html=True)

with v_col2:
    st.markdown(f"""
    <div class="stat-card">
        <span class="stat-label">Unique to Formula A:</span>
        <span class="stat-value" style="color: #00E5FF; font-size: 1.4rem;">{', '.join(sorted(unique_a)) if unique_a else 'None'}</span>
        <span style="font-size: 0.75rem; color: #64748B;">Parameters isolated to {eq_a.eq_id}</span>
    </div>
    """, unsafe_allow_html=True)

with v_col3:
    st.markdown(f"""
    <div class="stat-card">
        <span class="stat-label">Unique to Formula B:</span>
        <span class="stat-value" style="color: #8B5CF6; font-size: 1.4rem;">{', '.join(sorted(unique_b)) if unique_b else 'None'}</span>
        <span style="font-size: 0.75rem; color: #64748B;">Parameters isolated to {eq_b.eq_id}</span>
    </div>
    """, unsafe_allow_html=True)

# 2. Comparative Derivation & Physical Relationship
st.divider()
st.subheader("🧠 Mathematical Derivation & Theoretical Linkage")

with st.spinner("Analyzing mathematical compatibility and derivation pathways..."):
    gemini = GeminiService()
    comparison_prompt = f"""You are a computational physicist and mathematician comparing two mathematical expressions from an academic paper.

Formula A [{eq_a.eq_id}]:
$${eq_a.latex}$$
Section: {eq_a.section_title}
Context: {eq_a.context_paragraph}

Formula B [{eq_b.eq_id}]:
$${eq_b.latex}$$
Section: {eq_b.section_title}
Context: {eq_b.context_paragraph}

Compare both formulations:
1. Mathematical Structure & Operators (How their functional forms differ)
2. Underlying Assumptions & Regime of Applicability
3. Derivation Linkage: Can one be derived from the other (e.g., as an asymptotic limit, perturbation, or special case)? Or do they represent distinct models?
4. Physical Consequences: What physical differences arise when using Model A versus Model B?

Be rigorous and objective. If they are independent models, state that clearly without claiming equivalence.
"""
    if gemini.client and gemini.api_key:
        try:
            resp = gemini.client.models.generate_content(
                model=gemini.model,
                contents=comparison_prompt
            )
            analysis_text = resp.text
        except Exception:
            analysis_text = None
    else:
        analysis_text = None

if analysis_text:
    st.markdown(analysis_text)
else:
    # Deterministic local comparison heuristic
    st.markdown(f"""
    #### Heuristic Comparative Analysis
    - **Category Comparison:** Formula A is classified as **{eq_a.category}**, while Formula B is classified as **{eq_b.category}**.
    - **Coupled Parameters:** {"Both equations share state variables (" + ", ".join(shared_symbols) + "), indicating a possible physical coupling or consecutive derivation stage in the paper." if shared_symbols else "The equations use distinct variable sets, suggesting separate conceptual stages or multi-physics modules."}
    - **Dimensionality:** Formula A features {len(symbols_a)} independent degrees of freedom, whereas Formula B incorporates {len(symbols_b)} parameters.
    - **Asymptotic Behavior:** When comparing physical equations across regimes (such as classical mechanics vs. special relativity), examine whether higher-order parameters (e.g. $v/c$ or quantum action $\\hbar$) vanish in the classical limit to reproduce the simpler form.
    """)

# 3. Comparative Overlay Visualization (when possible)
st.divider()
st.subheader("📈 Comparative Numerical Simulation")

parsed_a = MathematicalEngine.safe_parse(eq_a.latex)
parsed_b = MathematicalEngine.safe_parse(eq_b.latex)

if parsed_a is not None and parsed_b is not None and shared_symbols:
    common_x = list(shared_symbols)[0]
    st.info(f"Visualizing both equations across shared coordinate: **{common_x}**")

    plot_col1, plot_col2 = st.columns([1, 2])
    with plot_col1:
        x_min = st.number_input("Sweep Min:", value=0.1)
        x_max = st.number_input("Sweep Max:", value=20.0)
        num_pts = st.slider("Resolution Points:", 50, 500, 200)

        # Fixed parameter dictionaries
        params_a = {s: 1.0 for s in symbols_a if s != common_x}
        params_b = {s: 1.0 for s in symbols_b if s != common_x}
        params_a.update(params_b)

    with plot_col2:
        x_a, y_a, _ = MathematicalEngine.generate_1d_grid(parsed_a, common_x, x_min, x_max, params_a, num_points=num_pts)
        x_b, y_b, _ = MathematicalEngine.generate_1d_grid(parsed_b, common_x, x_min, x_max, params_a, num_points=num_pts)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_a, y=y_a, mode="lines",
            name=f"Formula A: {eq_a.eq_id} ({eq_a.latex[:20]})",
            line=dict(color="#00E5FF", width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=x_b, y=y_b, mode="lines",
            name=f"Formula B: {eq_b.eq_id} ({eq_b.latex[:20]})",
            line=dict(color="#8B5CF6", width=2.5, dash="dash")
        ))
        fig.update_layout(
            title=f"Dual Response: {eq_a.eq_id} vs {eq_b.eq_id} across {common_x}",
            xaxis=dict(title=common_x, gridcolor="#1E293B"),
            yaxis=dict(title="Evaluated Response", gridcolor="#1E293B"),
            template="plotly_dark",
            paper_bgcolor="#0A0E1A",
            plot_bgcolor="#111827",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("ℹ️ Comparative overlay plot is available when both equations share at least one numerical coordinate and are symbolically evaluable.")
