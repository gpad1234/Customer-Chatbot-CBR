"""Persistent storage for the CBR domain ontology as a knowledge graph.

Uses the same SQLite database as the case base (DB_PATH from case_base.db).

Two tables are created:

    kg_concepts
    ───────────
    name        – unique concept identifier  (e.g. "track_order", "ORDER")
    type        – one of: 'root' | 'category' | 'intent'
    parent      – parent concept name (NULL for root)
    label       – human-readable display name
    description – plain-text explanation

    kg_relations
    ────────────
    subject     – concept name
    predicate   – relationship type  (e.g. 'IS_A', 'BROADER_THAN')
    object      – concept name
    (composite PK on all three columns)

The tables are seeded from ontology.domain on first call to init_kg().
Subsequent calls to init_kg() are idempotent (no duplicate rows).

Public API
----------
    init_kg()                    – create tables + seed from domain
    get_concept(name)            – fetch one concept dict or None
    get_children(name)           – list child concept dicts
    get_category_for_intent(i)   – return parent category name or None
    tree_distance(a, b)          – hop count between two concepts (undirected)
    get_kg_stats()               – summary dict for health-checks / the API
"""
from __future__ import annotations

import sqlite3
from typing import Any

from case_base.db import DB_PATH, _connect  # reuse the same connection helper

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_CREATE_CONCEPTS = """
CREATE TABLE IF NOT EXISTS kg_concepts (
    name        TEXT PRIMARY KEY,
    type        TEXT NOT NULL CHECK(type IN ('root','category','intent')),
    parent      TEXT REFERENCES kg_concepts(name),
    label       TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);
"""

_CREATE_RELATIONS = """
CREATE TABLE IF NOT EXISTS kg_relations (
    subject   TEXT NOT NULL REFERENCES kg_concepts(name),
    predicate TEXT NOT NULL,
    object    TEXT NOT NULL REFERENCES kg_concepts(name),
    PRIMARY KEY (subject, predicate, object)
);
"""

# ---------------------------------------------------------------------------
# Initialisation & seeding
# ---------------------------------------------------------------------------

