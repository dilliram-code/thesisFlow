"""
Page 3: Equation Playground for ThesisFlow.
Interactive scientific laboratory for dynamic parameter experimentation and real-time visualization.
Supports canonical physics models as well as any symbolically validated equation extracted from research papers.
"""

import streamlit as st
import numpy as np
from pathlib import Path
from config import ASSETS_DIR
from utils.file_utils import load_custom_css, generate_csv_from_grid
from utils.session_utils import init_session_state, get_active_paper, get_active_equation, set_active_equation
from utils.math_utils import format_scientific_number
from components.sidebar import render_sidebar
from components.header import render_header
from components.visualization import ScientificVisualizer
from database.db import db
from database.models import Experiment
from core.mathematical_engine import MathematicalEngine
from core.variable_analyzer import VariableAnalyzer
from core.scientific_constants import SCIENTIFIC_CONSTANTS

st.set_page_config(page_title="Equation Playground | ThesisFlow", page_icon="🔬", layout="wide")
css = load_custom_css(ASSETS_DIR / "styles.css")
if css:
    st.markdown(css, unsafe_allow_html=True)

init_session_state()
render_sidebar()
render_header()

st.title("🔬 Interactive Equation Playground")
st.markdown("Transform theoretical equations into living scientific experiments with real-time parameter controls.")

# Canonical Presets Registry
CANONICAL_PRESETS = {
    "Einstein's Mass-Energy Equivalence": {
        "latex": "E = m c^2",
        "description": "Mass-energy equivalence in Special Relativity ($c = 299,792,458\\text{ m/s}$).",
        "primary_indep": "m",
        "dep_var": "E",
        "variables": [
            {"symbol": "m", "meaning": "Mass", "unit": "kg", "var_type": "Variable", "min": 0.001, "max": 100.0, "default": 1.0, "step": 0.5},
            {"symbol": "c", "meaning": "Speed of Light", "unit": "m/s", "var_type": "Constant", "min": 299792458.0, "max": 299792458.0, "default": 299792458.0, "is_constant": True}
        ]
    },
    "Newton's Second Law of Motion": {
        "latex": "F = m a",
        "description": "Fundamental law of classical Newtonian dynamics relating net force to mass and acceleration.",
        "primary_indep": "a",
        "dep_var": "F",
        "variables": [
            {"symbol": "m", "meaning": "Mass", "unit": "kg", "var_type": "Parameter", "min": 0.1, "max": 100.0, "default": 10.0, "step": 0.5},
            {"symbol": "a", "meaning": "Acceleration", "unit": "m/s²", "var_type": "Variable", "min": -50.0, "max": 50.0, "default": 9.81, "step": 0.5}
        ]
    },
    "Simple Harmonic Motion": {
        "latex": r"x(t) = A \cos(\omega t + \phi)",
        "description": "Oscillatory displacement in an undamped conservative linear system.",
        "primary_indep": "t",
        "dep_var": "x",
        "is_harmonic_special": True,
        "variables": [
            {"symbol": "A", "meaning": "Amplitude", "unit": "m", "var_type": "Parameter", "min": 0.1, "max": 10.0, "default": 2.0, "step": 0.1},
            {"symbol": "omega", "meaning": "Angular Frequency (ω)", "unit": "rad/s", "var_type": "Parameter", "min": 0.1, "max": 15.0, "default": 2.0, "step": 0.1},
            {"symbol": "phi", "meaning": "Phase Constant (φ)", "unit": "rad", "var_type": "Parameter", "min": -3.1415, "max": 3.1415, "default": 0.0, "step": 0.1},
            {"symbol": "t", "meaning": "Time", "unit": "s", "var_type": "Variable", "min": 0.0, "max": 10.0, "default": 1.0, "step": 0.1}
        ]
    },
    "Gaussian Normal Distribution": {
        "latex": r"f(x) = \frac{1}{\sigma \sqrt{2 \pi}} \exp\left(-\frac{(x - \mu)^2}{2 \sigma^2}\right)",
        "description": "Continuous probability density function parameterized by mean μ and standard deviation σ.",
        "primary_indep": "x",
        "dep_var": "f",
        "is_gaussian_special": True,
        "variables": [
            {"symbol": "mu", "meaning": "Mean (μ)", "unit": "unspecified", "var_type": "Parameter", "min": -10.0, "max": 10.0, "default": 0.0, "step": 0.2},
            {"symbol": "sigma", "meaning": "Standard Deviation (σ)", "unit": "unspecified", "var_type": "Parameter", "min": 0.1, "max": 8.0, "default": 1.0, "step": 0.1},
            {"symbol": "x", "meaning": "Coordinate x", "unit": "unspecified", "var_type": "Variable", "min": -10.0, "max": 10.0, "default": 0.0, "step": 0.1}
        ]
    },
    "Newton's Universal Gravitation": {
        "latex": r"F = G \frac{m_1 m_2}{r^2}",
        "description": "Gravitational attraction between two masses separated by distance r.",
        "primary_indep": "r",
        "dep_var": "F",
        "variables": [
            {"symbol": "m_1", "meaning": "Mass 1", "unit": "kg", "var_type": "Parameter", "min": 1.0, "max": 1e6, "default": 5.972e4, "step": 1000.0},
            {"symbol": "m_2", "meaning": "Mass 2", "unit": "kg", "var_type": "Parameter", "min": 1.0, "max": 1e6, "default": 1000.0, "step": 100.0},
            {"symbol": "r", "meaning": "Separation Distance", "unit": "m", "var_type": "Variable", "min": 1.0, "max": 1000.0, "default": 50.0, "step": 5.0},
            {"symbol": "G", "meaning": "Gravitational Constant", "unit": "N m²/kg²", "var_type": "Constant", "min": 6.6743e-11, "max": 6.6743e-11, "default": 6.6743e-11, "is_constant": True}
        ]
    }
}

