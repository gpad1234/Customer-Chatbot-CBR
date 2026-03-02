"""CBR orchestrator: wires together retrieval and adaptation.

This module has no I/O dependency and can be exercised in tests without
starting the FastAPI server.
"""
from __future__ import annotations

from dataclasses import dataclass

from adaptation.adapter import adapt
from case_base.db import get_all_cases
from case_base.models import Case
from retrieval.engine import retrieve


@dataclass
class CBRResponse:
    """Structured response returned by the orchestrator."""

    answer: str
    matched_case: Case | None
    similarity_score: float
    top_matches: list[tuple[Case, float]]


def query(problem: str, top_k: int = 5, min_score: float = 0.0) -> CBRResponse:
    """Run the full CBR pipeline for a new customer problem.

    Parameters
    ----------
    problem:
        The incoming customer query / problem description.
    top_k:
        How many similar cases to retrieve (default 5).
    min_score:
        Minimum similarity score to accept; below this a fallback message is returned.

    Returns
    -------
    :class:`CBRResponse` with the adapted answer and retrieval metadata.
    """
    cases = get_all_cases()

    if not cases:
        return CBRResponse(
            answer="I'm sorry, I don't have enough information to help with that yet.",
            matched_case=None,
            similarity_score=0.0,
            top_matches=[],
        )

    top_matches = retrieve(problem, cases, top_k=top_k)
    best_case, best_score = top_matches[0] if top_matches else (None, 0.0)

    if best_case is None or best_score < min_score:
        return CBRResponse(
            answer="I couldn't find a close match for your issue. Please contact support directly.",
            matched_case=None,
            similarity_score=best_score,
            top_matches=top_matches,
        )

    adapted_solution = adapt(problem, best_case)

    return CBRResponse(
        answer=adapted_solution,
        matched_case=best_case,
        similarity_score=best_score,
        top_matches=top_matches,
    )
