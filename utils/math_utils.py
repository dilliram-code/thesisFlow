"""
Mathematical formatting and helper utilities for ThesisFlow.
"""

from typing import Union, Optional
import math


def format_scientific_number(val: Union[float, int], precision: int = 4) -> str:
    """Formats numbers nicely in scientific or standard decimal notation."""
    if val is None or math.isnan(val) or math.isinf(val):
        return "NaN / Undefined"

    abs_val = abs(val)
    if abs_val == 0.0:
        return "0.0"

    if abs_val >= 10000 or abs_val < 0.001:
        return f"{val:.{precision}e}"
    else:
        return f"{val:.{precision}f}".rstrip("0").rstrip(".")


def clean_latex_string(s: str) -> str:
    """Removes stray formatting artifacts for clean Streamlit st.latex rendering."""
    if not s:
        return ""
    clean = s.strip()
    if clean.startswith("$$") and clean.endswith("$$"):
        clean = clean[2:-2].strip()
    if clean.startswith("\\[") and clean.endswith("\\]"):
        clean = clean[2:-2].strip()
    if clean.startswith("$") and clean.endswith("$"):
        clean = clean[1:-1].strip()
    return clean
