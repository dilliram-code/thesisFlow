"""
Google Gemini AI Service for ThesisFlow.
Uses the official google-genai SDK with gemini-3.8-flash for scientific reasoning,
equation deconstruction, variable extraction, and academic tutoring.
Includes resilient fallback when offline or without an API key.
"""

from typing import Dict, Any, List, Optional
import os
import json
import time

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL


class GeminiService:
    """Manages interactions with Google Gemini API for deep scientific reasoning."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_GEMINI_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "") or GEMINI_API_KEY
        self.model = model
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initializes the official google-genai Client."""
        if GENAI_AVAILABLE and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None
        else:
            self.client = None

    def is_connected(self) -> Dict[str, Any]:
        """Checks connection status and latency."""
        if not self.api_key:
            return {"connected": False, "reason": "GEMINI_API_KEY not configured", "latency_ms": 0}
        if not GENAI_AVAILABLE:
            return {"connected": False, "reason": "google-genai SDK not installed", "latency_ms": 0}
        if not self.client:
            return {"connected": False, "reason": "Client initialization failed", "latency_ms": 0}

        try:
            start = time.time()
            # Fast ping check
            response = self.client.models.generate_content(
                model=self.model,
                contents="Ping. Respond with 'PONG'."
            )
            latency = int((time.time() - start) * 1000)
            return {"connected": True, "reason": "Operational", "latency_ms": latency, "model": self.model}
        except Exception as e:
            return {"connected": False, "reason": str(e), "latency_ms": 0}

    def deconstruct_equation(
        self,
        latex: str,
        context_text: str = "",
        section_title: str = "General",
        depth_level: str = "Intermediate",
        paper_title: str = ""
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive 8-point scientific deconstruction of an equation.
        Falls back to local heuristic/SymPy analysis if API is not connected.
        """
        if self.client and self.api_key:
            try:
                return self._call_gemini_deconstruction(latex, context_text, section_title, depth_level, paper_title)
            except Exception as e:
                # Log error and gracefully fall back to local heuristic
                fallback = self._generate_heuristic_deconstruction(latex, context_text, depth_level)
                fallback["ai_notice"] = f"Gemini API error ({str(e)}). Displaying local analytical deconstruction."
                return fallback

        # Offline / Heuristic mode
        fallback = self._generate_heuristic_deconstruction(latex, context_text, depth_level)
        fallback["ai_notice"] = "Running in offline mode. Configure GEMINI_API_KEY in the sidebar for full AI deconstruction."
        return fallback

    def _call_gemini_deconstruction(
        self,
        latex: str,
        context_text: str,
        section_title: str,
        depth_level: str,
        paper_title: str
    ) -> Dict[str, Any]:
        """Prompts Gemini with strict academic structure."""
        prompt = f"""You are a computational physicist, mathematician, and scientific paper deconstructor for the ThesisFlow academic research platform.
Analyze the following equation extracted from the research paper '{paper_title}'.

Target Equation (LaTeX):
$${latex}$$

Section: {section_title}
Context from paper:
\"\"\"{context_text}\"\"\"

Target Explanation Depth: {depth_level} (Options: Beginner, Intermediate, Advanced Mathematical, Research-level)

CRITICAL INSTRUCTIONS:
- Ground your explanation strictly in the context of the paper where applicable.
- Never invent units; if a unit is not known from SI or context, mark it as 'unspecified'.
- If the derivation is reconstructed rather than explicitly given in the paper, explicitly state: '[Reconstructed Derivation]'.
- Never assume an AI equation is mathematically equivalent to the original paper without verification.

Provide your response in JSON format with exactly the following structure:
{{
  "plain_language_explanation": "2-3 clear sentences explaining what this equation represents in simple, intuitive terms.",
  "mathematical_interpretation": {{
    "structure": "Analysis of the mathematical form and operators.",
    "relationships": "How dependent and independent variables influence each other.",
    "assumptions": "Underlying mathematical/physical assumptions.",
    "boundary_conditions": "Boundary conditions or domain limits.",
    "domain_of_applicability": "Applicable domain or coordinate system."
  }},
  "variable_breakdown": [
    {{"symbol": "x", "meaning": "Meaning", "unit": "SI unit", "type": "Variable | Constant | Dependent quantity | Parameter"}}
  ],
  "physical_intuition": "What the equation means physically with a practical real-world or theoretical analogy.",
  "derivation": "Step-by-step derivation or reconstruction.",
  "applications": [
    "Field 1 (e.g. Quantum Physics): Specific use case",
    "Field 2 (e.g. Machine Learning): Specific application"
  ],
  "limitations": [
    "Assumption or condition where this equation ceases to be valid (e.g. relativistic speeds, non-linear regime)."
  ]
}}
"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        data = json.loads(response.text)
        data["source"] = "Gemini AI"
        return data

    def _generate_heuristic_deconstruction(
        self,
        latex: str,
        context_text: str,
        depth_level: str
    ) -> Dict[str, Any]:
        """Deterministic, reliable offline deconstruction when no API key is available."""
        from core.scientific_constants import identify_constants_in_equation
        from core.equation_validator import EquationValidator

        val = EquationValidator.validate(latex)
        category = val["category"]
        constants = identify_constants_in_equation(latex)

        const_notes = ""
        if constants:
            const_notes = " Recognized physical constants: " + ", ".join([f"{c.name} ({c.symbol} = {c.value_display} {c.unit})" for c in constants]) + "."

        return {
            "plain_language_explanation": f"This mathematical relation ({category}) expresses a fundamental quantitative balance between the underlying state variables.{const_notes}",
            "mathematical_interpretation": {
                "structure": f"A {category.lower()} mathematical formulation relating independent parameters to the system's observable state.",
                "relationships": "Increases in the primary driving terms produce proportional or scaled responses in the dependent quantity.",
                "assumptions": "Standard continuum, linear, or perturbation regime as formulated in the surrounding section context.",
                "boundary_conditions": "Real domain limits; singularity points must be avoided at parameter roots.",
                "domain_of_applicability": "Classical, relativistic, or quantum domain depending on operator scale."
            },
            "variable_breakdown": [
                {"symbol": c.symbol, "meaning": c.name, "unit": c.unit, "type": "Constant"}
                for c in constants
            ],
            "physical_intuition": "The expression models how physical energy, force, or probability distributes through the system coordinates.",
            "derivation": "[Reconstructed Derivation] Originates from first principles (conservation laws or variational Euler-Lagrange equations) evaluated under the paper's specified boundary conditions.",
            "applications": [
                f"{category} systems modeling in computational physics",
                "Numerical simulation and parameter estimation in engineering"
            ],
            "limitations": [
                "Assumes ideal conditions without unmodeled dissipative or higher-order non-linear terms."
            ],
            "source": "Local Symbolic Engine"
        }

    def generate_chat_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        paper_title: str,
        conversation_history: List[Dict[str, str]],
        depth_level: str = "Intermediate"
    ) -> str:
        """Generates RAG-grounded response for the AI Research Assistant."""
        if not self.client or not self.api_key:
            return (
                "⚠️ **Gemini API Not Connected**\n\n"
                "To interactively converse with your research paper, please enter a valid Google Gemini API key in the sidebar.\n\n"
                "In offline mode, you can still explore all extracted equations, run the interactive playground, inspect scientific constants, and export Python code!"
            )

        # Build context from retrieved chunks
        formatted_context = []
        for i, chunk in enumerate(context_chunks, start=1):
            page = chunk.get("page", "?")
            sec = chunk.get("section", "General")
            text = chunk.get("text", "")
            formatted_context.append(f"[Source {i} | Page {page} | Section: {sec}]\n{text}\n")

        context_block = "\n".join(formatted_context)

        system_instruction = f"""You are the ThesisFlow AI Research Assistant for the academic paper '{paper_title}'.
Target Audience Depth: {depth_level}.

CRITICAL RESEARCH RULES:
1. Ground your answer strictly in the provided paper excerpts.
2. Prioritize the uploaded paper over general knowledge.
3. Every response MUST include page references (e.g. '[Page X]') and equation identifiers (e.g. 'EQ-001') when available.
4. If the paper does not contain the requested information, explicitly state: 'The provided paper does not contain information regarding this question.' Do not fabricate citations, equations, or experimental findings.
5. Provide beautiful LaTeX expressions for all mathematical formulations using $...$ for inline and $$...$$ for display equations.
"""

        messages = []
        # Add recent history
        for msg in conversation_history[-6:]:
            role = "user" if msg["role"] == "user" else "model"
            messages.append(f"{role.upper()}: {msg['content']}")

        messages.append(f"RELEVANT PAPER EXCERPTS:\n{context_block}")
        messages.append(f"USER QUESTION: {query}")

        full_prompt = "\n\n".join(messages)

        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.25
                )
            )
            return resp.text or "No response generated."
        except Exception as e:
            return f"❌ **Error generating response from Gemini API:** {str(e)}"

