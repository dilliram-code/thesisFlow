"""
Mathematical Computation Engine for ThesisFlow.
Integrates SymPy, NumPy, and SciPy for symbolic and numerical physics calculations.
Adheres strictly to safe AST / SymPy parsing with zero execution of arbitrary code.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import re
import math
import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

# Allowed safe mathematical functions for SymPy parsing
SAFE_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

SAFE_LOCALS = {
    # Constants
    "pi": sp.pi,
    "E": sp.E,
    "oo": sp.oo,
    "I": sp.I,
    # Functions
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "Abs": sp.Abs,
    "gamma": sp.gamma,
    "erf": sp.erf,
    "erfc": sp.erfc,
}


class MathematicalEngine:
    """Safe, high-performance symbolic and numerical mathematical engine."""

    @staticmethod
    def clean_latex_to_sympy_string(latex_str: str) -> str:
        """
        Transforms common LaTeX mathematical syntax into clean SymPy-parseable string.
        Does not execute any code.
        """
        if not latex_str:
            return ""

        s = latex_str.strip()
        # Remove LaTeX equation delimiters
        s = re.sub(r"^\$\$|\$\$$|^\\\[|\\\]$|^\$|\$$", "", s)
        s = re.sub(r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}", r"\1", s, flags=re.DOTALL)
        s = re.sub(r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}", r"\1", s, flags=re.DOTALL)

        # Standard LaTeX command replacements
        s = s.replace(r"\left", "").replace(r"\right", "")
        s = s.replace(r"\cdot", "*").replace(r"\times", "*")
        s = s.replace(r"\hbar", "hbar")
        s = s.replace(r"\omega", "omega").replace(r"\nu", "nu").replace(r"\phi", "phi")
        s = s.replace(r"\alpha", "alpha").replace(r"\beta", "beta").replace(r"\gamma", "gamma")
        s = s.replace(r"\sigma", "sigma").replace(r"\mu", "mu").replace(r"\lambda", "lambda_sym")
        s = s.replace(r"\theta", "theta").replace(r"\pi", "pi").replace(r"\tau", "tau")
        s = s.replace(r"\psi", "psi").replace(r"\Delta", "Delta")

        # Fractions: \frac{a}{b} -> ((a)/(b))
        # Handle nested fractions iteratively
        for _ in range(4):
            s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"((\1)/(\2))", s)

        # Square roots: \sqrt{a} -> sqrt(a)
        for _ in range(3):
            s = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", s)

        # Powers: x^{2} -> x**(2)
        s = re.sub(r"\^\{([^{}]+)\}", r"**(\1)", s)
        s = re.sub(r"\^([a-zA-Z0-9])", r"**(\1)", s)

        # Subscripts: m_1 -> m_1, a_{eff} -> a_eff
        s = re.sub(r"\_\{([^{}]+)\}", r"_\1", s)

        # Functions
        s = re.sub(r"\\(sin|cos|tan|exp|ln|log|sinh|cosh|tanh)\b", r"\1", s)
        s = s.replace(r"\ln", "ln")

        # Remove extra whitespace
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def safe_parse(expr_str: str) -> Optional[Union[sp.Expr, sp.Equality]]:
        """
        Safely parses an algebraic expression or equality using SymPy with strict AST transformations.
        Rejects suspicious tokens or Python code injection attempts.
        """
        if not expr_str or not isinstance(expr_str, str):
            return None

        # Injection prevention: block suspicious keywords
        forbidden = [
            "__", "import", "eval", "exec", "globals", "locals", "sys", "os", "subprocess",
            "open", "compile", "builtins", "getattr", "setattr", "delattr", "read", "write"
        ]
        lowered = expr_str.lower()
        if any(term in lowered for term in forbidden):
            raise ValueError("Forbidden token detected in mathematical expression.")

        # Pre-clean latex
        cleaned = MathematicalEngine.clean_latex_to_sympy_string(expr_str)

        # Check if it is an equality e.g. "E = m * c**2"
        if "=" in cleaned:
            parts = cleaned.split("=")
            if len(parts) == 2:
                try:
                    lhs = parse_expr(parts[0].strip(), transformations=SAFE_TRANSFORMATIONS, local_dict=SAFE_LOCALS)
                    rhs = parse_expr(parts[1].strip(), transformations=SAFE_TRANSFORMATIONS, local_dict=SAFE_LOCALS)
                    return sp.Eq(lhs, rhs)
                except Exception:
                    pass

        try:
            return parse_expr(cleaned, transformations=SAFE_TRANSFORMATIONS, local_dict=SAFE_LOCALS)
        except Exception:
            return None

    @staticmethod
    def extract_symbols(expr: Union[sp.Expr, sp.Equality]) -> List[str]:
        """Returns sorted list of free symbol names in the expression."""
        if expr is None:
            return []
        if isinstance(expr, sp.Equality):
            symbols = expr.lhs.free_symbols.union(expr.rhs.free_symbols)
        else:
            symbols = expr.free_symbols
        return sorted([str(s) for s in symbols])

    @staticmethod
    def simplify_expression(expr: sp.Expr) -> str:
        """Returns simplified symbolic string and LaTeX."""
        if expr is None:
            return ""
        try:
            simplified = sp.simplify(expr)
            return sp.latex(simplified)
        except Exception:
            return sp.latex(expr)

    @staticmethod
    def differentiate(expr: sp.Expr, var_name: str, order: int = 1) -> Tuple[str, str]:
        """
        Differentiates with respect to var_name.
        Returns (sympy_str, latex_str).
        """
        var = sp.Symbol(var_name)
        res = sp.diff(expr, var, order)
        return str(res), sp.latex(res)

    @staticmethod
    def integrate(expr: sp.Expr, var_name: str, lower: Optional[float] = None, upper: Optional[float] = None) -> Tuple[str, str]:
        """
        Computes indefinite or definite integral with respect to var_name.
        """
        var = sp.Symbol(var_name)
        if lower is not None and upper is not None:
            res = sp.integrate(expr, (var, lower, upper))
        else:
            res = sp.integrate(expr, var)
        return str(res), sp.latex(res)

    @staticmethod
    def compute_taylor_series(expr: sp.Expr, var_name: str, point: float = 0.0, order: int = 4) -> Tuple[str, str]:
        """Computes Taylor/Maclaurin series expansion."""
        var = sp.Symbol(var_name)
        series_res = sp.series(expr, var, point, order).removeO()
        return str(series_res), sp.latex(series_res)

    @staticmethod
    def solve_for_symbol(equality_or_expr: Union[sp.Equality, sp.Expr], target_symbol: str) -> List[str]:
        """Solves equation for the given target symbol."""
        target = sp.Symbol(target_symbol)
        try:
            if isinstance(equality_or_expr, sp.Equality):
                solutions = sp.solve(equality_or_expr, target)
            else:
                solutions = sp.solve(equality_or_expr, target)
            return [sp.latex(sol) for sol in solutions]
        except Exception as e:
            return [f"Could not solve symbolically: {str(e)}"]

    @staticmethod
    def evaluate_numerical_point(
        expr: Union[sp.Expr, sp.Equality],
        param_values: Dict[str, float],
        target_dep_var: Optional[str] = None
    ) -> Optional[float]:
        """
        Evaluates a single numerical point. If expr is an Equality, evaluates the RHS
        or solves for target_dep_var.
        """
        try:
            target_expr = expr
            if isinstance(expr, sp.Equality):
                if target_dep_var and str(expr.lhs) == target_dep_var:
                    target_expr = expr.rhs
                elif target_dep_var and str(expr.rhs) == target_dep_var:
                    target_expr = expr.lhs
                else:
                    target_expr = expr.rhs

            sub_dict = {sp.Symbol(k): v for k, v in param_values.items()}
            val = float(target_expr.evalf(subs=sub_dict))
            return val if not (math.isnan(val) or math.isinf(val)) else None
        except Exception:
            return None

    @staticmethod
    def generate_1d_grid(
        expr: Union[sp.Expr, sp.Equality],
        independent_var: str,
        min_val: float,
        max_val: float,
        fixed_params: Dict[str, float],
        num_points: int = 200,
        target_dep_var: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray, str]:
        """
        Generates clean, safe evaluation points (x_vals, y_vals, status_message) for plotting.
        """
        if min_val >= max_val:
            max_val = min_val + 10.0

        x_vals = np.linspace(min_val, max_val, num_points)

        # Identify target expression
        eval_expr = expr
        if isinstance(expr, sp.Equality):
            if target_dep_var and str(expr.lhs) == target_dep_var:
                eval_expr = expr.rhs
            elif target_dep_var and str(expr.rhs) == target_dep_var:
                eval_expr = expr.lhs
            else:
                eval_expr = expr.rhs

        indep_sym = sp.Symbol(independent_var)
        sub_dict = {sp.Symbol(k): v for k, v in fixed_params.items() if k != independent_var}

        try:
            # Substitute fixed parameters symbolically first
            partially_subbed = eval_expr.subs(sub_dict)
            free = partially_subbed.free_symbols

            if indep_sym not in free and len(free) == 0:
                # Constant expression
                const_val = float(partially_subbed.evalf())
                y_vals = np.full_like(x_vals, const_val)
                return x_vals, y_vals, "Constant value across domain"

            # Create fast numpy lambdified function
            f_lambdified = sp.lambdify(indep_sym, partially_subbed, modules=["numpy", "scipy"])
            y_raw = f_lambdified(x_vals)

            # Convert to numpy array safely
            if np.isscalar(y_raw):
                y_vals = np.full_like(x_vals, float(y_raw))
            else:
                y_vals = np.array(y_raw, dtype=float)

            # Filter infinite/unstable values
            y_vals = np.where(np.isinf(y_vals) | np.isnan(y_vals), np.nan, y_vals)
            return x_vals, y_vals, "Success"
        except Exception as e:
            # Fallback point-by-point evaluation
            y_list = []
            for x in x_vals:
                point_params = dict(fixed_params)
                point_params[independent_var] = float(x)
                val = MathematicalEngine.evaluate_numerical_point(eval_expr, point_params)
                y_list.append(val if val is not None else np.nan)
            return x_vals, np.array(y_list, dtype=float), f"Point-by-point fallback: {str(e)}"
