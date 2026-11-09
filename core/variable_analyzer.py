"""
Variable Analyzer Module for ThesisFlow.
Extracts mathematical symbols, classifies their roles (Dependent, Independent, Constant, Parameter),
infers standard SI units, and configures interactive slider bounds.
"""

from typing import List, Dict, Any, Optional, Set
import re
from core.scientific_constants import get_constant_by_symbol, SCIENTIFIC_CONSTANTS


# Known physical quantities database for heuristic lookup
KNOWN_QUANTITIES: Dict[str, Dict[str, Any]] = {
    "E": {"meaning": "Energy", "unit": "J", "var_type": "Dependent quantity", "min": 0.0, "max": 1e18, "default": 1.0},
    "m": {"meaning": "Mass", "unit": "kg", "var_type": "Variable", "min": 0.001, "max": 100.0, "default": 1.0},
    "c": {"meaning": "Speed of Light", "unit": "m s⁻¹", "var_type": "Constant", "min": 299792458.0, "max": 299792458.0, "default": 299792458.0},
    "F": {"meaning": "Force", "unit": "N", "var_type": "Dependent quantity", "min": -500.0, "max": 500.0, "default": 10.0},
    "a": {"meaning": "Acceleration", "unit": "m s⁻²", "var_type": "Variable", "min": -50.0, "max": 50.0, "default": 9.81},
    "v": {"meaning": "Velocity", "unit": "m s⁻¹", "var_type": "Variable", "min": -100.0, "max": 100.0, "default": 5.0},
    "t": {"meaning": "Time", "unit": "s", "var_type": "Variable", "min": 0.0, "max": 20.0, "default": 1.0},
    "x": {"meaning": "Position / Spatial Coordinate", "unit": "m", "var_type": "Variable", "min": -10.0, "max": 10.0, "default": 0.0},
    "A": {"meaning": "Amplitude", "unit": "m", "var_type": "Parameter", "min": 0.1, "max": 20.0, "default": 2.0},
    "omega": {"meaning": "Angular Frequency (ω)", "unit": "rad s⁻¹", "var_type": "Parameter", "min": 0.1, "max": 25.0, "default": 2.0},
    "phi": {"meaning": "Phase Constant (φ)", "unit": "rad", "var_type": "Parameter", "min": -3.1415, "max": 3.1415, "default": 0.0},
    "mu": {"meaning": "Mean / Center (μ)", "unit": "unspecified", "var_type": "Parameter", "min": -10.0, "max": 10.0, "default": 0.0},
    "sigma": {"meaning": "Standard Deviation (σ)", "unit": "unspecified", "var_type": "Parameter", "min": 0.1, "max": 10.0, "default": 1.0},
    "G": {"meaning": "Gravitational Constant", "unit": "m³ kg⁻¹ s⁻²", "var_type": "Constant", "min": 6.6743e-11, "max": 6.6743e-11, "default": 6.6743e-11},
    "r": {"meaning": "Distance / Separation Radius", "unit": "m", "var_type": "Variable", "min": 0.1, "max": 1000.0, "default": 10.0},
    "T": {"meaning": "Thermodynamic Temperature", "unit": "K", "var_type": "Variable", "min": 0.0, "max": 1000.0, "default": 300.0},
    "P": {"meaning": "Pressure", "unit": "Pa", "var_type": "Dependent quantity", "min": 0.0, "max": 1e6, "default": 101325.0},
    "V": {"meaning": "Volume", "unit": "m³", "var_type": "Variable", "min": 0.01, "max": 100.0, "default": 1.0},
    "n": {"meaning": "Amount of Substance", "unit": "mol", "var_type": "Variable", "min": 0.1, "max": 100.0, "default": 1.0},
    "R": {"meaning": "Universal Gas Constant", "unit": "J mol⁻¹ K⁻¹", "var_type": "Constant", "min": 8.314, "max": 8.314, "default": 8.314},
    "hbar": {"meaning": "Reduced Planck Constant", "unit": "J s", "var_type": "Constant", "min": 1.05457e-34, "max": 1.05457e-34, "default": 1.05457e-34},
    "h": {"meaning": "Planck Constant", "unit": "J s", "var_type": "Constant", "min": 6.62607e-34, "max": 6.62607e-34, "default": 6.62607e-34},
    "nu": {"meaning": "Frequency (ν)", "unit": "Hz", "var_type": "Variable", "min": 1.0, "max": 1e15, "default": 5e14},
    "k_B": {"meaning": "Boltzmann Constant", "unit": "J K⁻¹", "var_type": "Constant", "min": 1.380649e-23, "max": 1.380649e-23, "default": 1.380649e-23},
    "q": {"meaning": "Electric Charge", "unit": "C", "var_type": "Variable", "min": -1e-6, "max": 1e-6, "default": 1.6e-19},
    "k": {"meaning": "Spring Constant or Wave Number", "unit": "N m⁻¹ or m⁻¹", "var_type": "Parameter", "min": 0.1, "max": 200.0, "default": 10.0},
    "L": {"meaning": "Length or Inductance", "unit": "m or H", "var_type": "Parameter", "min": 0.1, "max": 50.0, "default": 1.0},
    "lambda_sym": {"meaning": "Wavelength (λ)", "unit": "m", "var_type": "Variable", "min": 1e-9, "max": 1e-3, "default": 5e-7},
}