# Source Selection
active_paper = get_active_paper()
active_eq = get_active_equation()
paper_eqs = db.get_equations_by_paper(active_paper.id) if active_paper else []

choice_options = ["Canonical Physics Laboratory"]
if paper_eqs:
    choice_options.append(f"Equations from Active Paper ({len(paper_eqs)} available)")

source_col1, source_col2 = st.columns([1, 2])
with source_col1:
    selected_source = st.selectbox("Select Experiment Source:", options=choice_options)

current_model = None

if selected_source == "Canonical Physics Laboratory":
    with source_col2:
        preset_name = st.selectbox("Select Physics Model:", options=list(CANONICAL_PRESETS.keys()))
        current_model = CANONICAL_PRESETS[preset_name]
        current_latex = current_model["latex"]
        current_desc = current_model["description"]
        current_vars = current_model["variables"]
        is_harmonic = current_model.get("is_harmonic_special", False)
        is_gaussian = current_model.get("is_gaussian_special", False)
else:
    with source_col2:
        eq_map = {e.id: f"{e.eq_id}: {e.latex[:40]} ({e.section_title})" for e in paper_eqs}
        default_id = active_eq.id if active_eq and active_eq.id in eq_map else paper_eqs[0].id
        selected_eq_id = st.selectbox("Choose Equation to Deconstruct:", options=list(eq_map.keys()), format_func=lambda x: eq_map[x], index=list(eq_map.keys()).index(default_id))
        paper_eq = db.get_equation_by_id(selected_eq_id)
        current_latex = paper_eq.latex
        current_desc = f"{paper_eq.eq_id} from '{active_paper.title}' (Page {paper_eq.page_number})"
        current_vars = paper_eq.variables
        is_harmonic = "cos" in current_latex and ("omega" in current_latex or r"\omega" in current_latex)
        is_gaussian = "exp" in current_latex and ("sigma" in current_latex or r"\sigma" in current_latex)

st.markdown(f"""
<div class="thesisflow-header" style="margin: 16px 0;">
    <span class="thesisflow-badge">ACTIVE EXPERIMENT</span>
    <h3 style="margin: 8px 0 4px 0; color: #F8FAFC;">{current_desc}</h3>
</div>
""", unsafe_allow_html=True)

st.latex(current_latex)

st.divider()

