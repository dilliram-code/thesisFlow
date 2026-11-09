"""
SQLite Database Layer for ThesisFlow.
Handles storage of papers, extracted equations, and user experiments.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import DB_PATH
from database.models import Paper, Equation, Experiment


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables with indexes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Papers table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                title TEXT NOT NULL,
                authors TEXT,
                abstract TEXT,
                total_pages INTEGER DEFAULT 1,
                uploaded_at TEXT NOT NULL,
                equations_count INTEGER DEFAULT 0,
                metadata_json TEXT DEFAULT '{}'
            )
            """)

            # Equations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS equations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eq_id TEXT NOT NULL,
                paper_id INTEGER,
                original_text TEXT NOT NULL,
                latex TEXT NOT NULL,
                page_number INTEGER DEFAULT 1,
                section_title TEXT DEFAULT 'General',
                context_paragraph TEXT,
                confidence REAL DEFAULT 1.0,
                category TEXT DEFAULT 'Algebraic',
                variables_json TEXT DEFAULT '[]',
                explanation_json TEXT DEFAULT '{}',
                is_valid INTEGER DEFAULT 1,
                sympy_expr TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
            )
            """)

            # Experiments table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equation_id INTEGER,
                eq_code TEXT,
                name TEXT NOT NULL,
                parameters_json TEXT DEFAULT '{}',
                results_json TEXT DEFAULT '{}',
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (equation_id) REFERENCES equations (id) ON DELETE CASCADE
            )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eq_paper ON equations(paper_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eq_code ON equations(eq_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_eq ON experiments(equation_id)")
            conn.commit()

    # --- Papers CRUD ---
    def insert_paper(self, paper: Paper) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO papers (filename, filepath, title, authors, abstract, total_pages, uploaded_at, equations_count, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper.filename,
                paper.filepath,
                paper.title,
                paper.authors,
                paper.abstract,
                paper.total_pages,
                paper.uploaded_at,
                paper.equations_count,
                json.dumps(paper.metadata)
            ))
            conn.commit()
            return cursor.lastrowid

    def update_paper_stats(self, paper_id: int, equations_count: int, title: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if title:
                cursor.execute("""
                    UPDATE papers SET equations_count = ?, title = ? WHERE id = ?
                """, (equations_count, title, paper_id))
            else:
                cursor.execute("""
                    UPDATE papers SET equations_count = ? WHERE id = ?
                """, (equations_count, paper_id))
            conn.commit()

    def get_all_papers(self) -> List[Paper]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers ORDER BY uploaded_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_paper(row) for row in rows]

    def get_paper_by_id(self, paper_id: int) -> Optional[Paper]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
            row = cursor.fetchone()
            return self._row_to_paper(row) if row else None

    def delete_paper(self, paper_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM experiments WHERE equation_id IN (SELECT id FROM equations WHERE paper_id = ?)", (paper_id,))
            cursor.execute("DELETE FROM equations WHERE paper_id = ?", (paper_id,))
            cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Equations CRUD ---
    def insert_equation(self, eq: Equation) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO equations (
                    eq_id, paper_id, original_text, latex, page_number,
                    section_title, context_paragraph, confidence, category,
                    variables_json, explanation_json, is_valid, sympy_expr, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                eq.eq_id,
                eq.paper_id,
                eq.original_text,
                eq.latex,
                eq.page_number,
                eq.section_title,
                eq.context_paragraph,
                eq.confidence,
                eq.category,
                json.dumps(eq.variables),
                json.dumps(eq.explanation),
                1 if eq.is_valid else 0,
                eq.sympy_expr,
                eq.created_at
            ))
            conn.commit()
            return cursor.lastrowid

    def update_equation_explanation(self, eq_id_int: int, explanation: Dict[str, Any], variables: List[Dict[str, Any]]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE equations SET explanation_json = ?, variables_json = ? WHERE id = ?
            """, (json.dumps(explanation), json.dumps(variables), eq_id_int))
            conn.commit()

    def get_equations_by_paper(self, paper_id: int) -> List[Equation]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equations WHERE paper_id = ? ORDER BY page_number ASC, id ASC", (paper_id,))
            rows = cursor.fetchall()
            return [self._row_to_equation(row) for row in rows]

    def get_equation_by_id(self, equation_id: int) -> Optional[Equation]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equations WHERE id = ?", (equation_id,))
            row = cursor.fetchone()
            return self._row_to_equation(row) if row else None

    def get_all_equations(self, limit: int = 200) -> List[Equation]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equations ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [self._row_to_equation(row) for row in rows]

    # --- Experiments CRUD ---
    def insert_experiment(self, exp: Experiment) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO experiments (equation_id, eq_code, name, parameters_json, results_json, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                exp.equation_id,
                exp.eq_code,
                exp.name,
                json.dumps(exp.parameters),
                json.dumps(exp.results),
                exp.notes,
                exp.created_at
            ))
            conn.commit()
            return cursor.lastrowid

    def get_experiments(self, equation_id: Optional[int] = None) -> List[Experiment]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if equation_id:
                cursor.execute("SELECT * FROM experiments WHERE equation_id = ? ORDER BY created_at DESC", (equation_id,))
            else:
                cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_experiment(row) for row in rows]

    # --- Helpers ---
    @staticmethod
    def _row_to_paper(row: sqlite3.Row) -> Paper:
        meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
        return Paper(
            id=row["id"],
            filename=row["filename"],
            filepath=row["filepath"],
            title=row["title"],
            authors=row["authors"] or "Unknown",
            abstract=row["abstract"] or "",
            total_pages=row["total_pages"],
            uploaded_at=row["uploaded_at"],
            equations_count=row["equations_count"],
            metadata=meta
        )

    @staticmethod
    def _row_to_equation(row: sqlite3.Row) -> Equation:
        variables = json.loads(row["variables_json"]) if row["variables_json"] else []
        explanation = json.loads(row["explanation_json"]) if row["explanation_json"] else {}
        return Equation(
            id=row["id"],
            eq_id=row["eq_id"],
            paper_id=row["paper_id"],
            original_text=row["original_text"],
            latex=row["latex"],
            page_number=row["page_number"],
            section_title=row["section_title"] or "General",
            context_paragraph=row["context_paragraph"] or "",
            confidence=row["confidence"],
            category=row["category"],
            variables=variables,
            explanation=explanation,
            is_valid=bool(row["is_valid"]),
            sympy_expr=row["sympy_expr"] or "",
            created_at=row["created_at"]
        )

    @staticmethod
    def _row_to_experiment(row: sqlite3.Row) -> Experiment:
        params = json.loads(row["parameters_json"]) if row["parameters_json"] else {}
        results = json.loads(row["results_json"]) if row["results_json"] else {}
        return Experiment(
            id=row["id"],
            equation_id=row["equation_id"],
            eq_code=row["eq_code"] or "",
            name=row["name"],
            parameters=params,
            results=results,
            notes=row["notes"] or "",
            created_at=row["created_at"]
        )


# Singleton database instance
db = Database()
