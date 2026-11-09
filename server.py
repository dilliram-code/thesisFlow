"""
ThesisFlow Web Server (Flask Implementation).
Serves the modern, responsive, glassy HTML5/CSS3/JS frontend
and provides RESTful APIs for PDF extraction, equation deconstruction,
RAG reasoning, and scientific computing.
"""

from pathlib import Path
import os
import json
from typing import Optional, List, Dict, Any
import io

from flask import Flask, request, jsonify, render_template, send_file, Response

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

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    template_folder=str(TEMPLATES_DIR)
)


# --- Frontend Entrypoint ---

@app.route("/")
def index():
    """Serves the glassy single-page research workspace."""
    return render_template("index.html")


# --- REST API Endpoints ---

@app.route("/api/status", methods=["GET"])
def get_system_status():
    """Returns system status, active Gemini model, and counts."""
    gemini = GeminiService()
    conn_info = gemini.is_connected()
    papers = db.get_all_papers()
    eqs = db.get_all_equations()
    exps = db.get_experiments()

    return jsonify({
        "status": "online",
        "gemini": conn_info,
        "counts": {
            "papers": len(papers),
            "equations": len(eqs),
            "experiments": len(exps),
            "constants": len(get_all_constants())
        }
    })


@app.route("/api/settings/api-key", methods=["POST"])
def update_api_key():
    """Updates the Gemini API Key dynamically."""
    data = request.get_json(silent=True) or {}
    api_key = (data.get("api_key") or "").strip()
    os.environ["GEMINI_API_KEY"] = api_key
    gemini = GeminiService(api_key=api_key)
    status = gemini.is_connected()
    return jsonify({"success": True, "connection": status})


@app.route("/api/papers", methods=["GET"])
def list_papers():
    """Lists all papers with optional query filtering."""
    search = request.args.get("search", "").strip()
    papers = db.get_all_papers()
    if search:
        q = search.lower()
        papers = [p for p in papers if q in p.title.lower() or q in p.authors.lower() or q in p.abstract.lower()]
    return jsonify([p.to_dict() for p in papers])


@app.route("/api/papers/upload", methods=["POST"])
def upload_paper():
    """Uploads, validates, and processes a research paper PDF."""
    if "file" not in request.files:
        return jsonify({"detail": "No file part in request."}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"detail": "Only PDF files are supported."}), 400

    file_bytes = file.read()
    try:
        paper, equations, msg = paper_service.process_uploaded_pdf(file_bytes, file.filename)
        return jsonify({
            "success": True,
            "paper": paper.to_dict(),
            "equations_count": len(equations),
            "message": msg
        })
    except Exception as e:
        return jsonify({"detail": str(e)}), 400


@app.route("/api/papers/reset-demos", methods=["POST"])
def reset_demo_papers():
    """Re-initializes classical physics demo papers."""
    paper_service.initialize_demo_papers_if_empty()
    papers = db.get_all_papers()
    return jsonify({"success": True, "papers_count": len(papers)})


@app.route("/api/papers/<int:paper_id>", methods=["GET"])
def get_paper(paper_id: int):
    """Gets paper by ID along with all cataloged equations."""
    paper, equations = paper_service.get_paper_with_equations(paper_id)
    if not paper:
        return jsonify({"detail": "Paper not found."}), 404

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

    return jsonify({
        "paper": paper.to_dict(),
        "equations": [e.to_dict() for e in equations],
        "pages_text": pages_text
    })


@app.route("/api/papers/<int:paper_id>", methods=["DELETE"])
def delete_paper(paper_id: int):
    """Deletes paper and all related equations and experiments."""
    success = db.delete_paper(paper_id)
    if not success:
        return jsonify({"detail": "Paper not found or already deleted."}), 404
    return jsonify({"success": True, "message": f"Paper {paper_id} deleted."})


@app.route("/api/equations", methods=["GET"])
def list_equations():
    """Lists equations with optional paper or category filtering."""
    paper_id = request.args.get("paper_id", type=int)
    category = request.args.get("category", "")

    if paper_id:
        eqs = db.get_equations_by_paper(paper_id)
    else:
        eqs = db.get_all_equations()

    if category and category != "All":
        eqs = [e for e in eqs if e.category.lower() == category.lower()]

    return jsonify([e.to_dict() for e in eqs])


@app.route("/api/equations/<int:equation_id>", methods=["GET"])
def get_equation(equation_id: int):
    """Gets single equation by ID."""
    eq = db.get_equation_by_id(equation_id)
    if not eq:
        return jsonify({"detail": "Equation not found."}), 404
    return jsonify(eq.to_dict())


@app.route("/api/equations/<int:equation_id>/deconstruct", methods=["POST"])
def deconstruct_equation_endpoint(equation_id: int):
    """Runs or fetches cached AI equation deconstruction."""
    eq = db.get_equation_by_id(equation_id)
    if not eq:
        return jsonify({"detail": "Equation not found."}), 404

    data = request.get_json(silent=True) or {}
    depth = data.get("depth_level", "Intermediate")
    paper_title = data.get("paper_title", "Research Paper")

    if eq.explanation and not data:
        return jsonify({"success": True, "explanation": eq.explanation, "cached": True})

    gemini = GeminiService()
    explanation = gemini.deconstruct_equation(
        latex=eq.latex,
        context_text=eq.context_paragraph,
        section_title=eq.section_title,
        depth_level=depth,
        paper_title=paper_title
    )

    db.update_equation_explanation(eq.id, explanation, eq.variables)
    eq.explanation = explanation

    return jsonify({"success": True, "explanation": explanation, "cached": False})


