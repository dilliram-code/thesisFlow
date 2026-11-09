"""
PDF Intelligence Parser for ThesisFlow.
Extracts structured document metadata, section headings, text chunks,
page contexts, tables, and raw mathematical occurrences using PyMuPDF and pdfplumber.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import os
import re
import pymupdf  # PyMuPDF
import pdfplumber

from config import MAX_UPLOAD_SIZE_MB, MAX_PAGES_TO_PROCESS


class PDFParser:
    """Robust PDF document processor with structural awareness."""

    @staticmethod
    def validate_pdf_file(filepath: Path) -> Tuple[bool, str]:
        """Validates file existence, format, size, and integrity."""
        if not filepath.exists():
            return False, f"File not found: {filepath.name}"

        # Size check
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if size_mb > MAX_UPLOAD_SIZE_MB:
            return False, f"File size ({size_mb:.1f} MB) exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_MB} MB."

        if not filepath.suffix.lower() == ".pdf":
            return False, "Uploaded file is not a valid PDF."

        try:
            doc = pymupdf.open(str(filepath))
            total_pages = len(doc)
            doc.close()
            if total_pages == 0:
                return False, "PDF contains zero pages or is empty."
            if total_pages > MAX_PAGES_TO_PROCESS:
                return True, f"Warning: PDF has {total_pages} pages. Only first {MAX_PAGES_TO_PROCESS} pages will be processed."
            return True, "Valid PDF document."
        except Exception as e:
            return False, f"PDF file is corrupted or unreadable: {str(e)}"

    @staticmethod
    def extract_document(filepath: Path) -> Dict[str, Any]:
        """
        Extracts document structure: title, authors, abstract, pages, sections, and metadata.
        """
        doc = pymupdf.open(str(filepath))
        total_pages = min(len(doc), MAX_PAGES_TO_PROCESS)

        pages_data: List[Dict[str, Any]] = []
        full_text_list: List[str] = []

        # Extract page by page
        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1
            text = page.get_text("text") or ""
            full_text_list.append(text)

            # Extract blocks to identify headings & paragraphs
            blocks = page.get_text("blocks") or []
            structured_blocks = []
            for b in blocks:
                # b format: (x0, y0, x1, y1, text, block_no, block_type)
                b_text = b[4].strip() if len(b) > 4 else ""
                if b_text:
                    structured_blocks.append({
                        "text": b_text,
                        "bbox": (b[0], b[1], b[2], b[3]),
                        "is_heading": PDFParser._is_likely_heading(b_text)
                    })

            # Check image/figure count
            image_list = page.get_images(full=True)

            pages_data.append({
                "page_number": page_num,
                "text": text,
                "blocks": structured_blocks,
                "figures_count": len(image_list)
            })

        doc.close()

        # Combine first 2 pages for metadata extraction (Title, Authors, Abstract)
        first_pages_text = "\n".join(full_text_list[:2]) if full_text_list else ""
        title = PDFParser._detect_title(first_pages_text, filepath.stem)
        authors = PDFParser._detect_authors(first_pages_text)
        abstract = PDFParser._detect_abstract(first_pages_text)

        # Extract tables count using pdfplumber safely
        tables_count = 0
        try:
            with pdfplumber.open(str(filepath)) as pdf:
                for p_idx in range(min(len(pdf.pages), 10)):  # sample first 10 pages
                    tables = pdf.pages[p_idx].extract_tables()
                    tables_count += len(tables) if tables else 0
        except Exception:
            pass

        return {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "total_pages": total_pages,
            "pages": pages_data,
            "tables_count": tables_count,
            "raw_text": "\n\n".join(full_text_list)
        }

    @staticmethod
    def _is_likely_heading(text: str) -> bool:
        """Heuristic for detecting section headings."""
        t = text.strip()
        if not t or len(t) > 100:
            return False
        # Numbered headings e.g. "1. Introduction", "2. Methodology", "IV. DISCUSSION"
        if re.match(r"^(\d+(\.\d+)*|[I|V|X]+\.)\s+[A-Z]", t):
            return True
        # Common standard sections
        standard = ["abstract", "introduction", "related work", "methodology", "methods", "experiments", "results", "discussion", "conclusion", "references"]
        if t.lower() in standard:
            return True
        return False

    @staticmethod
    def _detect_title(text: str, fallback_title: str) -> str:
        """Infers paper title from the top text blocks of the first page."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:8]:
            # Skip metadata headers like arXiv, DOI, Journal name
            if re.search(r"arxiv|published|journal|volume|doi:|issn|ieee|elsevier|springer", line, re.I):
                continue
            if len(line.split()) >= 3 and len(line) <= 180:
                return line
        return fallback_title.replace("_", " ").title()

    @staticmethod
    def _detect_authors(text: str) -> str:
        """Infers author names from first page text."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for i, line in enumerate(lines[1:10], start=1):
            if re.search(r"@|university|institute|department|laboratory|center|school", line, re.I):
                # The line right before affiliation is often author list
                prev_line = lines[i - 1]
                if len(prev_line.split()) <= 12 and not re.search(r"abstract|introduction", prev_line, re.I):
                    return prev_line
        return "Academic Researchers"

    @staticmethod
    def _detect_abstract(text: str) -> str:
        """Extracts the abstract paragraph."""
        m = re.search(r"(?:abstract|summary)\s*[:\-\—]?\s*(.*?)(?=\n\s*(?:1[\.\s]|introduction|keywords|i\.\s)|\Z)", text, re.I | re.DOTALL)
        if m:
            clean = re.sub(r"\s+", " ", m.group(1)).strip()
            return clean[:1200]
        return "No explicit abstract section detected in document header."