# Specialized Visualizations
if is_harmonic:
    # Harmonic motion parameters
    h_col1, h_col2 = st.columns([1, 2])
    with h_col1:
        st.markdown("#### 🎛️ Oscillator Parameters")
        A_val = st.slider("Amplitude (A) [m]", 0.1, 10.0, 2.0, 0.1)
        w_val = st.slider("Angular Frequency (ω) [rad/s]", 0.1, 20.0, 2.0, 0.1)
        phi_val = st.slider("Phase Constant (φ) [rad]", -3.1415, 3.1415, 0.0, 0.1)
        t_max = st.slider("Time Domain Range [s]", 2.0, 30.0, 10.0, 1.0)

        # Derived physics metrics
        period = (2 * np.pi) / w_val
        frequency = 1.0 / period
        v_max = A_val * w_val
        a_max = A_val * (w_val ** 2)

        st.markdown(f"""
        <div style="background: #141C2E; border: 1px solid #23314A; border-radius: 8px; padding: 12px; margin-top: 14px;">
            <div style="font-size: 0.75rem; color: #00E5FF; text-transform: uppercase; font-weight: 600;">Analytical Physical Properties:</div>
            <div style="margin-top: 6px; font-size: 0.88rem; color: #F8FAFC;">
                <div>Period (T): <b>{period:.3f} s</b></div>
                <div>Frequency (f): <b>{frequency:.3f} Hz</b></div>
                <div>Max Velocity (v_max): <b>{v_max:.3f} m/s</b></div>
                <div>Max Acceleration (a_max): <b>{a_max:.3f} m/s²</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with h_col2:
        st.markdown("#### 📈 Quad-Panel Scientific Dynamics")
        fig_harmonic = ScientificVisualizer.create_harmonic_motion_visualizer(A_val, w_val, phi_val, t_max)
        st.plotly_chart(fig_harmonic, use_container_width=True)

elif is_gaussian:
    g_col1, g_col2 = st.columns([1, 2])
    with g_col1:
        st.markdown("#### 🎛️ Distribution Parameters")
        mu_val = st.slider("Mean (μ)", -10.0, 10.0, 0.0, 0.2)
        sig_val = st.slider("Standard Deviation (σ)", 0.1, 8.0, 1.0, 0.1)
        x_span = st.slider("Evaluation Window (±σ)", 2.0, 6.0, 4.0, 0.5)

        peak_density = 1.0 / (sig_val * np.sqrt(2 * np.pi))
        variance = sig_val ** 2

        st.markdown(f"""
        <div style="background: #141C2E; border: 1px solid #23314A; border-radius: 8px; padding: 12px; margin-top: 14px;">
            <div style="font-size: 0.75rem; color: #00E5FF; text-transform: uppercase; font-weight: 600;">Statistical Invariants:</div>
            <div style="margin-top: 6px; font-size: 0.88rem; color: #F8FAFC;">
                <div>Peak Density f(μ): <b>{peak_density:.4f}</b></div>
                <div>Variance (σ²): <b>{variance:.4f}</b></div>
                <div>FWHM: <b>{2.355 * sig_val:.3f}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with g_col2:
        st.markdown("#### 📈 Gaussian Probability Density Curve")
        fig_gauss = ScientificVisualizer.create_gaussian_visualizer(
            mu=mu_val, sigma=sig_val,
            x_min=mu_val - x_span * sig_val,
            x_max=mu_val + x_span * sig_val
        )
        st.plotly_chart(fig_gauss, use_container_width=True)

else:
    # Generalized SymPy Parameter Laboratory
    p_col1, p_col2 = st.columns([1, 2])

    parsed_expr = MathematicalEngine.safe_parse(current_latex)
    if parsed_expr is None:
        st.warning("⚠️ This mathematical expression uses advanced operators that cannot be automatically evaluated on a 1D grid. Check the AI Deconstruction tab for theoretical analysis.")
    else:
        symbols = MathematicalEngine.extract_symbols(parsed_expr)
        var_analysis = current_vars if current_vars else VariableAnalyzer.analyze_symbols(symbols, current_latex)

        dep_var, indep_candidates = VariableAnalyzer.identify_dependent_independent(var_analysis)
        indep_candidates = [s for s in symbols if s != dep_var] or symbols

        with p_col1:
            st.markdown("#### 🎛️ Independent Axes & Parameters")
            primary_x = st.selectbox("Plot X-Axis Variable:", options=indep_candidates, index=0)

            # Sliders for other variables
            param_values = {}
            for v in var_analysis:
                sym = v.get("symbol")
                if sym == dep_var:
                    continue
                if v.get("is_constant") or sym == "c" or sym == "G":
                    st.caption(f"🔒 **{sym}** ({v.get('meaning')}): Fixed constant = {v.get('default_val')}")
                    param_values[sym] = float(v.get("default_val", 1.0))
                    continue

                if sym == primary_x:
                    # Operating point slider
                    min_val = float(v.get("min_val", 0.1))
                    max_val = float(v.get("max_val", 50.0))
                    def_val = float(v.get("default_val", (min_val + max_val) / 2))
                    step = (max_val - min_val) / 100.0 if max_val > min_val else 0.1
                    param_values[sym] = st.slider(f"Operating Point '{sym}' [{v.get('unit', '')}]", min_val, max_val, def_val, step)
                else:
                    min_val = float(v.get("min_val", 0.1))
                    max_val = float(v.get("max_val", 50.0))
                    def_val = float(v.get("default_val", 1.0))
                    step = (max_val - min_val) / 100.0 if max_val > min_val else 0.1
                    param_values[sym] = st.slider(f"Parameter '{sym}' [{v.get('unit', '')}]", min_val, max_val, def_val, step)

            # Domain bounds for X
            with st.expander("Domain Boundaries", expanded=False):
                x_min_domain = st.number_input("X Min:", value=0.1)
                x_max_domain = st.number_input("X Max:", value=50.0)

            # Live numerical calculation
            curr_x = param_values.get(primary_x, 1.0)
            eval_point = MathematicalEngine.evaluate_numerical_point(parsed_expr, param_values, target_dep_var=dep_var)

            st.markdown(f"""
            <div class="stat-card" style="margin-top: 16px;">
                <span class="stat-label">Calculated {dep_var} at Operating Point:</span>
                <span class="stat-value" style="color: #00E5FF; font-size: 1.5rem;">{format_scientific_number(eval_point)}</span>
            </div>
            """, unsafe_allow_html=True)

        with p_col2:
            st.markdown(f"#### 📈 Real-Time Plot: {dep_var} versus {primary_x}")
            x_vals, y_vals, msg = MathematicalEngine.generate_1d_grid(
                parsed_expr,
                independent_var=primary_x,
                min_val=x_min_domain if 'x_min_domain' in locals() else 0.1,
                max_val=x_max_domain if 'x_max_domain' in locals() else 50.0,
                fixed_params=param_values,
                num_points=300,
                target_dep_var=dep_var
            )

            fig = ScientificVisualizer.create_1d_curve(
                x=x_vals,
                y=y_vals,
                title=f"{dep_var} vs {primary_x} ({current_latex})",
                x_label=primary_x,
                y_label=dep_var or "Response",
                current_x=curr_x,
                current_y=eval_point
            )
            st.plotly_chart(fig, use_container_width=True)

            # Download CSV
            csv_str = generate_csv_from_grid(x_vals.tolist(), y_vals.tolist(), primary_x, dep_var or "y")
            st.download_button(
                "📥 Download Curve Data (CSV)",
                data=csv_str,
                file_name=f"{dep_var}_vs_{primary_x}_data.csv",
                mime="text/csv"
            )

# Save Experiment Module
st.divider()
st.subheader("💾 Save Experiment Snapshot")
exp_col1, exp_col2 = st.columns([2, 1])
with exp_col1:
    exp_name = st.text_input("Experiment Name:", value=f"Run on {current_desc[:30]}")
    exp_notes = st.text_area("Observations / Theoretical Notes:", placeholder="Notes on parameter sensitivity, asymptotic behavior...")
with exp_col2:
    st.write("")
    st.write("")
    if st.button("💾 Save Snapshot to Database", type="primary"):
        new_exp = Experiment(
            name=exp_name,
            notes=exp_notes,
            eq_code=current_latex,
            parameters={"model": current_desc}
        )
        exp_id = db.insert_experiment(new_exp)
        st.success(f"Snapshot #{exp_id} saved successfully!")

