"""Tests for the retrieval engine."""
from __future__ import annotations

from case_base.models import Case
from retrieval.engine import retrieve


def _cases() -> list[Case]:
    # Use high IDs to avoid colliding with the real DB vector cache
    return [
        Case(case_id=99991, problem="My order has not arrived yet", solution="Check tracking link."),
        Case(case_id=99992, problem="I cannot log in to my account", solution="Reset your password."),
        Case(case_id=99993, problem="I was charged twice for the same item", solution="Contact billing."),
    ]


def test_retrieve_returns_top_k():
    results = retrieve("where is my delivery", _cases(), top_k=2)
    assert len(results) == 2


def test_retrieve_sorted_descending():
    results = retrieve("order not delivered", _cases(), top_k=3)
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)


def test_retrieve_scores_in_range():
    results = retrieve("login problem", _cases(), top_k=3)
    for _, score in results:
        assert 0.0 <= score <= 1.0


def test_retrieve_empty_case_base():
    results = retrieve("any query", [], top_k=5)
    assert results == []


def test_retrieve_best_match():
    # "login" / "account" query should rank the account case above the order/billing cases
    results = retrieve("I cannot login to my account password forgotten", _cases(), top_k=3)
    # The account case should appear in the top 2 results
    top2_problems = [c.problem for c, _ in results[:2]]
    assert any("log in" in p or "account" in p for p in top2_problems)
