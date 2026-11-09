"""
File management and export utilities for ThesisFlow.
"""

from pathlib import Path
import csv
import io
from typing import List, Dict, Any


def generate_csv_from_grid(x_vals: List[float], y_vals: List[float], x_label: str, y_label: str) -> str:
    """Generates a downloadable CSV string from 1D grid data."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([x_label, y_label])
    for x, y in zip(x_vals, y_vals):
        writer.writerow([x, y])
    return output.getvalue()


def load_custom_css(css_path: Path) -> str:
    """Reads CSS content if present."""
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            return f"<style>{f.read()}</style>"
    return ""
