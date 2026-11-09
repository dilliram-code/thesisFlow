"""
Comprehensive Scientific Report Generation Service for ThesisFlow.
Synthesizes publication-grade PDF and Markdown analysis reports for research papers
using ReportLab and structured formatting.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

from database.models import Paper, Equation, Experiment
from database.db import db
from core.mathematical_engine import MathematicalEngine


class ReportService:
    """Generates complete PDF and Markdown research reports for ingested papers."""

    @staticmethod
    def generate_paper_pdf_report(paper_id: int) -> bytes:
        """
        Creates a multi-page, publication-grade PDF report summarizing the paper,
        all cataloged equations, variable dictionaries, and experiment snapshots.
        """
        paper = db.get_paper_by_id(paper_id)
        if not paper:
            raise ValueError(f"Paper with ID {paper_id} not found.")

        equations = db.get_equations_by_paper(paper_id)
        experiments = db.get_experiments()
        paper_experiments = [exp for exp in experiments if exp.eq_code and any(exp.eq_code == eq.latex for eq in equations)]

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0A0E1A"),
            alignment=0,
            spaceAfter=8
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=15
        )
        h1_style = ParagraphStyle(
            "Heading1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=14,
            spaceAfter=6
        )
        h2_style = ParagraphStyle(
            "Heading2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6
        )
        math_style = ParagraphStyle(
            "MathCode",
            parent=styles["Code"],
            fontName="Courier-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0284C7"),
            spaceBefore=4,
            spaceAfter=6
        )

        elements = []

        # --- 1. Document Header Banner ---
        elements.append(Paragraph("ThesisFlow Academic Research Deconstruction Report", subtitle_style))
        elements.append(Paragraph(paper.title, title_style))
        elements.append(Paragraph(f"<b>Author(s):</b> {paper.authors} &nbsp;|&nbsp; <b>Pages:</b> {paper.total_pages} &nbsp;|&nbsp; <b>Report Date:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
        elements.append(Spacer(1, 10))

        # --- 2. Paper Abstract ---
        elements.append(Paragraph("1. Document Abstract", h1_style))
        abstract_text = paper.abstract or "No explicit abstract recorded."
        elements.append(Paragraph(abstract_text, body_style))
        elements.append(Spacer(1, 10))

        # --- 3. Cataloged Equations Summary Table ---
        elements.append(Paragraph(f"2. Catalog of Mathematical Formulations ({len(equations)} Detected)", h1_style))

        if equations:
            table_data = [["ID", "LaTeX Expression", "Category", "Page", "Confidence"]]
            for eq in equations:
                latex_snippet = (eq.latex[:45] + "...") if len(eq.latex) > 45 else eq.latex
                table_data.append([
                    eq.eq_id,
                    latex_snippet,
                    eq.category,
                    str(eq.page_number),
                    f"{int(eq.confidence * 100)}%"
                ])

            summary_table = Table(table_data, colWidths=[55, 240, 110, 45, 65])
            summary_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]))
            elements.append(summary_table)
        else:
            elements.append(Paragraph("No equations detected in document.", body_style))

        elements.append(Spacer(1, 15))

        # --- 4. Detailed Equation Deconstructions ---
        elements.append(Paragraph("3. Detailed Equation Deconstruction & Variables", h1_style))

        for idx, eq in enumerate(equations, 1):
            eq_elements = []
            eq_elements.append(Paragraph(f"3.{idx} [{eq.eq_id}] {eq.section_title} (Page {eq.page_number})", h2_style))
            eq_elements.append(Paragraph(f"Formula: {eq.latex}", math_style))

            expl = eq.explanation or {}
            plain_text = expl.get("plain_language_explanation", "Mathematical formulation governing system behavior.")
            eq_elements.append(Paragraph(f"<b>Intuitive Meaning:</b> {plain_text}", body_style))

            # Variables table
            vars_list = eq.variables or []
            if vars_list:
                var_table_data = [["Symbol", "Meaning", "Unit", "Type"]]
                for v in vars_list:
                    var_table_data.append([
                        v.get("symbol", ""),
                        v.get("meaning", "Variable"),
                        v.get("unit", "unspecified"),
                        v.get("var_type", "Variable")
                    ])
                v_table = Table(var_table_data, colWidths=[70, 220, 110, 110])
                v_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                eq_elements.append(v_table)

            # Limitations
            limitations = expl.get("limitations", [])
            if limitations:
                lim_text = "<b>Theoretical Limits:</b> " + "; ".join(limitations)
                eq_elements.append(Paragraph(lim_text, body_style))

            eq_elements.append(Spacer(1, 10))
            elements.append(KeepTogether(eq_elements))

        # --- 5. Experimental Snapshots Log ---
        if paper_experiments:
            elements.append(Paragraph("4. Experimental Parameter Snapshots", h1_style))
            exp_table_data = [["ID", "Name", "Formula", "Created At", "Observations"]]
            for exp in paper_experiments:
                exp_table_data.append([
                    f"EXP-{exp.id}",
                    exp.name,
                    exp.eq_code[:30],
                    exp.created_at[:10],
                    (exp.notes[:50] + "...") if exp.notes and len(exp.notes) > 50 else (exp.notes or "None")
                ])
            exp_table = Table(exp_table_data, colWidths=[55, 140, 120, 75, 125])
            exp_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#065F46")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(exp_table)

        doc.build(elements)
        return buffer.getvalue()

    @staticmethod
    def generate_paper_full_markdown_report(paper_id: int) -> str:
        """Generates a complete consolidated Markdown dossier for the entire paper."""
        paper = db.get_paper_by_id(paper_id)
        if not paper:
            return "# Error: Paper Not Found"

        equations = db.get_equations_by_paper(paper_id)
        experiments = db.get_experiments()

        lines = [
            f"# ThesisFlow Research Dossier: {paper.title}",
            f"**Author(s):** {paper.authors}",
            f"**Total Pages:** {paper.total_pages} | **Cataloged Equations:** {len(equations)}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## 1. Abstract & Scope",
            paper.abstract or "No abstract provided.",
            "",
            "## 2. Complete Catalog of Equations",
            "| ID | Formula | Category | Page | Confidence |",
            "|---|---|---|---|---|"
        ]

        for eq in equations:
            lines.append(f"| {eq.eq_id} | `${eq.latex}$` | {eq.category} | {eq.page_number} | {int(eq.confidence * 100)}% |")

        lines.extend(["", "## 3. Equation Deconstruction Deep Dives", ""])

        for eq in equations:
            expl = eq.explanation or {}
            lines.extend([
                f"### {eq.eq_id}: {eq.section_title} (Page {eq.page_number})",
                f"$${eq.latex}$$",
                "",
                f"**Plain-Language Explanation:** {expl.get('plain_language_explanation', 'Mathematical relation extracted from document.')}",
                "",
                "**Variable Breakdown:**",
                "| Symbol | Meaning | Unit | Type |",
                "|---|---|---|---|"
            ])
            for v in eq.variables or []:
                lines.append(f"| `{v.get('symbol')}` | {v.get('meaning')} | {v.get('unit')} | {v.get('var_type')} |")

            lines.extend([
                "",
                f"**Physical Intuition:** {expl.get('physical_intuition', 'Physical balance between state coordinates.')}",
                f"**Derivation:** {expl.get('derivation', '[Reconstructed Derivation] From foundational principles.')}",
                ""
            ])

        return "\n".join(lines)


# Singleton instance
report_service = ReportService()
