# Ontology-Based CBR — Approach & Design

_Sprint 2 · 2026-03-02_

---

## 1. Motivation

The original CBR retrieval relied solely on **text similarity** — comparing the incoming customer query against every stored problem description using spaCy cosine distance. While effective for surface-level matches, this approach misses semantically related cases where the wording differs but the intent is the same (e.g. "I want my money back" vs. "how do I initiate a refund?").

An **ontology layer** solves this by encoding the *meaning* of a query — its intent and category — as a formal concept in a hierarchy. Retrieval then blends text evidence with ontological distance, giving higher scores to cases in the same intent family even when they use different words.

---

## 2. Domain Ontology

### 2.1 Concept hierarchy

```
CustomerSupportIssue  (root)
├── ORDER
│   ├── cancel_order
│   ├── change_order
│   ├── place_order
│   └── track_order
├── ACCOUNT
│   ├── create_account
│   ├── delete_account
│   ├── edit_account
│   └── switch_account
├── SHIPPING_ADDRESS
│   ├── change_shipping_address
│   └── set_up_shipping_address
├── PAYMENT
│   ├── check_payment_methods
│   └── payment_issue
├── REFUND
│   ├── check_refund_policy
│   ├── get_refund
│   └── track_refund
├── CANCELLATION_FEE
│   └── check_cancellation_fee
├── CONTACT
│   ├── contact_customer_service
│   └── contact_human_agent
├── FEEDBACK
│   ├── complaint
│   └── review
├── INVOICE
│   ├── check_invoice
│   └── get_invoice
├── NEWSLETTER
│   └── newsletter_subscription
└── DELIVERY
    ├── delivery_options
    └── delivery_period
```

The category names are drawn directly from the **Bitext customer support dataset** `category` field.  
The intent names are drawn from the `intent` field.

**Source:** `ontology/domain.py`

### 2.2 Properties on each concept

Every concept carries:

| Property | Description |
|---|---|
| `name` | Unique identifier (e.g. `track_order`, `ORDER`) |
| `type` | `root` \| `category` \| `intent` |
| `parent` | Name of the parent concept (NULL for root) |
| `label` | Human-readable display name |
| `description` | Plain-text explanation for documentation and future NLU |

---

## 3. Persistent Knowledge Graph

The ontology is stored as two tables in the **same SQLite database** as the case base (`data/cases.db`).

### 3.1 Schema

```sql
-- Nodes
CREATE TABLE kg_concepts (
    name        TEXT PRIMARY KEY,
    type        TEXT NOT NULL CHECK(type IN ('root','category','intent')),
    parent      TEXT REFERENCES kg_concepts(name),
    label       TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);

-- Edges
CREATE TABLE kg_relations (
    subject   TEXT NOT NULL REFERENCES kg_concepts(name),
    predicate TEXT NOT NULL,
    object    TEXT NOT NULL REFERENCES kg_concepts(name),
    PRIMARY KEY (subject, predicate, object)
);
```

### 3.2 Relations stored

| Predicate | Example |
|---|---|
| `IS_A` | `track_order IS_A ORDER` |
| `IS_A` | `ORDER IS_A CustomerSupportIssue` |
| `BROADER_THAN` | `ORDER BROADER_THAN track_order` |

### 3.3 Initialisation

`ontology.graph.init_kg()` is called from `case_base.db.init_db()`, which is the first thing the FastAPI `lifespan` handler runs on server startup. `init_kg` is **idempotent** — uses `INSERT OR IGNORE` so re-running it never creates duplicates.

```python
from ontology.graph import init_kg, get_kg_stats

init_kg()
print(get_kg_stats())
# {'concepts': 38, 'categories': 11, 'intents': 26, 'relations': 74}
```

**Source:** `ontology/graph.py`

---

## 4. Composite Similarity Score

### 4.1 Formula

$$\text{sim}(q, c) = w_{\text{text}} \cdot \text{sim}_{\text{text}} + w_{\text{intent}} \cdot \text{sim}_{\text{intent}} + w_{\text{category}} \cdot \text{sim}_{\text{category}}$$

All components are normalised to $[0, 1]$.

### 4.2 Default weights

| Component | Weight | Rationale |
|---|---|---|
| `text` | **0.60** | Cosine similarity on spaCy `en_core_web_md` vectors remains the primary signal |
| `intent` | **0.25** | Ontology tree distance gives a strong semantic boost to same-intent cases |
| `category` | **0.15** | Coarser grouping; rewards same-topic cases regardless of specific intent |

Weights are configurable in `ontology/domain.py → SIMILARITY_WEIGHTS` and must sum to 1.0.

