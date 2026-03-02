"""Adaptation layer: adjusts a retrieved solution to fit a new query context.

Rules are pure functions that accept ``(query, solution, metadata)`` and
return a modified solution string.  Each rule is independently testable.
"""
from __future__ import annotations

import re
from typing import Callable

from case_base.models import Case

# ---------------------------------------------------------------------------
# Individual adaptation rules (pure functions)
# ---------------------------------------------------------------------------

def _rule_replace_product(query: str, solution: str, metadata: dict) -> str:
    """Replace the product name in the solution when the query mentions a different one."""
    source_product: str = metadata.get("Product Purchased", "")
    if not source_product:
        return solution

    # Very simple heuristic: look for a quoted or capitalised product name in the query
    # that differs from the one in the original case.
    # Real-world use: plug in an NER model here.
    return solution  # placeholder – extend with domain-specific rules


def _rule_replace_order_number(query: str, solution: str, metadata: dict) -> str:
    """Substitute order/ticket numbers found in the query into the solution."""
    order_pattern = re.compile(r"\b(?:order|ticket|ref)[\s#:]*([A-Z0-9\-]{4,})\b", re.IGNORECASE)
    query_match = order_pattern.search(query)
    solution_match = order_pattern.search(solution)
    if query_match and solution_match:
        solution = solution.replace(solution_match.group(1), query_match.group(1))
    return solution


def _rule_strip_placeholder_brackets(query: str, solution: str, metadata: dict) -> str:
    """Remove unfilled template placeholders like {{Order Number}} from the solution."""
    return re.sub(r"\{\{[^}]+\}\}", "", solution).strip()


# ---------------------------------------------------------------------------
# Rule pipeline
# ---------------------------------------------------------------------------

_RULES: list[Callable[[str, str, dict], str]] = [
    _rule_replace_product,
    _rule_replace_order_number,
    _rule_strip_placeholder_brackets,
]


def adapt(query: str, case: Case) -> str:
    """Apply all adaptation rules and return the modified solution.

    Parameters
    ----------
    query:
        The new (incoming) problem description.
    case:
        The best-matching retrieved case.

    Returns
    -------
    The adapted solution string.
    """
    solution = case.solution
    for rule in _RULES:
        solution = rule(query, solution, case.metadata)
    return solution
