"""
Unit and Integration Test Suite for ThesisFlow.
Verifies mathematical engine, SymPy parsing, variable analyzer, constants lookup,
code generator, equation validator, and RAG retrieval across core physical equations:
1. E = mc^2
2. F = ma
3. x(t) = A cos(omega t + phi)
4. Gaussian probability density function
5. Schrödinger equation
6. Newton's law of gravitation
7. Wave / Maxwell formulations
8. Malformed and malicious expressions (injection prevention)
"""

import pytest
import numpy as np
import sympy as sp

from core.mathematical_engine import MathematicalEngine
from core.equation_validator import EquationValidator
from core.variable_analyzer import VariableAnalyzer
from core.scientific_constants import (
    get_constant_by_symbol,
    identify_constants_in_equation,
    SCIENTIFIC_CONSTANTS
)
from core.code_generator import CodeGenerator
from services.rag_service import RAGService
from database.models import Paper, Equation
from database.db import Database


# --- 1. Mathematical Parsing & Validation Tests ---

def test_einstein_mass_energy_equivalence():
    latex = "E = m c^2"
    val = EquationValidator.validate(latex)
    assert val["is_valid"] is True
    assert val["confidence"] >= 0.8

    # Safe parsing
    parsed = MathematicalEngine.safe_parse(latex)
    assert parsed is not None
    symbols = MathematicalEngine.extract_symbols(parsed)
    assert "m" in symbols
    assert "c" in symbols

    # Numerical evaluation
    # m = 2 kg, c = 3e8 m/s -> E = 2 * (3e8)^2 = 1.8e17 J
    eval_val = MathematicalEngine.evaluate_numerical_point(
        parsed, {"m": 2.0, "c": 3e8}, target_dep_var="E"
    )
    assert eval_val is not None
    assert np.isclose(eval_val, 1.8e17)


def test_newton_second_law():
    latex = "F = m a"
    val = EquationValidator.validate(latex)
    assert val["is_valid"] is True

    parsed = MathematicalEngine.safe_parse(latex)
    assert parsed is not None
    symbols = MathematicalEngine.extract_symbols(parsed)
    assert "m" in symbols
    assert "a" in symbols

    # m = 5 kg, a = 9.8 m/s^2 -> F = 49.0 N
    eval_val = MathematicalEngine.evaluate_numerical_point(
        parsed, {"m": 5.0, "a": 9.8}, target_dep_var="F"
    )
    assert np.isclose(eval_val, 49.0)


def test_simple_harmonic_motion():
    latex = r"x = A * cos(omega * t + phi)"
    val = EquationValidator.validate(latex)
    assert val["is_valid"] is True

    parsed = MathematicalEngine.safe_parse(latex)
    assert parsed is not None

    # At t = 0, phi = 0, x = A cos(0) = A
    eval_val = MathematicalEngine.evaluate_numerical_point(
        parsed, {"A": 3.5, "omega": 2.0, "t": 0.0, "phi": 0.0}, target_dep_var="x"
    )
    assert np.isclose(eval_val, 3.5)

    # 1D Grid generation
    x_vals, y_vals, status = MathematicalEngine.generate_1d_grid(
        parsed,
        independent_var="t",
        min_val=0.0,
        max_val=10.0,
        fixed_params={"A": 2.0, "omega": 1.0, "phi": 0.0},
        num_points=100,
        target_dep_var="x"
    )
    assert len(x_vals) == 100
    assert len(y_vals) == 100
    assert not np.isnan(y_vals[0])


def test_gaussian_distribution():
    latex = r"f = \frac{1}{\sigma \sqrt{2 \pi}} \exp\left(-\frac{(x - \mu)^2}{2 \sigma^2}\right)"
    val = EquationValidator.validate(latex)
    assert val["is_valid"] is True

    parsed = MathematicalEngine.safe_parse(latex)
    assert parsed is not None

    # Peak value at x = mu should be 1 / (sigma * sqrt(2*pi))
    sigma_val = 1.0
    mu_val = 0.0
    expected_peak = 1.0 / (sigma_val * np.sqrt(2 * np.pi))

    eval_val = MathematicalEngine.evaluate_numerical_point(
        parsed, {"sigma": sigma_val, "mu": mu_val, "x": mu_val}, target_dep_var="f"
    )
    assert eval_val is not None
    assert np.isclose(eval_val, expected_peak, rtol=1e-3)


def test_newton_gravitation():
    latex = r"F = G \frac{m_1 m_2}{r^2}"
    val = EquationValidator.validate(latex)
    assert val["is_valid"] is True

    parsed = MathematicalEngine.safe_parse(latex)
    assert parsed is not None
    symbols = MathematicalEngine.extract_symbols(parsed)
    assert "G" in symbols
    assert "r" in symbols

    # G = 6.6743e-11, m1 = 1000, m2 = 1000, r = 10 -> F = G * 1e6 / 100 = 10000 * G
    eval_val = MathematicalEngine.evaluate_numerical_point(
        parsed, {"G": 6.6743e-11, "m_1": 1000.0, "m_2": 1000.0, "r": 10.0}, target_dep_var="F"
    )
    assert np.isclose(eval_val, 6.6743e-11 * 10000.0)