class VariableAnalyzer:
    """Extracts, categorizes, and bounds variables for mathematical and physical expressions."""

    @staticmethod
    def analyze_symbols(symbols: List[str], equation_raw: str = "") -> List[Dict[str, Any]]:
        """
        Analyzes a list of symbols extracted from an equation.
        Returns a list of structured variable dictionaries.
        """
        results: List[Dict[str, Any]] = []

        # Identify LHS symbol if equality is present
        lhs_symbol = ""
        if "=" in equation_raw:
            parts = equation_raw.split("=")
            lhs_clean = parts[0].strip().replace("\\", "").replace("{", "").replace("}", "")
            # Look for leading single token or variable
            m = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*)", lhs_clean)
            if m:
                lhs_symbol = m.group(1)

        for sym in symbols:
            # Check if this symbol is a fundamental scientific constant
            const_obj = get_constant_by_symbol(sym)
            if const_obj:
                results.append({
                    "symbol": sym,
                    "meaning": const_obj.name,
                    "unit": const_obj.unit,
                    "var_type": "Constant",
                    "default_val": float(const_obj.value),
                    "min_val": float(const_obj.value),
                    "max_val": float(const_obj.value),
                    "is_constant": True,
                    "reference": const_obj.reference
                })
                continue

            # Check known physical quantities
            norm_sym = sym.replace("_", "")
            base = KNOWN_QUANTITIES.get(sym) or KNOWN_QUANTITIES.get(norm_sym)

            if base:
                var_type = base["var_type"]
                # If it's on the LHS of equality, flag as Dependent quantity
                if sym == lhs_symbol:
                    var_type = "Dependent quantity"

                results.append({
                    "symbol": sym,
                    "meaning": base["meaning"],
                    "unit": base["unit"],
                    "var_type": var_type,
                    "default_val": float(base["default"]),
                    "min_val": float(base["min"]),
                    "max_val": float(base["max"]),
                    "is_constant": var_type == "Constant",
                    "reference": "Classical / Modern Physics"
                })
            else:
                # Default heuristic for unknown symbols
                is_dependent = (sym == lhs_symbol)
                results.append({
                    "symbol": sym,
                    "meaning": f"Quantity {sym}",
                    "unit": "unspecified",
                    "var_type": "Dependent quantity" if is_dependent else "Variable",
                    "default_val": 1.0,
                    "min_val": 0.0 if not is_dependent else -100.0,
                    "max_val": 10.0 if not is_dependent else 100.0,
                    "is_constant": False,
                    "reference": "Paper Definition"
                })

        return results

    @staticmethod
    def identify_dependent_independent(variables: List[Dict[str, Any]]) -> Tuple[Optional[str], List[str]]:
        """
        Determines the primary dependent variable (y-axis) and candidate independent variables (x-axis, sliders).
        """
        dependent = None
        independent: List[str] = []

        for v in variables:
            if v["var_type"] == "Dependent quantity" and not dependent:
                dependent = v["symbol"]
            elif v["var_type"] in ("Variable", "Parameter") and not v.get("is_constant"):
                independent.append(v["symbol"])

        # If no explicit dependent variable found, pick first symbol or fallback
        if not dependent and variables:
            dependent = variables[0]["symbol"]
            independent = [v["symbol"] for v in variables[1:] if not v.get("is_constant")]

        return dependent, independent
