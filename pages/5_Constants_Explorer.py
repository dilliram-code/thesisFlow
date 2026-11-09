"""
Page 5: Scientific Constants Explorer for ThesisFlow.
Authoritative NIST CODATA fundamental physical constants reference with equations and citations.
"""

import streamlit as st
from pathlib import Path
from config import ASSETS_DIR
from utils.file_utils import load_custom_css
from utils.session_utils import init_session_state
from components.sidebar import render_sidebar
from components.header import render_header
from core.scientific_constants import get_all_constants

st.set_page_config(page_title="Scientific Constants | ThesisFlow", page_icon="⚛️", layout="wide")
css = load_custom_css(ASSETS_DIR / "styles.css")
if css:
    st.markdown(css, unsafe_allow_html=True)

init_session_state()
render_sidebar()
render_header()

st.title("⚛️ Fundamental Scientific Constants Explorer")
st.markdown("Reference database of authoritative physical constants from **NIST CODATA (2018/2019 SI Definitions)**.")

# Search and Category Filter
c_col1, c_col2 = st.columns([3, 1])
with c_col1:
    search = st.text_input("🔍 Search constants by name, symbol, or equation:", placeholder="e.g. Planck, c, Boltzmann, G, epsilon...")
with c_col2:
    all_consts = get_all_constants()
    categories = ["All"] + sorted(list(set(c.category for c in all_consts)))
    selected_cat = st.selectbox("Category Filter:", options=categories)

filtered_constants = all_consts
if selected_cat != "All":
    filtered_constants = [c for c in filtered_constants if c.category == selected_cat]

if search:
    q = search.lower()
    filtered_constants = [
        c for c in filtered_constants
        if q in c.name.lower() or q in c.symbol.lower() or q in c.meaning.lower() or q in c.canonical_equation.lower()
    ]

st.markdown(f"**Showing {len(filtered_constants)} physical constants:**")

for const in filtered_constants:
    with st.container():
        st.markdown(f"""
        <div style="background: #141C2E; border: 1px solid #23314A; border-radius: 10px; padding: 20px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span class="thesisflow-badge badge-purple">{const.category}</span>
                    <h3 style="margin: 6px 0 2px 0; color: #F8FAFC; font-size: 1.3rem;">{const.name}</h3>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; color: #00E5FF; margin-bottom: 8px;">
                        Symbol: <b>{const.symbol}</b>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC; font-family: monospace;">
                        {const.value_display} <span style="font-size: 0.9rem; color: #94A3B8;">{const.unit}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #64748B;">Uncertainty: {const.uncertainty}</div>
                </div>
            </div>
            <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.6; margin: 8px 0 12px 0;">{const.meaning}</p>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #1E293B; padding-top: 12px;">
                <div style="font-size: 0.8rem; color: #64748B;">
                    Source: <span style="color: #CBD5E1;">{const.reference}</span> | Dimension: <span style="color: #CBD5E1;">{const.dimension}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Canonical Governing Equations for {const.symbol}", expanded=False):
            st.latex(const.canonical_equation)
