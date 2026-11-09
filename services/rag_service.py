"""
Retrieval-Augmented Generation (RAG) Service for ThesisFlow.
Splits research documents into semantic chunks preserving page numbers, section headers,
and equation identifiers.
Implements multi-mode retrieval:
1. Lexical BM25 / TF-IDF scoring with math term boosting (zero-latency, offline-capable)
2. Semantic embedding cosine search via Gemini embeddings
"""

from typing import List, Dict, Any, Optional, Tuple
import re
import math
from collections import Counter


class RAGService:
    """Manages document chunking, indexing, and context retrieval."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # In-memory document indexes: paper_id -> List[Chunk]
        self.paper_indices: Dict[int, List[Dict[str, Any]]] = {}

    def index_paper(self, paper_id: int, pages_data: List[Dict[str, Any]], equations: Optional[List[Any]] = None):
        """
        Chunks and indexes paper pages, associating equations and section titles.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_id = 0

        # Build equation lookup by page
        eqs_by_page: Dict[int, List[str]] = {}
        if equations:
            for eq in equations:
                p_num = getattr(eq, "page_number", 1)
                eq_code = getattr(eq, "eq_id", "")
                eqs_by_page.setdefault(p_num, []).append(eq_code)

        for page in pages_data:
            page_num = page["page_number"]
            page_text = page["text"]
            blocks = page.get("blocks", [])
            page_eqs = eqs_by_page.get(page_num, [])

            current_section = "Overview"

            for block in blocks:
                b_text = block["text"].strip()
                if not b_text:
                    continue

                if block.get("is_heading"):
                    current_section = b_text
                    continue

                # Split block into sentences or chunk window
                words = b_text.split()
                if len(words) <= self.chunk_size:
                    chunk_id += 1
                    chunks.append({
                        "chunk_id": chunk_id,
                        "paper_id": paper_id,
                        "page": page_num,
                        "section": current_section,
                        "text": b_text,
                        "tokens": self._tokenize(b_text),
                        "associated_equations": page_eqs
                    })
                else:
                    # Sliding window
                    step = self.chunk_size - self.chunk_overlap
                    for start in range(0, len(words), step):
                        window = words[start:start + self.chunk_size]
                        if len(window) < 15:  # skip tiny remnants
                            continue
                        chunk_id += 1
                        sub_text = " ".join(window)
                        chunks.append({
                            "chunk_id": chunk_id,
                            "paper_id": paper_id,
                            "page": page_num,
                            "section": current_section,
                            "text": sub_text,
                            "tokens": self._tokenize(sub_text),
                            "associated_equations": page_eqs
                        })

        self.paper_indices[paper_id] = chunks

    def retrieve(self, paper_id: int, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves the top_k most relevant chunks using BM25-style lexical scoring with math term boosts.
        """
        chunks = self.paper_indices.get(paper_id, [])
        if not chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return chunks[:top_k]

        # Calculate BM25 / TF-IDF relevance
        total_docs = len(chunks)
        # Term frequencies in collection (DF)
        doc_freqs: Counter = Counter()
        for c in chunks:
            doc_freqs.update(set(c["tokens"]))

        avg_dl = sum(len(c["tokens"]) for c in chunks) / max(total_docs, 1)
        k1 = 1.5
        b = 0.75

        scored: List[Tuple[float, Dict[str, Any]]] = []

        for c in chunks:
            score = 0.0
            doc_len = len(c["tokens"])
            token_counts = Counter(c["tokens"])

            for q_tok in query_tokens:
                df = doc_freqs.get(q_tok, 0)
                if df == 0:
                    continue

                # IDF
                idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
                # TF with length normalization
                tf = token_counts.get(q_tok, 0)
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / avg_dl))
                term_score = idf * (numerator / max(denominator, 1e-6))

                # Boost if token appears in section heading or is an equation ID
                if q_tok in c["section"].lower():
                    term_score *= 1.4
                if any(q_tok == eq.lower() for eq in c.get("associated_equations", [])):
                    term_score *= 2.0

                score += term_score

            # Boost if query mentions explicit page and chunk matches page
            page_match = re.search(r"\bpage\s*(\d+)\b", query, re.I)
            if page_match and int(page_match.group(1)) == c["page"]:
                score += 5.0

            if score > 0:
                scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [item[1] for item in scored[:top_k]]

        # Fallback to initial chunks if query didn't match any token
        return top_chunks if top_chunks else chunks[:top_k]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple, fast tokenizer removing punctuation and lowering case."""
        # Retain tokens like eq-001, alpha, etc.
        tokens = re.findall(r"[a-zA-Z0-9_\-]+", text.lower())
        # Filter single char noise except significant physical variables
        return [t for t in tokens if len(t) > 1 or t in ("e", "m", "c", "f", "a", "t", "x", "v", "p")]


# Singleton RAG service instance
rag_service = RAGService()
