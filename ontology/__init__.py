"""Ontology package for the CBR Customer Support Chatbot.

Modules
-------
domain      – Domain ontology tree, concept hierarchy, similarity weights.
graph       – SQLite persistence for concepts and relations (knowledge graph).
similarity  – Ontology-aware similarity functions (intent, category, composite).
"""
from ontology.domain import ONTOLOGY, SIMILARITY_WEIGHTS, INTENT_TO_CATEGORY
from ontology.graph import init_kg, get_concept, get_kg_stats, tree_distance
from ontology.similarity import (
    intent_similarity,
    category_similarity,
    composite_similarity,
    infer_intent_from_matches,
    infer_category_from_intent,
)

__all__ = [
    "ONTOLOGY",
    "SIMILARITY_WEIGHTS",
    "INTENT_TO_CATEGORY",
    "init_kg",
    "get_concept",
    "get_kg_stats",
    "tree_distance",
    "intent_similarity",
    "category_similarity",
    "composite_similarity",
    "infer_intent_from_matches",
    "infer_category_from_intent",
]
