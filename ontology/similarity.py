"""Ontology-aware similarity functions for CBR retrieval.

Three components are combined into a weighted composite score:

    sim_composite = w_text * sim_text
                  + w_intent * sim_intent
                  + w_category * sim_category

Where the weights come from ontology.domain.SIMILARITY_WEIGHTS and each
component is normalised to [0.0, 1.0].

Public API
----------
    intent_similarity(a, b)              → float [0, 1]
    category_similarity(a, b)            → float [0, 1]
    composite_similarity(...)            → float [0, 1]
    infer_intent_from_matches(matches)   → str | None
"""
from __future__ import annotations

from case_base.models import Case


# ---------------------------------------------------------------------------
# Intent similarity via ontology tree distance
# ---------------------------------------------------------------------------

def intent_similarity(intent_a: str | None, intent_b: str | None) -> float:
    """Return a normalised similarity score for two intent labels.

    Uses the ontology tree distance defined in domain.TREE_DISTANCE_SCORES.
    Returns 0.0 whenever either intent is None or not in the ontology.

    Examples
    --------
    >>> intent_similarity("track_order", "track_order")
    1.0
    >>> intent_similarity("cancel_order", "track_order")   # siblings
    0.6
    >>> intent_similarity("cancel_order", "reset_password")  # cross-category
    0.2
    >>> intent_similarity(None, "track_order")
    0.0
    """
    if not intent_a or not intent_b:
        return 0.0

    from ontology.domain import TREE_DISTANCE_SCORES
    from ontology.graph import tree_distance

    dist = tree_distance(intent_a, intent_b)
    if dist is None:
        return 0.0
    return TREE_DISTANCE_SCORES.get(dist, 0.0)


# ---------------------------------------------------------------------------
# Category similarity (exact match on the tree's second level)
# ---------------------------------------------------------------------------

def category_similarity(cat_a: str | None, cat_b: str | None) -> float:
    """Return 1.0 if both categories are identical, 0.0 otherwise.

    Category names are normalised to uppercase before comparison so that
    values from the Bitext dataset ("ORDER") and from user metadata match
    regardless of casing.
    """
    if not cat_a or not cat_b:
        return 0.0
    return 1.0 if cat_a.upper() == cat_b.upper() else 0.0


# ---------------------------------------------------------------------------
# Composite weighted similarity
# ---------------------------------------------------------------------------

def composite_similarity(
    text_score: float,
    query_intent: str | None,
    case_intent: str | None,
    query_category: str | None,
    case_category: str | None,
    weights: dict[str, float] | None = None,
) -> float:
    """Combine text, intent and category scores into a single weighted score.

    Parameters
    ----------
    text_score:
        Raw cosine (or Jaccard) similarity from the retrieval engine [0, 1].
    query_intent:
        Intent label inferred for the incoming query (may be None).
    case_intent:
        Intent label stored in the case's metadata (may be None).
    query_category:
        Category label inferred for the incoming query (may be None).
    case_category:
        Category label stored in the case's metadata (may be None).
    weights:
        Override the default weights from domain.SIMILARITY_WEIGHTS.
        Dict with keys ``"text"``, ``"intent"``, ``"category"``.

    Returns
    -------
    float in [0.0, 1.0]

    Notes
    -----
    When both intent and category are unknown (None on both sides), the
    composite score degrades gracefully to the plain text score.
    """
    from ontology.domain import SIMILARITY_WEIGHTS

    w = weights if weights is not None else SIMILARITY_WEIGHTS

    sim_text = max(0.0, min(1.0, text_score))
    sim_intent = intent_similarity(query_intent, case_intent)
    sim_cat = category_similarity(query_category, case_category)

    # If no ontology info is available at all, fall back to pure text score
    # so we don't penalise cases that pre-date the ontology.
    if sim_intent == 0.0 and sim_cat == 0.0:
        if not query_intent and not query_category:
            return sim_text

    score = (
        w["text"]     * sim_text
        + w["intent"]   * sim_intent
        + w["category"] * sim_cat
    )
    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# Intent inference helper
# ---------------------------------------------------------------------------

def infer_intent_from_matches(
    matches: list[tuple[Case, float]],
    top_n: int = 3,
) -> str | None:
    """Infer the most likely intent for a new query from its top-n text matches.

    Picks the intent that appears most frequently among the top-n retrieved
    cases (majority vote), weighted by similarity score.

    Parameters
    ----------
    matches:
        Output of the text-only ``retrieve()`` call, sorted descending.
    top_n:
        How many top matches to consider.

    Returns
    -------
    The inferred intent string, or None if no intent metadata is present.
    """
    from ontology.domain import ALL_INTENTS

    intent_scores: dict[str, float] = {}
    for case, score in matches[:top_n]:
        intent = (case.metadata.get("intent") or "").strip()
        if intent and intent in ALL_INTENTS:
            intent_scores[intent] = intent_scores.get(intent, 0.0) + score

    if not intent_scores:
        return None
    return max(intent_scores, key=lambda k: intent_scores[k])


def infer_category_from_intent(intent: str | None) -> str | None:
    """Return the category for a given intent using the in-memory look-up."""
    if not intent:
        return None
    from ontology.domain import INTENT_TO_CATEGORY
    return INTENT_TO_CATEGORY.get(intent)
