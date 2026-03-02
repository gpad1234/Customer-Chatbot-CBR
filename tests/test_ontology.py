"""Tests for the ontology layer: domain, graph persistence, and similarity."""
from __future__ import annotations

import os
import tempfile

import pytest

_t = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_t.close()
os.environ["CBR_DB_PATH"] = _t.name


# ---------------------------------------------------------------------------
# domain.py
# ---------------------------------------------------------------------------

class TestDomain:
    def test_ontology_non_empty(self):
        from ontology.domain import ONTOLOGY
        assert len(ONTOLOGY) > 0

    def test_all_categories_have_intents(self):
        from ontology.domain import ONTOLOGY
        for cat, intents in ONTOLOGY.items():
            assert len(intents) > 0, f"{cat} has no intents"

    def test_intent_to_category_lookup(self):
        from ontology.domain import INTENT_TO_CATEGORY, ONTOLOGY
        for category, intents in ONTOLOGY.items():
            for intent in intents:
                assert INTENT_TO_CATEGORY[intent] == category

    def test_weights_sum_to_one(self):
        from ontology.domain import SIMILARITY_WEIGHTS
        assert abs(sum(SIMILARITY_WEIGHTS.values()) - 1.0) < 1e-9

    def test_all_intents_have_descriptions(self):
        from ontology.domain import ONTOLOGY, INTENT_DESCRIPTIONS
        for intents in ONTOLOGY.values():
            for intent in intents:
                assert intent in INTENT_DESCRIPTIONS


# ---------------------------------------------------------------------------
# graph.py
# ---------------------------------------------------------------------------

class TestGraph:
    @pytest.fixture(autouse=True)
    def seed_kg(self):
        from case_base.db import init_db
        from ontology.graph import init_kg
        init_db()
        init_kg()

    def test_root_exists(self):
        from ontology.graph import get_concept
        from ontology.domain import ROOT
        root = get_concept(ROOT)
        assert root is not None
        assert root["type"] == "root"

    def test_categories_seeded(self):
        from ontology.graph import get_concept
        from ontology.domain import ONTOLOGY
        for category in ONTOLOGY:
            c = get_concept(category)
            assert c is not None and c["type"] == "category"

    def test_intents_seeded(self):
        from ontology.graph import get_concept
        from ontology.domain import ONTOLOGY
        for intents in ONTOLOGY.values():
            for intent in intents:
                c = get_concept(intent)
                assert c is not None and c["type"] == "intent"

    def test_idempotent(self):
        from ontology.graph import init_kg, get_kg_stats
        init_kg()
        a = get_kg_stats()
        init_kg()
        b = get_kg_stats()
        assert a == b

    def test_get_children(self):
        from ontology.graph import get_children
        ch = get_children("ORDER")
        assert len(ch) > 0
        assert all(c["type"] == "intent" for c in ch)

    def test_stats_counts(self):
        from ontology.graph import get_kg_stats
        from ontology.domain import ONTOLOGY
        stats = get_kg_stats()
        total_intents = sum(len(v) for v in ONTOLOGY.values())
        assert stats["intents"] == total_intents
        assert stats["categories"] == len(ONTOLOGY)
        assert stats["concepts"] == 1 + len(ONTOLOGY) + total_intents

    def test_same_concept_distance(self):
        from ontology.graph import tree_distance
        assert tree_distance("track_order", "track_order") == 0

    def test_sibling_distance(self):
        from ontology.graph import tree_distance
        assert tree_distance("cancel_order", "track_order") == 2

    def test_cross_category_distance(self):
        from ontology.graph import tree_distance
        assert tree_distance("cancel_order", "get_refund") == 4

    def test_unknown_distance(self):
        from ontology.graph import tree_distance
        assert tree_distance("cancel_order", "__nope__") is None


# ---------------------------------------------------------------------------
# similarity.py
# ---------------------------------------------------------------------------

class TestSimilarity:
    def test_intent_exact(self):
        from ontology.similarity import intent_similarity
        assert intent_similarity("track_order", "track_order") == 1.0

    def test_intent_siblings(self):
        from ontology.similarity import intent_similarity
        assert intent_similarity("cancel_order", "track_order") == 0.6

    def test_intent_cross_category(self):
        from ontology.similarity import intent_similarity
        assert intent_similarity("cancel_order", "get_refund") == 0.2

    def test_intent_none(self):
        from ontology.similarity import intent_similarity
        assert intent_similarity(None, "track_order") == 0.0
        assert intent_similarity("track_order", None) == 0.0

    def test_category_exact(self):
        from ontology.similarity import category_similarity
        assert category_similarity("ORDER", "ORDER") == 1.0
        assert category_similarity("order", "ORDER") == 1.0

    def test_category_different(self):
        from ontology.similarity import category_similarity
        assert category_similarity("ORDER", "REFUND") == 0.0

    def test_category_none(self):
        from ontology.similarity import category_similarity
        assert category_similarity(None, "ORDER") == 0.0

    def test_composite_full_match(self):
        from ontology.similarity import composite_similarity
        score = composite_similarity(1.0, "track_order", "track_order", "ORDER", "ORDER")
        assert score == pytest.approx(1.0)

    def test_composite_no_ontology_fallback(self):
        from ontology.similarity import composite_similarity
        assert composite_similarity(0.72, None, None, None, None) == pytest.approx(0.72)

    def test_composite_weighted_blend(self):
        from ontology.similarity import composite_similarity
        from ontology.domain import SIMILARITY_WEIGHTS as W
        score = composite_similarity(0.8, "cancel_order", "track_order", "ORDER", "ORDER")
        expected = W["text"] * 0.8 + W["intent"] * 0.6 + W["category"] * 1.0
        assert score == pytest.approx(expected, abs=1e-6)

    def test_infer_intent_from_matches(self):
        from ontology.similarity import infer_intent_from_matches
        from case_base.models import Case
        matches = [
            (Case("p", "s", {"intent": "track_order"}), 0.9),
            (Case("p", "s", {"intent": "track_order"}), 0.8),
            (Case("p", "s", {"intent": "cancel_order"}), 0.7),
        ]
        assert infer_intent_from_matches(matches) == "track_order"

    def test_infer_category_from_intent(self):
        from ontology.similarity import infer_category_from_intent
        assert infer_category_from_intent("track_order") == "ORDER"
        assert infer_category_from_intent("get_refund") == "REFUND"
        assert infer_category_from_intent(None) is None
