"""
Page 4: AI Research Assistant for ThesisFlow.
RAG-powered conversational scientist grounded strictly in the uploaded research paper.
Provides page citations, equation cross-references, and multi-tier comprehension levels.
"""

import streamlit as st
from pathlib import Path
from config import ASSETS_DIR
from utils.file_utils import load_custom_css
from utils.session_utils import init_session_state, get_active_paper
from components.sidebar import render_sidebar
from components.header import render_header
from services.gemini_service import GeminiService
from services.rag_service import rag_service
from database.db import db

st.set_page_config(page_title="AI Research Assistant | ThesisFlow", page_icon="🤖", layout="wide")
css = load_custom_css(ASSETS_DIR / "styles.css")
if css:
    st.markdown(css, unsafe_allow_html=True)

init_session_state()
render_sidebar()
render_header()

active_paper = get_active_paper()

if not active_paper:
    st.warning("Please select or upload a research paper from the Research Library to activate the AI Research Assistant.")
    st.stop()

st.title("🤖 Grounded AI Research Assistant")
st.markdown(f"Conversational academic reasoning grounded strictly in **'{active_paper.title}'**.")

# Quick Prompt Suggestions Bar
st.markdown("##### 💡 Suggested Scientific Questions:")
suggested_cols = st.columns(4)
prompts = [
    "Explain Equation 1 in detail and state its physical meaning.",
    "What are the core mathematical assumptions of this model?",
    "How do the variables scale if the primary parameter is doubled?",
    "What are the physical limitations and invalid regimes of this theory?"
]

selected_prompt = None
for i, col in enumerate(suggested_cols):
    with col:
        if st.button(prompts[i], key=f"sug_btn_{i}"):
            selected_prompt = prompts[i]

# Chat History Container
chat_history = st.session_state.get("chat_messages", [])

# Display existing messages
for msg in chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input Box
user_query = st.chat_input("Ask any question regarding the paper, its derivations, variables, or equations...")
if selected_prompt:
    user_query = selected_prompt

if user_query:
    # 1. Add user query to chat
    chat_history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Retrieve relevant chunks using RAG
    with st.spinner("Retrieving relevant passages, equations, and section context..."):
        relevant_chunks = rag_service.retrieve(active_paper.id, user_query, top_k=4)

        # 3. Call Gemini with strict grounding
        depth = st.session_state.get("explanation_depth", "Intermediate")
        gemini = GeminiService()
        response_text = gemini.generate_chat_response(
            query=user_query,
            context_chunks=relevant_chunks,
            paper_title=active_paper.title,
            conversation_history=chat_history,
            depth_level=depth
        )

    # 4. Display response
    with st.chat_message("assistant"):
        st.markdown(response_text)

        # Show grounded sources expander
        if relevant_chunks:
            with st.expander("📚 Verified Grounded Sources & Citations", expanded=False):
                for idx, c in enumerate(relevant_chunks, start=1):
                    eqs_tag = f" | Equations: {', '.join(c.get('associated_equations', []))}" if c.get("associated_equations") else ""
                    st.markdown(f"**Source {idx}:** Page {c.get('page', '?')} • *{c.get('section', 'General')}*{eqs_tag}")
                    st.caption(f"\"{c.get('text', '')[:250]}...\"")

    # Save to session
    chat_history.append({"role": "assistant", "content": response_text})
    st.session_state["chat_messages"] = chat_history
