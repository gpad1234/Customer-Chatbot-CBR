"""Tests for the case_base module."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Point the DB at a temp file for every test session
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["CBR_DB_PATH"] = _tmp.name

# Import after setting env var
from case_base.db import delete_case, get_all_cases, get_case, init_db, insert_case
from case_base.models import Case


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Use a fresh in-memory-like DB file for each test."""
    db_file = tmp_path / "test_cases.db"
    os.environ["CBR_DB_PATH"] = str(db_file)
    # Reload db module so it picks up the new path
    import importlib
    import case_base.db as db_mod
    importlib.reload(db_mod)
    init_db()
    yield
    importlib.reload(db_mod)  # restore after test


def _make_case(n: int = 1) -> Case:
    return Case(
        problem=f"Problem {n}",
        solution=f"Solution {n}",
        metadata={"type": "test"},
    )


def test_insert_and_get():
    cid = insert_case(_make_case(1))
    assert isinstance(cid, int) and cid > 0
    fetched = get_case(cid)
    assert fetched is not None
    assert fetched.problem == "Problem 1"
    assert fetched.solution == "Solution 1"
    assert fetched.metadata == {"type": "test"}


def test_get_missing_case():
    assert get_case(9999) is None


def test_get_all_cases():
    insert_case(_make_case(1))
    insert_case(_make_case(2))
    all_cases = get_all_cases()
    assert len(all_cases) == 2


def test_delete_case():
    cid = insert_case(_make_case(1))
    assert delete_case(cid) is True
    assert get_case(cid) is None


def test_delete_missing_case():
    assert delete_case(9999) is False
