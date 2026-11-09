"""
ThesisFlow FastAPI Application Server.
Provides RESTful APIs for PDF ingestion, equation deconstruction,
RAG reasoning, symbolic calculations, and serves the modern HTML5/CSS3/JS single-page frontend.
"""

from pathlib import Path
import os
import json
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import BASE_DIR, DATA_DIR, UPLOADS_DIR, GEMINI_API_KEY, DEFAULT_GEMINI_MODEL
from database.db import db
from database.models import Paper, Equation, Experiment
from services.paper_service import paper_service
from services.gemini_service import GeminiService
from services.rag_service import rag_service
from services.report_service import report_service
from core.mathematical_engine import MathematicalEngine
from core.scientific_constants import get_all_constants, get_constant_by_symbol, identify_constants_in_equation
from core.code_generator import CodeGenerator
from core.variable_analyzer import VariableAnalyzer

# Ensure demo papers exist on startup
paper_service.initialize_demo_papers_if_empty()

app = FastAPI(
    title="ThesisFlow API",
    description="The Interactive Math & Physics Research Paper Deconstructer",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Templates Directories
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Pydantic Schemas for Requests
class DeconstructRequest(BaseModel):
    latex: str
    context_text: Optional[str] = ""
    section_title: Optional[str] = "General"
    depth_level: Optional[str] = "Intermediate"
    paper_title: Optional[str] = "Research Paper"


class CodeGenRequest(BaseModel):
    latex: str
    dependent_var: Optional[str] = "y"
    independent_vars: Optional[List[str]] = None
    equation_name: Optional[str] = "Calculated Equation"


class EvaluateGridRequest(BaseModel):
    latex: str
    independent_var: str
    min_val: float
    max_val: float
    fixed_params: Dict[str, float]
    num_points: Optional[int] = 200
    target_dep_var: Optional[str] = None


class ChatRequest(BaseModel):
    paper_id: int
    query: str
    depth_level: Optional[str] = "Intermediate"
    history: Optional[List[Dict[str, str]]] = []


class ExperimentCreate(BaseModel):
    equation_id: Optional[int] = None
    eq_code: str = ""
    name: str = "Experiment Snapshot"
    parameters: Dict[str, float] = {}
    results: Dict[str, Any] = {}
    notes: Optional[str] = ""


class ApiKeyUpdate(BaseModel):
    api_key: str


# --- API Routes ---

@app.get("/api/status")
async def get_system_status():
    """Returns system status, active Gemini model, and counts."""
    gemini = GeminiService()
    conn_info = gemini.is_connected()
    papers = db.get_all_papers()
    eqs = db.get_all_equations()
    exps = db.get_experiments()

    return {
        "status": "online",
        "gemini": conn_info,
        "counts": {
            "papers": len(papers),
            "equations": len(eqs),
            "experiments": len(exps),
            "constants": len(get_all_constants())
        }
    }


@app.post("/api/settings/api-key")
async def update_api_key(payload: ApiKeyUpdate):
    """Updates the Gemini API Key dynamically."""
    os.environ["GEMINI_API_KEY"] = payload.api_key.strip()
    gemini = GeminiService(api_key=payload.api_key.strip())
    status = gemini.is_connected()
    return {"success": True, "connection": status}


@app.get("/api/papers")
async def list_papers(search: Optional[str] = None):
    """Lists all papers with optional query filtering."""
    papers = db.get_all_papers()
    if search:
        q = search.lower()
        papers = [p for p in papers if q in p.title.lower() or q in p.authors.lower() or q in p.abstract.lower()]
    return [p.to_dict() for p in papers]


@app.post("/api/papers/upload")
async def upload_paper(file: UploadFile = File(...)):
    """Uploads, validates, and processes a research paper PDF."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    try:
        paper, equations, msg = paper_service.process_uploaded_pdf(file_bytes, file.filename)
        return {
            "success": True,
            "paper": paper.to_dict(),
            "equations_count": len(equations),
            "message": msg
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/papers/reset-demos")
async def reset_demo_papers():
    """Re-initializes classical physics demo papers."""
    paper_service.initialize_demo_papers_if_empty()
    papers = db.get_all_papers()
    return {"success": True, "papers_count": len(papers)}


@app.get("/api/papers/{paper_id}")
async def get_paper(paper_id: int):
    """Gets paper by ID along with all cataloged equations."""
    paper, equations = paper_service.get_paper_with_equations(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    # Read page text list if available
    pdf_path = Path(paper.filepath)
    pages_text = []
    if pdf_path.exists():
        try:
            import pymupdf
            doc = pymupdf.open(str(pdf_path))
            for p in doc:
                pages_text.append(p.get_text("text") or "")
            doc.close()
        except Exception:
            pass

    return {
        "paper": paper.to_dict(),
        "equations": [e.to_dict() for e in equations],
        "pages_text": pages_text
    }


@app.delete("/api/papers/{paper_id}")
async def delete_paper(paper_id: int):
    """Deletes paper and all related equations and experiments."""
    success = db.delete_paper(paper_id)
    if not success:
        raise HTTPException(status_code=404, detail="Paper not found or already deleted.")
    return {"success": True, "message": f"Paper {paper_id} deleted."}


@app.get("/api/equations")
async def list_equations(paper_id: Optional[int] = None, category: Optional[str] = None):
    """Lists equations with optional paper or category filtering."""
    if paper_id:
        eqs = db.get_equations_by_paper(paper_id)
    else:
        eqs = db.get_all_equations()

    if category and category != "All":
        eqs = [e for e in eqs if e.category.lower() == category.lower()]

    return [e.to_dict() for e in eqs]


@app.get("/api/equations/{equation_id}")
async def get_equation(equation_id: int):
    """Gets single equation by ID."""
    eq = db.get_equation_by_id(equation_id)
    if not eq:
        raise HTTPException(status_code=404, detail="Equation not found.")
    return eq.to_dict()


@app.post("/api/equations/{equation_id}/deconstruct")
async def deconstruct_equation_endpoint(equation_id: int, payload: Optional[DeconstructRequest] = None):
    """Runs or fetches cached AI equation deconstruction."""
    eq = db.get_equation_by_id(equation_id)
    if not eq:
        raise HTTPException(status_code=404, detail="Equation not found.")

    if eq.explanation and not payload:
        return {"success": True, "explanation": eq.explanation, "cached": True}

    depth = payload.depth_level if payload else "Intermediate"
    paper_title = payload.paper_title if payload else "Research Paper"

    gemini = GeminiService()
    explanation = gemini.deconstruct_equation(
        latex=eq.latex,
        context_text=eq.context_paragraph,
        section_title=eq.section_title,
        depth_level=depth,
        paper_title=paper_title
    )

    # Cache in DB
    db.update_equation_explanation(eq.id, explanation, eq.variables)
    eq.explanation = explanation

    return {"success": True, "explanation": explanation, "cached": False}


@app.post("/api/equations/code")
async def generate_code_endpoint(payload: CodeGenRequest):
    """Generates Python, NumPy, SymPy, and Plotly code implementations."""
    code_suite = CodeGenerator.generate_all_implementations(
        latex_str=payload.latex,
        dependent_var=payload.dependent_var or "y",
        independent_vars=payload.independent_vars or ["x"],
        equation_name=payload.equation_name or "calculate_quantity"
    )
    return {"success": True, "code": code_suite}


@app.post("/api/playground/evaluate")
async def evaluate_playground_grid(payload: EvaluateGridRequest):
    """Evaluates a formula over a 1D grid for real-time visualization."""
    parsed = MathematicalEngine.safe_parse(payload.latex)
    if parsed is None:
        raise HTTPException(status_code=400, detail="Could not parse expression symbolically.")

    x_vals, y_vals, msg = MathematicalEngine.generate_1d_grid(
        expr=parsed,
        independent_var=payload.independent_var,
        min_val=payload.min_val,
        max_val=payload.max_val,
        fixed_params=payload.fixed_params,
        num_points=payload.num_points or 200,
        target_dep_var=payload.target_dep_var
    )

    eval_point = MathematicalEngine.evaluate_numerical_point(
        parsed,
        payload.fixed_params,
        target_dep_var=payload.target_dep_var
    )

    # Clean NaN/Inf for JSON compliance
    clean_y = [None if (val is None or val != val or abs(val) == float('inf')) else float(val) for val in y_vals]

    return {
        "success": True,
        "x": x_vals.tolist(),
        "y": clean_y,
        "operating_point_y": eval_point,
        "status_message": msg
    }


@app.get("/api/constants")
async def list_constants(category: Optional[str] = None, search: Optional[str] = None):
    """Lists fundamental physical constants with optional filtering."""
    consts = get_all_constants()
    if category and category != "All":
        consts = [c for c in consts if c.category.lower() == category.lower()]
    if search:
        q = search.lower()
        consts = [c for c in consts if q in c.name.lower() or q in c.symbol.lower() or q in c.meaning.lower()]

    return [
        {
            "symbol": c.symbol,
            "latex_symbol": c.latex_symbol,
            "name": c.name,
            "value": c.value,
            "value_display": c.value_display,
            "uncertainty": c.uncertainty,
            "unit": c.unit,
            "dimension": c.dimension,
            "meaning": c.meaning,
            "canonical_equation": c.canonical_equation,
            "reference": c.reference,
            "category": c.category
        }
        for c in consts
    ]


@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    """Conversational RAG query grounded in the paper."""
    paper = db.get_paper_by_id(payload.paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    chunks = rag_service.retrieve(payload.paper_id, payload.query, top_k=4)
    gemini = GeminiService()
    reply = gemini.generate_chat_response(
        query=payload.query,
        context_chunks=chunks,
        paper_title=paper.title,
        conversation_history=payload.history or [],
        depth_level=payload.depth_level or "Intermediate"
    )

    return {
        "success": True,
        "response": reply,
        "citations": [
            {
                "page": c.get("page", 1),
                "section": c.get("section", "General"),
                "snippet": c.get("text", "")[:280] + "...",
                "equations": c.get("associated_equations", [])
            }
            for c in chunks
        ]
    }


@app.get("/api/experiments")
async def list_experiments(equation_id: Optional[int] = None):
    """Lists saved experiments."""
    exps = db.get_experiments(equation_id)
    return [e.to_dict() for e in exps]


@app.post("/api/experiments")
async def create_experiment(exp: ExperimentCreate):
    """Saves a new experiment snapshot."""
    new_exp = Experiment(
        equation_id=exp.equation_id,
        eq_code=exp.eq_code,
        name=exp.name,
        parameters=exp.parameters,
        results=exp.results,
        notes=exp.notes or ""
    )
    exp_id = db.insert_experiment(new_exp)
    new_exp.id = exp_id
    return {"success": True, "experiment": new_exp.to_dict()}


@app.get("/api/reports/paper/{paper_id}/pdf")
async def export_paper_pdf(paper_id: int):
    """Generates and downloads a complete publication-grade PDF report."""
    try:
        pdf_bytes = report_service.generate_paper_pdf_report(paper_id)
        paper = db.get_paper_by_id(paper_id)
        safe_title = (paper.title[:30] if paper else f"paper_{paper_id}").replace(" ", "_")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ThesisFlow_Report_{safe_title}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/paper/{paper_id}/markdown")
async def export_paper_markdown(paper_id: int):
    """Generates and downloads full paper dossier in Markdown."""
    md_text = report_service.generate_paper_full_markdown_report(paper_id)
    paper = db.get_paper_by_id(paper_id)
    safe_title = (paper.title[:30] if paper else f"paper_{paper_id}").replace(" ", "_")
    return Response(
        content=md_text,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=ThesisFlow_{safe_title}.md"}
    )


# --- Serve HTML Frontend ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main single-page web app."""
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>ThesisFlow</h1><p>Frontend template not initialized.</p>")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