def init_kg() -> None:
    """Create knowledge-graph tables and seed from the domain ontology.

    Safe to call multiple times — uses INSERT OR IGNORE so existing rows
    are never overwritten.
    """
    from ontology.domain import (
        ROOT,
        ONTOLOGY,
        CATEGORY_DESCRIPTIONS,
        INTENT_DESCRIPTIONS,
    )

    with _connect() as conn:
        conn.execute(_CREATE_CONCEPTS)
        conn.execute(_CREATE_RELATIONS)

        # Root concept
        conn.execute(
            "INSERT OR IGNORE INTO kg_concepts (name, type, parent, label, description) "
            "VALUES (?, 'root', NULL, ?, ?)",
            (ROOT, "Customer Support Issue", "Top-level concept for all customer support enquiries."),
        )

        for category, intents in ONTOLOGY.items():
            label = category.replace("_", " ").title()
            desc = CATEGORY_DESCRIPTIONS.get(category, "")
            # Category concept
            conn.execute(
                "INSERT OR IGNORE INTO kg_concepts (name, type, parent, label, description) "
                "VALUES (?, 'category', ?, ?, ?)",
                (category, ROOT, label, desc),
            )
            # IS_A relation: category IS_A root
            conn.execute(
                "INSERT OR IGNORE INTO kg_relations (subject, predicate, object) VALUES (?, 'IS_A', ?)",
                (category, ROOT),
            )
            # BROADER_THAN relation: root BROADER_THAN category
            conn.execute(
                "INSERT OR IGNORE INTO kg_relations (subject, predicate, object) VALUES (?, 'BROADER_THAN', ?)",
                (ROOT, category),
            )

            for intent in intents:
                label_i = intent.replace("_", " ").title()
                desc_i = INTENT_DESCRIPTIONS.get(intent, "")
                # Intent concept
                conn.execute(
                    "INSERT OR IGNORE INTO kg_concepts (name, type, parent, label, description) "
                    "VALUES (?, 'intent', ?, ?, ?)",
                    (intent, category, label_i, desc_i),
                )
                # IS_A relation: intent IS_A category
                conn.execute(
                    "INSERT OR IGNORE INTO kg_relations (subject, predicate, object) VALUES (?, 'IS_A', ?)",
                    (intent, category),
                )
                # BROADER_THAN relation: category BROADER_THAN intent
                conn.execute(
                    "INSERT OR IGNORE INTO kg_relations (subject, predicate, object) VALUES (?, 'BROADER_THAN', ?)",
                    (category, intent),
                )


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_concept(name: str) -> dict[str, Any] | None:
    """Return a concept row as a dict, or None if not found."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT name, type, parent, label, description FROM kg_concepts WHERE name = ?",
            (name,),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def get_children(name: str) -> list[dict[str, Any]]:
    """Return all direct children of a concept."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT name, type, parent, label, description FROM kg_concepts WHERE parent = ?",
            (name,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_category_for_intent(intent: str) -> str | None:
    """Return the parent category name for an intent, or None if not in the KG.

    Falls back to the in-memory INTENT_TO_CATEGORY dict for performance
    (avoids a DB round-trip on every retrieval call).
    """
    from ontology.domain import INTENT_TO_CATEGORY
    return INTENT_TO_CATEGORY.get(intent)


def tree_distance(concept_a: str, concept_b: str) -> int | None:
    """Return the undirected hop count between two concepts in the KG tree.

    Returns
    -------
    int
        0  – same concept
        1  – direct parent/child
        2  – siblings (same parent)
        3  – uncle/nephew
        4  – cousins (different category subtrees)
    None
        Either concept is not in the ontology.
    """
    from ontology.domain import INTENT_TO_CATEGORY, ALL_CATEGORIES, ROOT

    if concept_a == concept_b:
        return 0

    def _type(name: str) -> str:
        if name == ROOT:
            return "root"
        if name in ALL_CATEGORIES:
            return "category"
        if name in INTENT_TO_CATEGORY:
            return "intent"
        return "unknown"

    def _parent(name: str) -> str | None:
        if name == ROOT:
            return None
        if name in ALL_CATEGORIES:
            return ROOT
        return INTENT_TO_CATEGORY.get(name)

    type_a, type_b = _type(concept_a), _type(concept_b)
    if "unknown" in (type_a, type_b):
        return None

    # Build ancestor chains
    def _ancestors(name: str) -> list[str]:
        chain: list[str] = []
        current: str | None = name
        while current is not None:
            chain.append(current)
            current = _parent(current)
        return chain

    chain_a = _ancestors(concept_a)
    chain_b = _ancestors(concept_b)

    # Find lowest common ancestor
    set_b = {n: i for i, n in enumerate(chain_b)}
    for depth_a, node in enumerate(chain_a):
        if node in set_b:
            return depth_a + set_b[node]

    return None  # should never reach here in a valid tree


# ---------------------------------------------------------------------------
# Health / stats
# ---------------------------------------------------------------------------

def get_kg_stats() -> dict[str, int]:
    """Return a summary of the knowledge graph (concept and relation counts)."""
    with _connect() as conn:
        try:
            n_concepts = conn.execute("SELECT COUNT(*) FROM kg_concepts").fetchone()[0]
            n_intents = conn.execute(
                "SELECT COUNT(*) FROM kg_concepts WHERE type = 'intent'"
            ).fetchone()[0]
            n_categories = conn.execute(
                "SELECT COUNT(*) FROM kg_concepts WHERE type = 'category'"
            ).fetchone()[0]
            n_relations = conn.execute("SELECT COUNT(*) FROM kg_relations").fetchone()[0]
        except sqlite3.OperationalError:
            return {"concepts": 0, "categories": 0, "intents": 0, "relations": 0}
    return {
        "concepts": n_concepts,
        "categories": n_categories,
        "intents": n_intents,
        "relations": n_relations,
    }
