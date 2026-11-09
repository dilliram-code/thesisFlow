"""
Sidebar component for ThesisFlow.
Provides project selector, paper switching, API settings, and navigation metrics.
"""

import streamlit as st
import os
from config import APP_NAME
from database.db import db
from utils.session_utils import set_active_paper, get_active_paper
from services.gemini_service import GeminiService


def render_sidebar():
    """Renders the comprehensive sidebar navigation and settings panel."""
    with st.sidebar:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <div style="width: 28px; height: 28px; border-radius: 6px; background: linear-gradient(135deg, #00E5FF, #8B5CF6); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #0A0E1A;">Ψ</div>
            <span style="font-size: 1.3rem; font-weight: 700; color: #F8FAFC;">{APP_NAME}</span>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📚 Active Paper")
        papers = db.get_all_papers()
        active_paper = get_active_paper()

        if papers:
            paper_options = {p.id: f"{p.title[:38]}..." if len(p.title) > 38 else p.title for p in papers}
            current_idx = list(paper_options.keys()).index(active_paper.id) if active_paper and active_paper.id in paper_options else 0

            selected_id = st.selectbox(
                "Select Paper to Analyze:",
                options=list(paper_options.keys()),
                format_func=lambda x: paper_options[x],
                index=current_idx,
                label_visibility="collapsed"
            )

            if selected_id and (not active_paper or selected_id != active_paper.id):
                set_active_paper(selected_id)
                st.rerun()
        else:
            st.caption("No papers loaded yet.")

        st.divider()

        # Explanation depth control
        st.subheader("🎯 Explanation Depth")
        depth = st.select_slider(
            "Select comprehension level:",
            options=["Beginner", "Intermediate", "Advanced Mathematical", "Research-level"],
            value=st.session_state.get("explanation_depth", "Intermediate"),
            help="Adapts AI reasoning, analogy choice, and mathematical rigor across all modules."
        )
        st.session_state["explanation_depth"] = depth

        st.divider()

        # AI Configuration Accordion
        with st.expander("⚙️ AI & API Settings", expanded=False):
            current_key = os.getenv("GEMINI_API_KEY", "") or st.session_state.get("gemini_api_key", "")
            input_key = st.text_input(
                "Google Gemini API Key",
                type="password",
                value=current_key,
                help="Set GEMINI_API_KEY for deep equation reasoning, conversational RAG, and paper deconstruction."
            )
            if input_key != current_key:
                os.environ["GEMINI_API_KEY"] = input_key
                st.session_state["gemini_api_key"] = input_key
                st.success("API Key updated.")
                st.rerun()

            gemini = GeminiService()
            conn = gemini.is_connected()
            if conn["connected"]:
                st.markdown(f"🟢 **Status:** Connected ({conn.get('latency_ms', 0)} ms)")
            else:
                st.markdown(f"🟠 **Status:** {conn.get('reason', 'Disconnected')}")

        st.divider()

        # Workspace Statistics
        total_papers = len(papers)
        total_equations = len(db.get_all_equations())
        total_experiments = len(db.get_experiments())

        st.markdown(f"""
        <div style="font-size: 0.8rem; color: #94A3B8;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>Papers Indexed:</span>
                <b style="color: #F8FAFC;">{total_papers}</b>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>Equations Cataloged:</span>
                <b style="color: #00E5FF;">{total_equations}</b>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>Saved Experiments:</span>
                <b style="color: #10B981;">{total_experiments}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
