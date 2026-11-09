"""
Equation Card Component for ThesisFlow.
Renders individual equations with LaTeX display, metadata badges,
AI deconstruction tabs, variable tables, code generator, and playground links.
"""

from typing import Optional
import streamlit as st
from database.models import Equation
from database.db import db
from utils.session_utils import set_active_equation
from utils.math_utils import clean_latex_string
from core.code_generator import CodeGenerator
from services.gemini_service import GeminiService
from services.paper_service import paper_service


def render_equation_card(eq: Equation, paper_title: str = "Research Paper", allow_playground: bool = True):
    """Renders a fully interactive equation card."""
    with st.container():
        # Top Card Header with Badges
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <span class="thesisflow-badge">{eq.eq_id}</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: #F8FAFC;">{eq.section_title}</span>
                <span style="font-size: 0.75rem; color: #64748B;">• Page {eq.page_number}</span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            conf_percent = int(eq.confidence * 100)
            badge_class = "badge-verified" if eq.confidence >= 0.8 else "badge-warning"
            st.markdown(f"""
            <div style="text-align: right;">
                <span class="thesisflow-badge {badge_class}">{eq.category} ({conf_percent}%)</span>
            </div>
            """, unsafe_allow_html=True)

        # LaTeX Equation Display
        cleaned_latex = clean_latex_string(eq.latex)
        try:
            st.latex(cleaned_latex)
        except Exception:
            st.code(eq.latex, language="latex")

        # Action Buttons Row
        b_col1, b_col2, b_col3, b_col4 = st.columns([1.2, 1.2, 1.2, 1.2])

        with b_col1:
            if allow_playground:
                if st.button("🔬 Playground", key=f"play_{eq.id}_{eq.eq_id}", help="Experiment with variables and live Plotly graph"):
                    set_active_equation(eq.id)
                    st.switch_page("pages/3_Equation_Playground.py")

        with b_col2:
            show_decon = st.button("✨ Deconstruct", key=f"decon_{eq.id}_{eq.eq_id}", help="AI deep dive into meaning, assumptions & derivation")

        with b_col3:
            show_code = st.button("💻 Python Code", key=f"code_{eq.id}_{eq.eq_id}", help="View and download executable Python / NumPy / SymPy implementations")

        with b_col4:
            md_report = paper_service.export_equation_markdown(eq, paper_title)
            st.download_button(
                "📥 Export",
                data=md_report,
                file_name=f"{eq.eq_id}_analysis.md",
                mime="text/markdown",
                key=f"export_{eq.id}_{eq.eq_id}",
                help="Download full equation analysis as Markdown"
            )

        # Context Paragraph Accordion
        if eq.context_paragraph:
            with st.expander("📄 Document Context from Paper", expanded=False):
                st.caption(f"Excerpt surrounding {eq.eq_id} on page {eq.page_number}:")
                st.write(eq.context_paragraph)

        # Dynamic Code Implementation Expander
        if show_code:
            with st.expander(f"💻 Executable Code Suite for {eq.eq_id}", expanded=True):
                vars_list = [v.get("symbol", "x") for v in eq.variables if v.get("var_type") != "Constant"]
                dep_var = next((v.get("symbol") for v in eq.variables if v.get("var_type") == "Dependent quantity"), "y")
                code_suite = CodeGenerator.generate_all_implementations(
                    latex_str=eq.latex,
                    dependent_var=dep_var,
                    independent_vars=vars_list,
                    equation_name=f"{eq.eq_id}_{eq.section_title}",
                    variables_meta=eq.variables
                )

                c_tab1, c_tab2, c_tab3, c_tab4 = st.tabs(["Pure Python", "NumPy Vectorized", "SymPy Symbolic", "Plotly Visualizer"])
                with c_tab1:
                    st.code(code_suite["pure_python"], language="python")
                    st.download_button("Download pure_python.py", data=code_suite["pure_python"], file_name=f"{eq.eq_id}_pure.py")
                with c_tab2:
                    st.code(code_suite["numpy"], language="python")
                    st.download_button("Download numpy_impl.py", data=code_suite["numpy"], file_name=f"{eq.eq_id}_numpy.py")
                with c_tab3:
                    st.code(code_suite["sympy"], language="python")
                with c_tab4:
                    st.code(code_suite["plotly"], language="python")

        # Dynamic AI Deconstruction Expander
        if show_decon:
            with st.expander(f"✨ Scientific Deconstruction: {eq.eq_id}", expanded=True):
                explanation = eq.explanation
                if not explanation:
                    with st.spinner("Analyzing mathematical formulation and physical context..."):
                        gemini = GeminiService()
                        explanation = gemini.deconstruct_equation(
                            latex=eq.latex,
                            context_text=eq.context_paragraph,
                            section_title=eq.section_title,
                            depth_level=st.session_state.get("explanation_depth", "Intermediate"),
                            paper_title=paper_title
                        )
                        # Save in DB for instant cache reload
                        eq.explanation = explanation
                        db.update_equation_explanation(eq.id, explanation, eq.variables)

                if "ai_notice" in explanation:
                    st.caption(f"ℹ️ {explanation['ai_notice']}")

                tab_a, tab_b, tab_c, tab_d, tab_e, tab_f = st.tabs([
                    "Intuition", "Mathematical Structure", "Variables", "Physical Context", "Derivation", "Limitations"
                ])

                with tab_a:
                    st.markdown("#### Plain-Language Explanation")
                    st.info(explanation.get("plain_language_explanation", "No explanation available."))

                with tab_b:
                    st.markdown("#### Mathematical Interpretation")
                    math_info = explanation.get("mathematical_interpretation", {})
                    if isinstance(math_info, dict):
                        st.write(f"**Structure & Form:** {math_info.get('structure', 'Standard algebraic relation.')}")
                        st.write(f"**Variable Interactions:** {math_info.get('relationships', 'Proportional and inverse balances.')}")
                        st.write(f"**Core Assumptions:** {math_info.get('assumptions', 'Linear continuum regime.')}")
                        st.write(f"**Boundary Conditions:** {math_info.get('boundary_conditions', 'Real coordinate space.')}")
                        st.write(f"**Applicable Domain:** {math_info.get('domain_of_applicability', 'All real numbers.')}")
                    else:
                        st.write(str(math_info))

                with tab_c:
                    st.markdown("#### Variable Breakdown Table")
                    vars_list = explanation.get("variable_breakdown", eq.variables)
                    if vars_list:
                        header = "| Symbol | Meaning | Unit | Type |\n|---|---|---|---|\n"
                        rows = "\n".join([
                            f"| `{v.get('symbol', '')}` | {v.get('meaning', '')} | {v.get('unit', 'unspecified')} | {v.get('type', v.get('var_type', 'Variable'))} |"
                            for v in vars_list
                        ])
                        st.markdown(header + rows)
                    else:
                        st.caption("No variables detected.")

                with tab_d:
                    st.markdown("#### Physical Meaning & Real-World Intuition")
                    st.write(explanation.get("physical_intuition", "Physical relationship balancing observable quantities."))
                    st.markdown("##### Applications Across Disciplines:")
                    for app in explanation.get("applications", []):
                        st.markdown(f"- {app}")

                with tab_e:
                    st.markdown("#### Derivation Steps")
                    st.write(explanation.get("derivation", "[Reconstructed Derivation] Originates from primary conservation principles."))

                with tab_f:
                    st.markdown("#### Theoretical Limitations & Non-Applicability")
                    for lim in explanation.get("limitations", []):
                        st.markdown(f"- ⚠️ {lim}")

        st.markdown("<hr style='border: none; border-bottom: 1px solid #1E293B; margin: 16px 0;'>", unsafe_allow_html=True)

