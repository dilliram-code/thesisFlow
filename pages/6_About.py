"""
Page 6: About & Architecture Guide for ThesisFlow.
"""

import streamlit as st
from pathlib import Path
from config import ASSETS_DIR, APP_NAME, APP_VERSION
from utils.file_utils import load_custom_css
from utils.session_utils import init_session_state
from components.sidebar import render_sidebar
from components.header import render_header

st.set_page_config(page_title="About & Guide | ThesisFlow", page_icon="ℹ️", layout="wide")
css = load_custom_css(ASSETS_DIR / "styles.css")
if css:
    st.markdown(css, unsafe_allow_html=True)

init_session_state()
render_sidebar()
render_header()

st.title(f"ℹ️ About {APP_NAME} (v{APP_VERSION})")
st.markdown("""
### Transforming Static Equations into Interactive Scientific Laboratories

ThesisFlow is an AI-powered academic research companion that bridges the gap between static LaTeX notation in scientific preprints and interactive computational experiments.
""")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("""
    #### 🚀 Core Capabilities
    - **PDF Structural Parser:** Ingests research papers and extracts headings, page contexts, and mathematical expressions using `pymupdf` and `pdfplumber`.
    - **SymPy Symbolic Validation:** Sanitizes, validates, and evaluates mathematical formulas with restricted AST transformations (zero arbitrary code execution).
    - **Deep AI Deconstruction:** Deconstructs equations across 8 dimensions: plain-language meaning, mathematical form, variable table, physical intuition, derivation steps, cross-disciplinary applications, and theoretical validity boundaries.
    - **Interactive Equation Playground:** Real-time Plotly visualizations with dynamic sliders, numerical operating points, and sensitivity sweeps.
    - **Grounded Conversational RAG:** Chat with your paper through BM25 chunk retrieval and Google Gemini reasoning with mandatory page and equation citations.
    - **Authoritative Physical Constants:** Direct cross-referencing against NIST CODATA standard values.
    - **Multi-Flavor Python Code Generation:** Exports verified Pure Python, NumPy vectorized code, SymPy scripts, and Plotly graphics.
    """)

with col2:
    st.markdown("""
    #### 🛠️ Technology Stack
    - **Frontend / UI:** Streamlit, Custom Dark CSS, KaTeX / MathJax, Plotly Express & Graph Objects.
    - **Symbolic & Numerical Math:** SymPy 1.14, NumPy 1.26, SciPy 1.17.
    - **Document Extraction:** PyMuPDF (1.28), pdfplumber.
    - **AI / LLM:** Google Gemini API (`google-genai` SDK with `gemini-3.8-flash`).
    - **Persistence:** SQLite with indexing and JSON metadata storage.
    - **Safe Parsing:** Restricted AST transformations with forbidden keyword blocking.
    """)

st.divider()

st.markdown("""
### 🧭 First-Time User Walkthrough

1. **Upload or Select a Paper:** Navigate to the **Dashboard** or **Research Library** and drop a scientific PDF (or pick one of the pre-indexed demo papers).
2. **Inspect Equations:** In the **Paper Explorer**, navigate page-by-page. Notice how equations are detected alongside their surrounding context.
3. **Deconstruct with AI:** Click **✨ Deconstruct** on any equation to view intuitive explanations, variable meanings, derivation paths, and real-world limits.
4. **Experiment in the Playground:** Click **🔬 Playground** to adjust sliders, inspect how energy scales with mass, observe harmonic oscillator phase orbits, or sweep Gaussian probabilities.
5. **Ask the Research Assistant:** Open the **AI Research Assistant** to ask targeted questions about derivations, assumptions, or model comparisons with grounded page citations.
6. **Export Code & Reports:** Download fully commented Python scripts or complete Markdown analysis reports for your research notes.
""")
