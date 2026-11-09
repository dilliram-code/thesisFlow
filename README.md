# ThesisFlow: The Interactive Math & Physics Research Paper Deconstructer

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F51B5.svg)](https://plotly.com/)
[![SymPy](https://img.shields.io/badge/SymPy-Symbolic_Math-3B5526.svg)](https://www.sympy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **ThesisFlow** transforms complex, static LaTeX and mathematical equations in scientific research papers into **interactive, living computational laboratories**.

---

## 🌟 Vision & Overview

In traditional scientific publishing, mathematical formulations appear as static typeset equations. Graduate students, PhD researchers, and physicists often struggle to answer:
- *What does each symbol represent, and what are its physical units?*
- *What fundamental assumptions or boundary conditions justify this formula?*
- *How does the system behave when parameters change dynamically?*
- *How can this mathematical model be translated into clean Python code?*

**ThesisFlow** bridges this divide by turning scientific papers into interactive, multi-dimensional experimentation spaces. It combines the rigorous symbolic reasoning of **SymPy**, interactive graphics of **Plotly**, authoritative physical constants of **NIST CODATA**, and conversational grounding of **Google Gemini (gemini-3.8-flash)** with Retrieval-Augmented Generation (RAG).

---

## 🔬 Core Capabilities

### 1. Multi-Stage PDF Intelligence Engine
- Ingests preprints, manuscripts, and dissertations up to 35 MB.
- Preserves document layout, page coordinates, and section hierarchies using `PyMuPDF` and `pdfplumber`.
- Extracts display math (`$$...$$`, `\[...\]`), numbered equations `(1)`, `(2)`, and LaTeX formulations.
- Assigns unique, persistent identifiers (`EQ-001`, `EQ-002`, ...) with surrounding paragraph context.

### 2. SymPy Symbolic Verification & Safe Evaluation
- Zero arbitrary execution of untrusted user input or LLM code.
- Strict Abstract Syntax Tree (AST) validation using restricted SymPy transformations.
- Categorizes expressions into Algebraic, Differential, Integral, Statistical, Relativistic, and Quantum domains.
- Detects independent versus dependent variables and sets valid slider parameter bounds.

### 3. AI Equation Deconstruction (8 Dimensions)
For every equation, ThesisFlow generates an in-depth structured breakdown:
1. **LaTeX Presentation:** Crisp mathematical rendering via KaTeX.
2. **Plain-Language Explanation:** Intuitive explanation tailored to the selected comprehension depth (Beginner, Intermediate, Advanced, Research-level).
3. **Mathematical Interpretation:** Operators, variable couplings, core assumptions, boundary conditions, and domain of applicability.
4. **Variable Breakdown Table:** Symbol, physical meaning, SI unit, and variable role.
5. **Physical Intuition:** Real-world examples and theoretical analogies.
6. **Derivation Steps:** Explicitly marks reconstructed derivations vs. paper's original text.
7. **Cross-Disciplinary Applications:** Use cases across physics, engineering, and scientific computing.
8. **Limitations & Validity Boundaries:** Non-relativistic limits, continuum breakdowns, and singularity constraints.

### 4. Interactive Equation Playground
- Dynamic slider controls for every variable with live Plotly figure re-rendering.
- Real-time numerical readouts at user-chosen operating points.
- Specialized physics visualizers:
  - **Einstein's Mass-Energy Equivalence ($E = mc^2$):** Mass slider, fixed $c$ constant, energy curve.
  - **Newton's Second Law ($F = ma$):** Force vs. acceleration and mass.
  - **Simple Harmonic Motion ($x(t) = A \cos(\omega t + \phi)$):** Quad-panel displacement, velocity, acceleration, and phase space orbit ($v$ vs. $x$).
  - **Gaussian Probability Density ($f(x)$):** Mean $\mu$, standard deviation $\sigma$, $\pm 1\sigma$ confidence intervals.
  - **Newton's Universal Gravitation ($F = G \frac{m_1 m_2}{r^2}$):** Dual mass controls, inverse-square curve.
- Export curve data to CSV and save parameter snapshots to SQLite.

### 5. Grounded AI Research Assistant (RAG)
- Conversational assistant grounded strictly in the uploaded research paper.
- Mandatory page citations (`[Page X]`) and equation cross-references (`[EQ-001]`).
- Lexical BM25 and semantic vector retrieval with mathematical keyword boosting.
- Hallucination prevention: explicitly states when information is absent from the paper.

### 6. NIST CODATA Scientific Constants Explorer
- Complete directory of fundamental physical constants ($c, h, \hbar, G, e, k_B, N_A, m_e, m_p, \varepsilon_0, \mu_0, \alpha, \sigma, R, a_0$).
- Exact SI values, relative uncertainties, dimensional analysis, and canonical governing equations.
- Automatic symbol detection in equations.

### 7. Multi-Flavor Python Code Generation
- Export production-ready code with type annotations, docstrings, and input checks:
  - **Pure Python** standalone function.
  - **NumPy Vectorized** implementation for array processing.
  - **SymPy Symbolic** script for differentiation and limits.
  - **Plotly Visualization** script for Jupyter notebooks.

---

## 🏗️ Architecture

```
thesisflow/
│
├── app.py                         # Main Streamlit dashboard & entry point
├── config.py                      # Global configuration & theme palettes
├── requirements.txt               # Locked dependencies
├── .env.example                   # Environment configuration template
│
├── assets/
│   └── styles.css                 # Dark/Light academic styling
│
├── components/
│   ├── header.py                  # App banner, project switcher, API status
│   ├── sidebar.py                 # Navigation, paper selector, depth slider
│   ├── equation_card.py           # Multi-action equation card
│   └── visualization.py           # Plotly scientific plotting engine
│
├── core/
│   ├── pdf_parser.py              # PyMuPDF & pdfplumber extraction
│   ├── equation_extractor.py      # LaTeX & numbered math detection
│   ├── mathematical_engine.py     # SymPy parsing & numerical evaluation
│   ├── equation_validator.py      # Syntax & confidence checking
│   ├── variable_analyzer.py       # Physical variable & SI unit inference
│   ├── scientific_constants.py    # NIST CODATA database & cross-referencer
│   └── code_generator.py          # Python / NumPy / SymPy script generator
│
├── services/
│   ├── gemini_service.py          # Google Gemini SDK (gemini-3.8-flash)
│   ├── rag_service.py             # Semantic chunking & BM25 retrieval
│   └── paper_service.py           # Paper pipeline & demo seeder
│
├── database/
│   ├── db.py                      # SQLite connection & CRUD operations
│   └── models.py                  # Paper, Equation, and Experiment dataclasses
│
├── utils/
│   ├── session_utils.py           # Streamlit session state management
│   ├── math_utils.py              # Number formatting & LaTeX cleaning
│   └── file_utils.py              # CSV generation & CSS injection
│
├── pages/
│   ├── 1_Research_Library.py      # Catalog, search, and paper management
│   ├── 2_Paper_Explorer.py        # Split-screen PDF reader & equations
│   ├── 3_Equation_Playground.py   # Interactive scientific laboratory
│   ├── 4_AI_Research_Assistant.py # RAG conversational paper scientist
│   ├── 5_Constants_Explorer.py    # Searchable NIST constants explorer
│   └── 6_About.py                 # Architectural guide & walkthrough
│
├── data/
│   ├── demo_papers/               # Pre-seeded classical physics research PDFs
│   └── uploads/                   # User-uploaded PDFs
│
└── tests/
    └── test_thesisflow.py         # Comprehensive pytest suite
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Clone Repository
```bash
git clone https://github.com/your-username/thesisflow.git
cd thesisflow
```

### 3. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and add your Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
```
*(Note: ThesisFlow operates in offline/local mode if no API key is provided, using SymPy and deterministic heuristics for analysis and plotting).*

### 6. Launch Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Running Unit Tests

Run the complete test suite verifying mathematical parsing, constants lookup, code generation, and RAG retrieval:

```bash
pytest tests/test_thesisflow.py -v
```

All 15 tests cover:
- Einstein's Mass-Energy Equivalence ($E = mc^2$)
- Newton's Second Law ($F = ma$)
- Simple Harmonic Motion ($x(t) = A \cos(\omega t + \phi)$)
- Gaussian Probability Density Function
- Newton's Law of Gravitation ($F = G \frac{m_1 m_2}{r^2}$)
- Schrödinger Wave Equation
- Wave Equations
- AST Code Injection Prevention
- Delimiter Balance Verification
- NIST Constants Lookup & Symbol Detection
- Variable Analyzer & Role Classification
- Pure Python & NumPy Code Generation
- RAG Document Chunking & BM25 Scoring

---

## ☁️ Deployment on Streamlit Community Cloud

1. Push your repository to GitHub.
2. Log into [share.streamlit.io](https://share.streamlit.io/).
3. Connect your repository and select `app.py` as the main file path.
4. In **Advanced Settings -> Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key"
   GEMINI_MODEL = "gemini-3.8-flash"
   ```
5. Deploy! ThesisFlow is fully optimized for memory constraints on Streamlit Cloud.

---

## 🔒 Security & Safe Computing

- **No `eval()` or `exec()`:** ThesisFlow never executes user-submitted or AI-generated strings.
- **SymPy Restricted Transformations:** Mathematical expressions are parsed strictly through AST transformations with forbidden keyword blocking (`__import__`, `eval`, `os`, `sys`, etc.).
- **Graceful Offline Fallback:** If the Gemini API is unreachable, the platform continues functioning smoothly with SymPy calculations, interactive Plotly visualization, and local heuristic analysis.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
