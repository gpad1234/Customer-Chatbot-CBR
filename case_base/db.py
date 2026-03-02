"""SQLite persistence for the CBR case base.

DB path is read from the environment variable CBR_DB_PATH.
Defaults to data/cases.db relative to this file's package root.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from case_base.models import Case

_DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "cases.db"
DB_PATH: Path = Path(os.environ.get("CBR_DB_PATH", str(_DEFAULT_DB)))

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS cases (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    problem  TEXT    NOT NULL,
    solution TEXT    NOT NULL,
    metadata TEXT    NOT NULL DEFAULT '{}'
);
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the cases table and the ontology knowledge graph if they do not exist."""
    with _connect() as conn:
        conn.execute(_CREATE_TABLE)
    # Initialise the ontology knowledge graph in the same DB
    try:
        from ontology.graph import init_kg
        init_kg()
    except Exception:  # pragma: no cover
        pass  # KG is optional — never block case-base startup


def insert_case(case: Case) -> int:
    """Insert a case and return its new row id."""
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO cases (problem, solution, metadata) VALUES (?, ?, ?)",
            (case.problem, case.solution, json.dumps(case.metadata)),
        )
        return cur.lastrowid  # type: ignore[return-value]


def get_case(case_id: int) -> Case | None:
    """Fetch a single case by id, or None if not found."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, problem, solution, metadata FROM cases WHERE id = ?",
            (case_id,),
        ).fetchone()
    if row is None:
        return None
    return _row_to_case(row)


def get_all_cases() -> list[Case]:
    """Return every case in the case base."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, problem, solution, metadata FROM cases"
        ).fetchall()
    return [_row_to_case(r) for r in rows]


def delete_case(case_id: int) -> bool:
    """Delete a case by id. Returns True if a row was removed."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_case(row: sqlite3.Row) -> Case:
    metadata: dict[str, Any] = json.loads(row["metadata"])
    return Case(
        case_id=row["id"],
        problem=row["problem"],
        solution=row["solution"],
        metadata=metadata,
    )
