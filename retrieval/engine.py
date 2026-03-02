"""Retrieval engine: finds the top-k most similar cases for a query.

Uses spaCy document vectors and cosine similarity.  Falls back to a simple
token-overlap (Jaccard) score when the spaCy model has no word vectors.
"""
from __future__ import annotations

import importlib
import math
from typing import TYPE_CHECKING

from case_base.models import Case

if TYPE_CHECKING:
    import spacy  # noqa: F401 – type-checking only

_nlp = None  # lazily loaded

# Simple in-memory vector cache: maps case_id -> vector array
# Invalidated when a new case_id is seen that isn't in the cache.
_vector_cache: dict[int, list[float]] = {}


def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy  # noqa: WPS433

        try:
            _nlp = spacy.load("en_core_web_md")
        except OSError:
            # Fallback: blank English pipeline (no vectors)
            _nlp = spacy.blank("en")
    return _nlp


# ---------------------------------------------------------------------------
# Similarity helpers
# ---------------------------------------------------------------------------

def _cosine(vec_a, vec_b) -> float:
    """Cosine similarity between two spaCy vector arrays."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def _jaccard(text_a: str, text_b: str) -> float:
    """Token-overlap Jaccard similarity used when vectors are unavailable."""
    tokens_a = set(text_a.lower().split())
    tokens_b = set(text_b.lower().split())
    if not tokens_a and not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _similarity(doc_query, doc_case, has_vectors: bool) -> float:
    if has_vectors and doc_query.has_vector and doc_case.has_vector:
        return _cosine(doc_query.vector, doc_case.vector)
    return _jaccard(doc_query.text, doc_case.text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def retrieve(query: str, cases: list[Case], top_k: int = 5) -> list[tuple[Case, float]]:
    """Return the *top_k* most similar cases sorted by descending similarity score.

    Parameters
    ----------
    query:
        The new problem description.
    cases:
        All cases in the case base.
    top_k:
        Maximum number of results to return.

    Returns
    -------
    List of ``(Case, score)`` tuples, score in ``[0.0, 1.0]``, sorted descending.
    """
    if not cases:
        return []

    nlp = _get_nlp()
    has_vectors: bool = nlp.vocab.vectors.shape[0] > 0
    disabled = [p for p in ["tagger", "parser", "ner", "lemmatizer"] if p in nlp.pipe_names]

    # Populate vector cache for any unseen cases (only cache when case_id is set)
    uncached = [c for c in cases if c.case_id is None or c.case_id not in _vector_cache]
    if uncached:
        texts = [c.problem for c in uncached]
        for case, doc in zip(uncached, nlp.pipe(texts, disable=disabled, batch_size=256)):
            vec = doc.vector.tolist() if has_vectors else doc.text
            if case.case_id is not None:
                _vector_cache[case.case_id] = vec
            # For un-keyed cases, attach vector directly on the object temporarily
            object.__setattr__(case, "_vec", vec) if hasattr(case, "__dataclass_fields__") else setattr(case, "_vec", vec)

    doc_query = nlp(query)

    scored: list[tuple[Case, float]] = []
    for case in cases:
        vec = _vector_cache.get(case.case_id) if case.case_id is not None else getattr(case, "_vec", None)
        if vec is None:
            # Fallback: compute on the fly
            doc_case = nlp(case.problem)
            vec = doc_case.vector.tolist() if has_vectors else doc_case.text
        if has_vectors:
            score = _cosine(doc_query.vector, vec)
        else:
            score = _jaccard(doc_query.text, vec)
        scored.append((case, score))

    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:top_k]
