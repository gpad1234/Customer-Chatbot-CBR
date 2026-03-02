"""Tests for the adaptation module."""
from __future__ import annotations

from case_base.models import Case
from adaptation.adapter import adapt


def test_adapt_strips_placeholders():
    case = Case(
        problem="I need a refund",
        solution="Please visit {{Website URL}} to request a refund of {{Money Amount}}.",
        metadata={},
    )
    result = adapt("I need a refund", case)
    assert "{{" not in result
    assert "}}" not in result


def test_adapt_replaces_order_number():
    case = Case(
        problem="Cancel order ORD-1111",
        solution="We have cancelled order ORD-1111 for you.",
        metadata={},
    )
    result = adapt("Please cancel order ORD-9999", case)
    assert "ORD-9999" in result


def test_adapt_returns_string():
    case = Case(problem="A problem", solution="A solution", metadata={})
    result = adapt("A new problem", case)
    assert isinstance(result, str)