def test_schrodinger_equation_preservation():
    # Advanced operator equation
    latex = r"i \hbar \frac{\partial \psi}{\partial t} = - \frac{\hbar^2}{2 m} \frac{\partial^2 \psi}{\partial x^2} + V(x) \psi"
    val = EquationValidator.validate(latex)
    assert val["is_valid"] is True
    assert val["category"] == "Quantum Mechanical"
    # Preserved faithfully even when not trivially evaluated on a scalar 1D grid
    assert val["confidence"] >= 0.8


def test_wave_equation():
    latex = r"\frac{\partial^2 u}{\partial t^2} = v^2 \frac{\partial^2 u}{\partial x^2}"
    val = EquationValidator.validate(latex)
    assert val["is_valid"] is True
    assert val["category"] == "Differential"


# --- 2. Security and Malformed Input Tests ---

def test_code_injection_prevention():
    malicious = "__import__('os').system('echo hack')"
    with pytest.raises(ValueError, match="Forbidden token detected"):
        MathematicalEngine.safe_parse(malicious)


def test_unbalanced_delimiters():
    malformed = r"\frac{a}{b"
    val = EquationValidator.validate(malformed)
    assert val["is_valid"] is False
    assert val["confidence"] <= 0.5


# --- 3. Scientific Constants Tests ---

def test_constants_lookup():
    c = get_constant_by_symbol("c")
    assert c is not None
    assert c.value == 299792458.0
    assert c.unit == "m s⁻¹"

    h = get_constant_by_symbol("h")
    assert h is not None
    assert np.isclose(h.value, 6.62607015e-34)

    hbar = get_constant_by_symbol("hbar")
    assert hbar is not None
    assert np.isclose(hbar.value, 1.054571817e-34)

    G = get_constant_by_symbol("G")
    assert G is not None
    assert np.isclose(G.value, 6.67430e-11)


def test_identify_constants_in_equation():
    found = identify_constants_in_equation("E = m c^2")
    symbols = [c.symbol for c in found]
    assert "c" in symbols

    found_q = identify_constants_in_equation(r"i \hbar \frac{\partial \psi}{\partial t}")
    symbols_q = [c.symbol for c in found_q]
    assert "hbar" in symbols_q


# --- 4. Variable Analyzer Tests ---

def test_variable_analyzer():
    symbols = ["E", "m", "c"]
    vars_info = VariableAnalyzer.analyze_symbols(symbols, "E = m c^2")
    assert len(vars_info) == 3

    # Check c is classified as Constant
    c_info = next((v for v in vars_info if v["symbol"] == "c"), None)
    assert c_info is not None
    assert c_info["var_type"] == "Constant"

    # Check E is classified as Dependent quantity
    e_info = next((v for v in vars_info if v["symbol"] == "E"), None)
    assert e_info is not None
    assert e_info["var_type"] == "Dependent quantity"


# --- 5. Code Generator Tests ---

def test_code_generator_pure_python():
    code = CodeGenerator.generate_pure_python(
        latex_str="F = m * a",
        dependent_var="F",
        indep_vars=["m", "a"],
        fn_name="calculate_force"
    )
    assert "def calculate_force" in code
    assert "m: float" in code
    assert "a: float" in code
    assert "return float(result)" in code


def test_code_generator_numpy():
    code = CodeGenerator.generate_numpy(
        latex_str="E = m * c**2",
        dependent_var="E",
        indep_vars=["m"],
        fn_name="calculate_energy"
    )
    assert "import numpy as np" in code
    assert "_vectorized" in code


# --- 6. RAG Retrieval Tests ---

def test_rag_service():
    rag = RAGService(chunk_size=50, chunk_overlap=10)
    mock_pages = [
        {
            "page_number": 1,
            "text": "Albert Einstein formulated the theory of Special Relativity where energy and mass are equivalent.",
            "blocks": [{"text": "Albert Einstein formulated the theory of Special Relativity where energy and mass are equivalent.", "is_heading": False}]
        },
        {
            "page_number": 2,
            "text": "Newtonian dynamics describe classical force as the rate of change of momentum F = ma.",
            "blocks": [{"text": "Newtonian dynamics describe classical force as the rate of change of momentum F = ma.", "is_heading": False}]
        }
    ]
    rag.index_paper(paper_id=999, pages_data=mock_pages)

    retrieved = rag.retrieve(paper_id=999, query="mass-energy equivalence in special relativity", top_k=1)
    assert len(retrieved) > 0
    assert retrieved[0]["page"] == 1
