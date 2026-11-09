"""
Header component for ThesisFlow.
Displays branding, active paper status, API connection indicator, and explanation depth toggle.
"""

import streamlit as st
from config import APP_NAME, APP_SUBTITLE
from utils.session_utils import get_active_paper
from services.gemini_service import GeminiService


def render_header():
    """Renders the top branding and status banner."""
    active_paper = get_active_paper()
    gemini = GeminiService()
    status = gemini.is_connected()

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
            <div style="width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #00E5FF, #8B5CF6); display: flex; align-items: center; justify-content: center; font-weight: 800; color: #0A0E1A; font-size: 1.2rem;">Ψ</div>
            <h1 style="margin: 0; font-size: 2.0rem; font-weight: 700; color: #F8FAFC; letter-spacing: -0.02em;">{APP_NAME}</h1>
            <span class="thesisflow-badge">Academic v1.0</span>
        </div>
        <p style="margin: 0 0 12px 0; color: #94A3B8; font-size: 0.95rem;">{APP_SUBTITLE}</p>
        """, unsafe_allow_html=True)

    with col2:
        # Status pill
        if status["connected"]:
            st.markdown(f"""
            <div style="text-align: right; margin-top: 6px;">
                <span class="thesisflow-badge badge-verified">● Gemini Online ({status.get('latency_ms', 0)}ms)</span>
                <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">Model: {status.get('model', 'gemini-3.8-flash')}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: right; margin-top: 6px;">
                <span class="thesisflow-badge badge-warning">○ Local / Offline Mode</span>
                <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">SymPy & Classical Physics Engine Active</div>
            </div>
            """, unsafe_allow_html=True)

    # Active paper breadcrumb bar
    if active_paper:
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #243248; border-radius: 8px; padding: 10px 16px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="font-size: 0.75rem; color: #00E5FF; font-weight: 600; text-transform: uppercase;">Active Paper:</span>
                <span style="font-size: 0.9rem; color: #F8FAFC; font-weight: 500; margin-left: 8px;">{active_paper.title}</span>
                <span style="font-size: 0.8rem; color: #94A3B8; margin-left: 8px;">— {active_paper.authors} ({active_paper.total_pages} pages, {active_paper.equations_count} equations)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ No paper active. Please select or upload a research paper from the Research Library or Dashboard.")
