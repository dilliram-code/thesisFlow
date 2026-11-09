"""
Session State Management for ThesisFlow.
Initializes and maintains persistent state across Streamlit reruns and multi-page routing.
"""

from typing import Any, Dict, Optional
import streamlit as st
from database.db import db
from database.models import Paper, Equation
from services.paper_service import paper_service


def init_session_state():
    """Ensures all required session state variables are present."""
    # Ensure demo papers exist if db is fresh
    paper_service.initialize_demo_papers_if_empty()

    if "active_paper_id" not in st.session_state:
        # Default to first paper if available
        papers = db.get_all_papers()
        st.session_state["active_paper_id"] = papers[0].id if papers else None

    if "active_equation_id" not in st.session_state:
        st.session_state["active_equation_id"] = None

    if "gemini_api_key" not in st.session_state:
        st.session_state["gemini_api_key"] = ""

    if "explanation_depth" not in st.session_state:
        st.session_state["explanation_depth"] = "Intermediate"

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"


def get_active_paper() -> Optional[Paper]:
    """Returns currently selected Paper object."""
    paper_id = st.session_state.get("active_paper_id")
    if paper_id:
        return db.get_paper_by_id(paper_id)
    return None


def set_active_paper(paper_id: int):
    """Sets active paper and resets dependent states."""
    st.session_state["active_paper_id"] = paper_id
    st.session_state["active_equation_id"] = None
    st.session_state["chat_messages"] = []


def get_active_equation() -> Optional[Equation]:
    """Returns currently selected Equation object."""
    eq_id = st.session_state.get("active_equation_id")
    if eq_id:
        return db.get_equation_by_id(eq_id)
    return None


def set_active_equation(eq_id: int):
    """Sets currently selected equation for playground or deconstruction."""
    st.session_state["active_equation_id"] = eq_id