@app.route("/api/equations/code", methods=["POST"])
def generate_code_endpoint():
    """Generates Python, NumPy, SymPy, and Plotly code implementations."""
    data = request.get_json(silent=True) or {}
    latex = data.get("latex", "")
    dep_var = data.get("dependent_var", "y")
    indep_vars = data.get("independent_vars") or ["x"]
    eq_name = data.get("equation_name", "calculate_quantity")

    code_suite = CodeGenerator.generate_all_implementations(
        latex_str=latex,
        dependent_var=dep_var,
        independent_vars=indep_vars,
        equation_name=eq_name
    )
    return jsonify({"success": True, "code": code_suite})


@app.route("/api/playground/evaluate", methods=["POST"])
def evaluate_playground_grid():
    """Evaluates a formula over a 1D grid for real-time visualization."""
    data = request.get_json(silent=True) or {}
    latex = data.get("latex", "")
    indep_var = data.get("independent_var", "x")
    min_val = float(data.get("min_val", 0.1))
    max_val = float(data.get("max_val", 50.0))
    fixed_params = data.get("fixed_params", {})
    num_points = int(data.get("num_points", 200))
    target_dep = data.get("target_dep_var")

    parsed = MathematicalEngine.safe_parse(latex)
    if parsed is None:
        return jsonify({"detail": "Could not parse expression symbolically."}), 400

    x_vals, y_vals, msg = MathematicalEngine.generate_1d_grid(
        expr=parsed,
        independent_var=indep_var,
        min_val=min_val,
        max_val=max_val,
        fixed_params=fixed_params,
        num_points=num_points,
        target_dep_var=target_dep
    )

    eval_point = MathematicalEngine.evaluate_numerical_point(
        parsed,
        fixed_params,
        target_dep_var=target_dep
    )

    clean_y = [None if (val is None or val != val or abs(val) == float('inf')) else float(val) for val in y_vals]

    return jsonify({
        "success": True,
        "x": x_vals.tolist(),
        "y": clean_y,
        "operating_point_y": eval_point,
        "status_message": msg
    })


@app.route("/api/constants", methods=["GET"])
def list_constants():
    """Lists fundamental physical constants with optional filtering."""
    category = request.args.get("category", "")
    search = request.args.get("search", "")

    consts = get_all_constants()
    if category and category != "All":
        consts = [c for c in consts if c.category.lower() == category.lower()]
    if search:
        q = search.lower()
        consts = [c for c in consts if q in c.name.lower() or q in c.symbol.lower() or q in c.meaning.lower()]

    return jsonify([
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
    ])


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    """Conversational RAG query grounded in the paper."""
    data = request.get_json(silent=True) or {}
    paper_id = data.get("paper_id")
    query = data.get("query", "")
    depth = data.get("depth_level", "Intermediate")
    history = data.get("history", [])

    paper = db.get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"detail": "Paper not found."}), 404

    chunks = rag_service.retrieve(paper_id, query, top_k=4)
    gemini = GeminiService()
    reply = gemini.generate_chat_response(
        query=query,
        context_chunks=chunks,
        paper_title=paper.title,
        conversation_history=history,
        depth_level=depth
    )

    return jsonify({
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
    })


@app.route("/api/experiments", methods=["GET"])
def list_experiments():
    """Lists saved experiments."""
    eq_id = request.args.get("equation_id", type=int)
    exps = db.get_experiments(eq_id)
    return jsonify([e.to_dict() for e in exps])


@app.route("/api/experiments", methods=["POST"])
def create_experiment():
    """Saves a new experiment snapshot."""
    data = request.get_json(silent=True) or {}
    new_exp = Experiment(
        equation_id=data.get("equation_id"),
        eq_code=data.get("eq_code", ""),
        name=data.get("name", "Experiment Snapshot"),
        parameters=data.get("parameters", {}),
        results=data.get("results", {}),
        notes=data.get("notes", "")
    )
    exp_id = db.insert_experiment(new_exp)
    new_exp.id = exp_id
    return jsonify({"success": True, "experiment": new_exp.to_dict()})


@app.route("/api/reports/paper/<int:paper_id>/pdf", methods=["GET"])
def export_paper_pdf(paper_id: int):
    """Generates and downloads a complete publication-grade PDF report."""
    try:
        pdf_bytes = report_service.generate_paper_pdf_report(paper_id)
        paper = db.get_paper_by_id(paper_id)
        safe_title = (paper.title[:30] if paper else f"paper_{paper_id}").replace(" ", "_")
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"ThesisFlow_Report_{safe_title}.pdf"
        )
    except Exception as e:
        return jsonify({"detail": str(e)}), 500


@app.route("/api/reports/paper/<int:paper_id>/markdown", methods=["GET"])
def export_paper_markdown(paper_id: int):
    """Generates and downloads full paper dossier in Markdown."""
    md_text = report_service.generate_paper_full_markdown_report(paper_id)
    paper = db.get_paper_by_id(paper_id)
    safe_title = (paper.title[:30] if paper else f"paper_{paper_id}").replace(" ", "_")
    return Response(
        md_text,
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=ThesisFlow_{safe_title}.md"}
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