### 4.3 Intent similarity (tree distance)

```
Tree hops → Similarity score

0  (same intent)         → 1.0
2  (sibling intents)     → 0.6    e.g. cancel_order ↔ track_order
4  (cross-category)      → 0.2    e.g. cancel_order ↔ get_refund
unknown (not in tree)    → 0.0
```

Hop counts on the undirected concept tree:

```
cancel_order  (intent)
    └── ORDER  (category)           ← 1 hop
        └── CustomerSupportIssue   ← 2 hops from ORDER
            └── REFUND             ← 3 hops from ORDER
                └── get_refund     ← 4 hops total
```

**Source:** `ontology/similarity.py`

### 4.4 Graceful degradation

- If a case has no `intent` or `category` metadata, the ontology components contribute 0 but the text weight still applies — the score is not penalised unfairly.
- If the query intent cannot be inferred AND the case has no intent, `composite_similarity` falls back to the pure text score so pre-ontology cases rank normally.
- If the `ontology` package is somehow unavailable (import error), both `retrieval/engine.py` and `chatbot/orchestrator.py` fall back silently to text-only retrieval.

---

## 5. Two-Stage Retrieval Pipeline

```
Incoming query (text only)
        │
        ▼  Stage 1 — Text pass
retrieve(query, all_cases, top_k=max(requested_k, 5))
        │  → text-ranked candidate list
        ▼
infer_intent_from_matches(top_n=3)
        │  → majority-vote intent from top-3 text results
        ▼
infer_category_from_intent(intent)
        │
        ▼  Stage 2 — Composite re-rank
retrieve(query, all_cases, top_k=k,
         query_intent=inferred_intent,
         query_category=inferred_category)
        │  → composite-scored, re-sorted top-k
        ▼
CBR orchestrator → adaptation → LLM refinement → response
```

Intent inference uses a **weighted majority vote** over the top-3 text-match cases: the intent appearing most frequently, weighted by similarity score, wins. This avoids a dedicated classifier dependency.

**Source:** `chatbot/orchestrator.py`, `retrieval/engine.py`

---

## 6. File Layout

```
ontology/
├── __init__.py         Public re-exports for the package
├── domain.py           Ontology tree, descriptions, weights, TREE_DISTANCE_SCORES
├── graph.py            SQLite persistence: init_kg, get_concept, tree_distance, get_kg_stats
└── similarity.py       intent_similarity, category_similarity, composite_similarity,
                        infer_intent_from_matches, infer_category_from_intent
tests/
└── test_ontology.py    27 unit tests covering all three modules
```

---

## 7. Knowledge Graph Stats (after init)

```
Concepts  : 38   (1 root + 11 categories + 26 intents)
Relations : 74   (2 per edge × 37 edges)
```

Inspect at runtime:

```bash
sqlite3 data/cases.db "SELECT type, COUNT(*) FROM kg_concepts GROUP BY type;"
# intent    26
# category  11
# root       1

sqlite3 data/cases.db "SELECT predicate, COUNT(*) FROM kg_relations GROUP BY predicate;"
# BROADER_THAN  37
# IS_A          37
```

---

## 8. Extending the Ontology

### Adding a new intent

1. Add it to the relevant list in `ONTOLOGY` in `ontology/domain.py`.
2. Add a description in `INTENT_DESCRIPTIONS`.
3. The KG will pick it up automatically on the next server restart (or `init_kg()` call).

### Adding a new category

1. Add a new key + intent list in `ONTOLOGY`.
2. Add a description in `CATEGORY_DESCRIPTIONS`.

### Tuning weights

Edit `SIMILARITY_WEIGHTS` in `ontology/domain.py`. Weights must sum to 1.0 (validated by `tests/test_ontology.py::TestDomain::test_weights_sum_to_one`).

### Tuning tree-distance scores

Edit `TREE_DISTANCE_SCORES` in `ontology/domain.py`.

---

## 9. Future Work

| Enhancement | Notes |
|---|---|
| **Intent classifier** | Replace majority-vote inference with a spaCy `textcat` or zero-shot classifier trained on the Bitext dataset |
| **Weighted edges** | Store per-relation weights in `kg_relations` to model stronger/weaker semantic links |
| **OWL / RDF export** | Export `kg_concepts` + `kg_relations` to Turtle/OWL for use in semantic web tools |
| **User feedback loop** | When a user rates an answer, update case metadata with the confirmed intent for retention |
| **Ontology admin API** | `GET /ontology/concepts`, `GET /ontology/stats` endpoints for inspection |
