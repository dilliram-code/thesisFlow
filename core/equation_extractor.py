"""
Equation Extraction Module for ThesisFlow.
Extracts mathematical expressions, display equations, numbered formulations,
and physics relations from document pages.
Assigns unique IDs (EQ-001, EQ-002, ...) and contextualizes with surrounding paragraphs.
"""

from typing import List, Dict, Any, Optional
import re
from database.models import Equation
from core.equation_validator import EquationValidator
from core.variable_analyzer import VariableAnalyzer
from core.mathematical_engine import MathematicalEngine


class EquationExtractor:
    """Intelligent mathematical formula extractor."""

    @staticmethod
    def extract_from_pages(pages_data: List[Dict[str, Any]], paper_id: Optional[int] = None) -> List[Equation]:
        """
        Processes parsed pages and returns a list of uniquely identified Equation objects.
        """
        extracted_equations: List[Equation] = []
        seen_formulas = set()
        eq_counter = 1

        for page in pages_data:
            page_num = page["page_number"]
            page_text = page["text"]
            blocks = page.get("blocks", [])

            # Current section context
            current_section = "Introduction / Overview"

            for block in blocks:
                b_text = block["text"]
                if block.get("is_heading"):
                    current_section = b_text.strip()
                    continue

                # 1. Check for LaTeX environments ($$, \[, \begin{equation})
                latex_matches = EquationExtractor._find_latex_blocks(b_text)
                for formula in latex_matches:
                    normalized = EquationExtractor._normalize_formula(formula)
                    if normalized and normalized not in seen_formulas and len(normalized) > 2:
                        seen_formulas.add(normalized)
                        eq_obj = EquationExtractor._create_equation_object(
                            eq_id=f"EQ-{eq_counter:03d}",
                            paper_id=paper_id,
                            raw_text=formula,
                            latex=normalized,
                            page_number=page_num,
                            section_title=current_section,
                            context=b_text
                        )
                        extracted_equations.append(eq_obj)
                        eq_counter += 1

                # 2. Check for numbered equations e.g. "F = m a   (1)" or "(2) E = \hbar \omega"
                numbered_matches = EquationExtractor._find_numbered_equations(b_text)
                for formula, num_tag in numbered_matches:
                    normalized = EquationExtractor._normalize_formula(formula)
                    if normalized and normalized not in seen_formulas and len(normalized) > 2:
                        seen_formulas.add(normalized)
                        eq_obj = EquationExtractor._create_equation_object(
                            eq_id=f"EQ-{eq_counter:03d}",
                            paper_id=paper_id,
                            raw_text=f"{formula} ({num_tag})",
                            latex=normalized,
                            page_number=page_num,
                            section_title=current_section,
                            context=b_text
                        )
                        extracted_equations.append(eq_obj)
                        eq_counter += 1

                # 3. Check for standalone mathematical lines with math operators
                math_lines = EquationExtractor._find_standalone_math_lines(b_text)
                for formula in math_lines:
                    normalized = EquationExtractor._normalize_formula(formula)
                    if normalized and normalized not in seen_formulas and len(normalized) > 2:
                        seen_formulas.add(normalized)
                        eq_obj = EquationExtractor._create_equation_object(
                            eq_id=f"EQ-{eq_counter:03d}",
                            paper_id=paper_id,
                            raw_text=formula,
                            latex=normalized,
                            page_number=page_num,
                            section_title=current_section,
                            context=b_text
                        )
                        extracted_equations.append(eq_obj)
                        eq_counter += 1

        return extracted_equations

    @staticmethod
    def _create_equation_object(
        eq_id: str,
        paper_id: Optional[int],
        raw_text: str,
        latex: str,
        page_number: int,
        section_title: str,
        context: str
    ) -> Equation:
        # Validate through SymPy
        val_report = EquationValidator.validate(latex)

        # Extract symbols
        symbols = []
        try:
            parsed = MathematicalEngine.safe_parse(latex)
            if parsed is not None:
                symbols = MathematicalEngine.extract_symbols(parsed)
        except Exception:
            pass

        # If no symbols found via AST, fallback to regex symbol scanner
        if not symbols:
            tokens = re.findall(r"\\[a-zA-Z]+|[a-zA-Z](?:_[a-zA-Z0-9]+)?", latex)
            ignore = {"frac", "sqrt", "sin", "cos", "tan", "exp", "ln", "log", "int", "sum", "partial", "cdot", "left", "right"}
            symbols = sorted(list(set([t for t in tokens if t not in ignore and len(t) <= 10])))

        # Analyze variables
        var_analysis = VariableAnalyzer.analyze_symbols(symbols, latex)

        return Equation(
            eq_id=eq_id,
            paper_id=paper_id,
            original_text=raw_text.strip(),
            latex=latex.strip(),
            page_number=page_number,
            section_title=section_title,
            context_paragraph=context.strip()[:600],
            confidence=val_report["confidence"],
            category=val_report["category"],
            variables=var_analysis,
            is_valid=val_report["is_valid"],
            sympy_expr=val_report["sympy_repr"]
        )

    @staticmethod
    def _find_latex_blocks(text: str) -> List[str]:
        matches = []
        # Display math $$ ... $$
        matches.extend(re.findall(r"\$\$(.*?)\$\$", text, flags=re.DOTALL))
        # Display math \[ ... \]
        matches.extend(re.findall(r"\\\[(.*?)\\\]", text, flags=re.DOTALL))
        # \begin{equation} ... \end{equation}
        matches.extend(re.findall(r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}", text, flags=re.DOTALL))
        # \begin{align} ... \end{align}
        matches.extend(re.findall(r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}", text, flags=re.DOTALL))
        return [m.strip() for m in matches if m.strip()]

    @staticmethod
    def _find_numbered_equations(text: str) -> List[tuple]:
        """Detects equations followed by equation numbers like '(1)', '(2.3)', '[4]'."""
        pattern = r"([^\n]{3,150}?)\s*[\(\[]\s*(\d+(?:\.\d+)?)\s*[\)\]]\s*$"
        results = []
        for line in text.split("\n"):
            line_str = line.strip()
            # Must contain an equality or math symbol
            if any(sym in line_str for sym in ["=", r"\int", r"\sum", r"\partial", r"\alpha", r"\beta", r"\gamma", r"\omega"]):
                m = re.search(pattern, line_str)
                if m:
                    formula = m.group(1).strip()
                    num = m.group(2).strip()
                    results.append((formula, num))
        return results

    @staticmethod
    def _find_standalone_math_lines(text: str) -> List[str]:
        """Detects single lines that represent standalone mathematical equations."""
        results = []
        math_indicators = ["=", r"\approx", r"\le", r"\ge", r"\sim", r"\equiv", r"\propto"]
        operator_indicators = [r"\frac", r"\sqrt", r"\int", r"\partial", r"\sum", "^2", "_i", r"\cos", r"\sin", r"\exp"]

        for line in text.split("\n"):
            l = line.strip()
            # If line has typical math characters, reasonable length, and contains equality/relation
            if 3 <= len(l) <= 120:
                has_relation = any(rel in l for rel in math_indicators)
                has_math = any(op in l for op in operator_indicators) or re.search(r"\b[a-zA-Z]\s*=\s*[a-zA-Z0-9\(\)]+", l)
                # Ensure it is not regular English prose
                words = l.split()
                english_word_count = sum(1 for w in words if len(w) > 4 and w.isalpha())
                if has_relation and (has_math or english_word_count <= 2):
                    results.append(l)
        return results

    @staticmethod
    def _normalize_formula(formula: str) -> str:
        f = formula.strip()
        # Remove trailing equation numbers e.g. (1)
        f = re.sub(r"\s*[\(\[]\s*\d+(?:\.\d+)?\s*[\)\]]\s*$", "", f)
        # Strip outer dollar signs
        f = re.sub(r"^\$+|\$+$", "", f)
        return f.strip()

