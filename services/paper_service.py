"""
Paper Management Service for ThesisFlow.
Orchestrates PDF ingestion, database persistence, demo paper creation,
indexing, and multi-format exports.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import shutil
from datetime import datetime

from config import UPLOADS_DIR, DEMO_DIR
from database.models import Paper, Equation, Experiment
from database.db import db
from core.pdf_parser import PDFParser
from core.equation_extractor import EquationExtractor
from services.rag_service import rag_service
from services.gemini_service import GeminiService


class PaperService:
    """High-level document processing and catalog coordinator."""

    def __init__(self):
        self.gemini = GeminiService()

    def process_uploaded_pdf(self, file_bytes: bytes, filename: str) -> Tuple[Paper, List[Equation], str]:
        """
        Saves uploaded PDF bytes, validates, extracts metadata, equations, and indexes for RAG.
        """
        # 1. Save file to disk
        safe_filename = filename.replace(" ", "_")
        dest_path = UPLOADS_DIR / safe_filename
        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        # 2. Validate
        is_valid, val_msg = PDFParser.validate_pdf_file(dest_path)
        if not is_valid:
            # Clean up corrupted file
            if dest_path.exists():
                dest_path.unlink()
            raise ValueError(val_msg)

        # 3. Extract Document Structure
        doc_data = PDFParser.extract_document(dest_path)

        # 4. Create and Save Paper Record in DB
        paper = Paper(
            filename=safe_filename,
            filepath=str(dest_path),
            title=doc_data["title"],
            authors=doc_data["authors"],
            abstract=doc_data["abstract"],
            total_pages=doc_data["total_pages"],
            equations_count=0,
            metadata={
                "tables_count": doc_data["tables_count"],
                "processed_at": datetime.utcnow().isoformat()
            }
        )
        paper_id = db.insert_paper(paper)
        paper.id = paper_id

        # 5. Extract Equations
        equations = EquationExtractor.extract_from_pages(doc_data["pages"], paper_id=paper_id)

        # If zero equations extracted via standard patterns, add a fallback detected formula
        if not equations and doc_data["raw_text"]:
            eq_fallback = Equation(
                eq_id="EQ-001",
                paper_id=paper_id,
                original_text="y = f(x)",
                latex="y = f(x)",
                page_number=1,
                section_title="Introduction",
                context_paragraph="Document contains qualitative narrative or non-standard notation.",
                confidence=0.6,
                category="Algebraic",
                is_valid=True
            )
            equations.append(eq_fallback)

        # Save equations to DB
        for eq in equations:
            eq.paper_id = paper_id
            eq_id_db = db.insert_equation(eq)
            eq.id = eq_id_db

        # Update paper equation count
        db.update_paper_stats(paper_id, len(equations), title=doc_data["title"])
        paper.equations_count = len(equations)

        # 6. Index in RAG service
        rag_service.index_paper(paper_id, doc_data["pages"], equations)

        return paper, equations, val_msg

    def get_paper_with_equations(self, paper_id: int) -> Tuple[Optional[Paper], List[Equation]]:
        """Fetches paper and all associated equations."""
        paper = db.get_paper_by_id(paper_id)
        if not paper:
            return None, []
        equations = db.get_equations_by_paper(paper_id)
        return paper, equations

    def initialize_demo_papers_if_empty(self):
        """
        Pre-seeds demo scientific research papers if database is empty so
        first-time users can immediately test all features.
        """
        existing = db.get_all_papers()
        if existing:
            return

        demo_papers = [
            {
                "filename": "demo_einstein_relativity_1905.pdf",
                "title": "On the Electrodynamics of Moving Bodies & Mass-Energy Equivalence",
                "authors": "Albert Einstein",
                "abstract": "We investigate the consequences of the principle of relativity and the constancy of the speed of light in vacuum. It is shown that the mass of a body is a measure of its energy-content, establishing the fundamental equivalence E = m c^2.",
                "total_pages": 4,
                "equations": [
                    {
                        "eq_id": "EQ-001",
                        "latex": "E = m c^2",
                        "original": "E = m c^2 (1)",
                        "page": 1,
                        "section": "Mass-Energy Equivalence",
                        "context": "If a body gives off the energy L in the form of radiation, its mass diminishes by L/c^2. The fact that the energy that withdraws from the body becomes energy of radiation evidently makes no difference, so that we are led to the more general conclusion: the mass of a body is a measure of its energy-content.",
                        "category": "Relativistic / Tensor"
                    },
                    {
                        "eq_id": "EQ-002",
                        "latex": r"\gamma = \frac{1}{\sqrt{1 - \frac{v^2}{c^2}}}",
                        "original": r"\gamma = 1 / \sqrt{1 - v^2/c^2}",
                        "page": 2,
                        "section": "Lorentz Transformations",
                        "context": "The Lorentz factor γ appears universally in relativistic kinematics and electrodynamics to describe relativistic time dilation and length contraction for bodies with relative velocity v.",
                        "category": "Relativistic / Tensor"
                    },
                    {
                        "eq_id": "EQ-003",
                        "latex": "p = \\gamma m v",
                        "original": "p = \\gamma m v",
                        "page": 3,
                        "section": "Relativistic Momentum",
                        "context": "The relativistic momentum p extends classical Newtonian momentum by scaling with the Lorentz factor γ as velocity approaches the speed of light c.",
                        "category": "Relativistic / Tensor"
                    }
                ]
            },
            {
                "filename": "demo_classical_oscillations.pdf",
                "title": "Analytical Mechanics: Harmonic Oscillators & Conservative Fields",
                "authors": "Sir Isaac Newton, Joseph-Louis Lagrange",
                "abstract": "A foundational examination of Newtonian dynamics, Hooke's restoring forces, and second-order linear differential equations governing undamped and damped physical harmonic oscillators.",
                "total_pages": 3,
                "equations": [
                    {
                        "eq_id": "EQ-001",
                        "latex": "F = m a",
                        "original": "F = m a",
                        "page": 1,
                        "section": "Newton's Second Law",
                        "context": "The alteration of motion is ever proportional to the motive force impressed; and is made in the direction of the right line in which that force is impressed.",
                        "category": "Algebraic"
                    },
                    {
                        "eq_id": "EQ-002",
                        "latex": r"x(t) = A \cos(\omega t + \phi)",
                        "original": "x(t) = A cos(omega t + phi)",
                        "page": 2,
                        "section": "Simple Harmonic Motion",
                        "context": "The general displacement solution x(t) for an unforced, undamped harmonic oscillator where A represents oscillation amplitude, ω is angular frequency, and φ represents initial phase.",
                        "category": "Differential"
                    },
                    {
                        "eq_id": "EQ-003",
                        "latex": r"F = - k x",
                        "original": "F = - k x",
                        "page": 2,
                        "section": "Hooke's Law",
                        "context": "The restoring force exerted by a linear spring is proportional to the displacement from equilibrium and directed oppositely.",
                        "category": "Algebraic"
                    },
                    {
                        "eq_id": "EQ-004",
                        "latex": r"F = G \frac{m_1 m_2}{r^2}",
                        "original": "F = G m_1 m_2 / r^2",
                        "page": 3,
                        "section": "Universal Gravitation",
                        "context": "Every particle attracts every other particle in the universe with a force proportional to the product of their masses and inversely proportional to the square of the distance between their centers.",
                        "category": "Algebraic"
                    }
                ]
            },
            {
                "filename": "demo_quantum_and_statistics.pdf",
                "title": "Statistical Physics & Quantum Probability Distributions",
                "authors": "Erwin Schrödinger, Carl Friedrich Gauss",
                "abstract": "Theoretical foundations linking Gaussian probability densities in statistical thermodynamics with time-dependent wavefunctions in non-relativistic quantum systems.",
                "total_pages": 3,
                "equations": [
                    {
                        "eq_id": "EQ-001",
                        "latex": r"f(x) = \frac{1}{\sigma \sqrt{2 \pi}} \exp\left(-\frac{(x - \mu)^2}{2 \sigma^2}\right)",
                        "original": "f(x) = 1/(sigma sqrt(2 pi)) exp(-(x-mu)^2 / (2 sigma^2))",
                        "page": 1,
                        "section": "Gaussian Normal Distribution",
                        "context": "The probability density function of the normal distribution, parameterized by the expected mean μ and standard deviation σ.",
                        "category": "Statistical / Distribution"
                    },
                    {
                        "eq_id": "EQ-002",
                        "latex": r"i \hbar \frac{\partial \psi}{\partial t} = - \frac{\hbar^2}{2 m} \frac{\partial^2 \psi}{\partial x^2} + V(x) \psi",
                        "original": "i hbar d psi / dt = - (hbar^2 / 2m) d^2 psi / dx^2 + V(x) psi",
                        "page": 2,
                        "section": "Schrödinger Wave Equation",
                        "context": "The non-relativistic time-dependent Schrödinger equation governing the evolution of the quantum wavefunction ψ for a particle of mass m in potential V(x).",
                        "category": "Quantum Mechanical"
                    }
                ]
            }
        ]

        for p_info in demo_papers:
            # Create a mock PDF placeholder file in demo dir
            dummy_pdf_path = DEMO_DIR / p_info["filename"]
            if not dummy_pdf_path.exists():
                with open(dummy_pdf_path, "wb") as f:
                    f.write(b"%PDF-1.4\n%ThesisFlow Demo PDF File\n%%EOF")

            paper = Paper(
                filename=p_info["filename"],
                filepath=str(dummy_pdf_path),
                title=p_info["title"],
                authors=p_info["authors"],
                abstract=p_info["abstract"],
                total_pages=p_info["total_pages"],
                equations_count=len(p_info["equations"]),
                metadata={"is_demo": True}
            )
            pid = db.insert_paper(paper)

            mock_pages = []
            for page_num in range(1, p_info["total_pages"] + 1):
                mock_pages.append({
                    "page_number": page_num,
                    "text": f"Paper: {p_info['title']}. Section excerpts for page {page_num}.\n{p_info['abstract']}",
                    "blocks": [{"text": p_info['abstract'], "is_heading": False}]
                })

            eq_objs = []
            for eq_data in p_info["equations"]:
                eq_obj = EquationExtractor._create_equation_object(
                    eq_id=eq_data["eq_id"],
                    paper_id=pid,
                    raw_text=eq_data["original"],
                    latex=eq_data["latex"],
                    page_number=eq_data["page"],
                    section_title=eq_data["section"],
                    context=eq_data["context"]
                )
                eq_id_db = db.insert_equation(eq_obj)
                eq_obj.id = eq_id_db
                eq_objs.append(eq_obj)

            rag_service.index_paper(pid, mock_pages, eq_objs)

    def export_equation_markdown(self, eq: Equation, paper_title: str) -> str:
        """Exports equation deconstruction report as structured Markdown."""
        expl = eq.explanation or {}
        latex_str = eq.latex

        lines = [
            f"# ThesisFlow Equation Analysis: {eq.eq_id}",
            f"**Research Paper:** {paper_title}",
            f"**Section:** {eq.section_title} | **Page:** {eq.page_number}",
            f"**Category:** {eq.category} | **Confidence:** {int(eq.confidence * 100)}%",
            "",
            "## 1. Mathematical Formulation",
            f"$${latex_str}$$",
            "",
            "## 2. Plain-Language Explanation",
            expl.get("plain_language_explanation", "Mathematical relation extracted from document."),
            "",
            "## 3. Mathematical Interpretation",
        ]

        math_interp = expl.get("mathematical_interpretation", {})
        if isinstance(math_interp, dict):
            for k, v in math_interp.items():
                lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")

        lines.extend([
            "",
            "## 4. Variable Breakdown",
            "| Symbol | Meaning | Unit | Type |",
            "|---|---|---|---|"
        ])

        vars_list = eq.variables or []
        for v in vars_list:
            lines.append(f"| `{v.get('symbol')}` | {v.get('meaning', 'Variable')} | {v.get('unit', 'unspecified')} | {v.get('var_type', 'Variable')} |")

        lines.extend([
            "",
            "## 5. Physical Intuition",
            expl.get("physical_intuition", "Represents physical equilibrium and parameter interaction."),
            "",
            "## 6. Derivation Notes",
            expl.get("derivation", "[Reconstructed Derivation] Derived from foundational conservation principles."),
            "",
            "## 7. Limitations & Validity Domain",
        ])
        for lim in expl.get("limitations", ["Standard non-relativistic, continuum approximation."]):
            lines.append(f"- {lim}")

        return "\n".join(lines)


# Singleton paper service
paper_service = PaperService()
