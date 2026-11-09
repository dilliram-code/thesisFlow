"""
Database models for ThesisFlow.
Defines data structures for Papers, Equations, and Experiments.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import json
from datetime import datetime


@dataclass
class VariableInfo:
    symbol: str
    meaning: str
    unit: str = "unspecified"
    var_type: str = "Variable"  # Variable, Constant, Dependent quantity, Parameter
    default_val: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None


@dataclass
class Equation:
    id: Optional[int] = None
    eq_id: str = "EQ-001"
    paper_id: Optional[int] = None
    original_text: str = ""
    latex: str = ""
    page_number: int = 1
    section_title: str = "General"
    context_paragraph: str = ""
    confidence: float = 0.95
    category: str = "Algebraic"  # Algebraic, Differential, Integral, Statistical, Quantum, Relativistic
    variables: List[Dict[str, Any]] = field(default_factory=list)
    explanation: Dict[str, Any] = field(default_factory=dict)
    is_valid: bool = True
    sympy_expr: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["variables_json"] = json.dumps(self.variables)
        d["explanation_json"] = json.dumps(self.explanation)
        return d


@dataclass
class Paper:
    id: Optional[int] = None
    filename: str = ""
    filepath: str = ""
    title: str = "Untitled Paper"
    authors: str = "Unknown"
    abstract: str = ""
    total_pages: int = 1
    uploaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    equations_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["metadata_json"] = json.dumps(self.metadata)
        return d


@dataclass
class Experiment:
    id: Optional[int] = None
    equation_id: Optional[int] = None
    eq_code: str = ""
    name: str = "Default Experiment"
    parameters: Dict[str, float] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["parameters_json"] = json.dumps(self.parameters)
        d["results_json"] = json.dumps(self.results)
        return d

