# CBR Customer Support Chatbot — Session Notes
_Last updated: 2026-03-01_

---

## What Was Built

A fully working **Case-Based Reasoning (CBR) customer support chatbot** with:

- A browser-based chat UI served at `http://localhost:8000`
- A REST API (FastAPI) at the same origin
- An NLP retrieval engine (spaCy `en_core_web_md` cosine similarity)
- A rule-based adaptation layer
- An optional OpenAI GPT-4o-mini refinement layer
- SQLite persistence for the case base
- A test suite (pytest) covering all layers

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.11+ | Type hints throughout |
| API framework | FastAPI 0.135 + Uvicorn 0.41 | With `--reload` in dev |
| Schemas | Pydantic v2 | Request/response validation |
| NLP | spaCy 3.8 (`en_core_web_md`) | Document vectors + cosine similarity |
| NLP fallback | Jaccard token overlap | Used when spaCy vectors absent |
| LLM refinement | OpenAI SDK 2.x (`gpt-4o-mini`) | Optional; graceful fallback if no key |
| Persistence | SQLite via `sqlite3` stdlib | Path configurable via `CBR_DB_PATH` |
| Testing | pytest 8 + httpx (FastAPI TestClient) | 4 test modules |
| Config | python-dotenv | `.env` at project root |

---

## Module Layout

```
getting-started/
├── api/
│   ├── main.py          # FastAPI app, lifespan, all route handlers
│   ├── schemas.py       # Pydantic request/response models
│   └── static/
│       └── index.html   # Chat UI (single-page, vanilla JS)
├── case_base/
│   ├── models.py        # Case dataclass {problem, solution, metadata, case_id}
│   └── db.py            # SQLite CRUD (init_db, insert, get, get_all, delete)
├── retrieval/
│   └── engine.py        # retrieve(query, cases, top_k) → [(Case, score)]
├── adaptation/
│   └── adapter.py       # adapt(query, case) → str  (rule pipeline)
├── chatbot/
│   ├── orchestrator.py  # query(problem, top_k, min_score) → CBRResponse
│   └── llm.py           # refine(problem, CBRResponse) → str (OpenAI layer)
├── data/
│   ├── cases.db         # SQLite DB (auto-created on first run)
│   ├── customer_support_tickets.csv
│   ├── ingest_bitext.py
│   └── ingest_kaggle.py
└── tests/
    ├── test_api.py
    ├── test_case_base.py
    ├── test_retrieval.py
    └── test_adaptation.py
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Serves the chat UI |
| `POST` | `/chat-query` | UI endpoint; returns single answer + metadata |
| `POST` | `/query` | JSON API; returns answer + top-k matched cases |
| `POST` | `/cases` | Add a new case to the case base |
| `GET` | `/cases/{id}` | Fetch a case by ID |
| `DELETE` | `/cases/{id}` | Remove a case by ID |
| `GET` | `/docs` | Swagger / OpenAPI UI |

### Key request shapes

```json
// POST /chat-query
{ "problem": "string", "top_k": 3, "use_ai": true }

// POST /query
{ "problem": "string", "top_k": 5, "min_score": 0.0 }

// POST /cases
{ "problem": "string", "solution": "string", "metadata": {} }
```

---

## Running the Project

```bash
# Activate venv
source .venv/bin/activate

# Start dev server (hot-reload)
uvicorn api.main:app --reload

# Run test suite
pytest tests/ -v
```

Environment variables (`.env`):

```dotenv
OPENAI_API_KEY=sk-...          # optional — enables GPT-4o-mini refinement
CBR_DB_PATH=data/cases.db      # optional — defaults to data/cases.db
```

---

## CBR Pipeline (data flow)

```
User query
    │
    ▼
retrieval/engine.py
    retrieve(query, all_cases, top_k)
    → spaCy cosine similarity (or Jaccard fallback)
    → [(Case, score), …] sorted desc
    │
    ▼  (best match)
adaptation/adapter.py
    adapt(query, best_case)
    → rule pipeline: replace product / order number / strip placeholders
    → adapted solution string
    │
    ▼  (optional)
chatbot/llm.py
    refine(problem, CBRResponse)
    → GPT-4o-mini rephrases answer naturally
    → falls back to raw CBR answer if no key / error
    │
    ▼
API response → Chat UI
```

---

## Adaptation Rules (current)

| Rule | What it does |
|---|---|
| `_rule_replace_product` | Placeholder — detects product name in query vs metadata (extend with NER) |
| `_rule_replace_order_number` | Substitutes order/ticket/ref numbers from query into solution |
| `_rule_strip_placeholder_brackets` | Removes unfilled `{{...}}` template tokens from solution |

---

## Vector Cache

`retrieval/engine.py` maintains an in-memory `_vector_cache: dict[int, list[float]]` keyed on `case_id`. The server pre-warms this cache on startup (in the FastAPI `lifespan`) so the first real request is fast.

---

## Test Coverage Summary

| File | Tests |
|---|---|
| `test_api.py` | create case, get case, 404 case, query endpoint, delete case |
| `test_case_base.py` | SQLite CRUD (insert, get, get_all, delete) |
| `test_retrieval.py` | cosine similarity, top-k ordering, Jaccard fallback |
| `test_adaptation.py` | each adaptation rule independently |

---

## Suggested Next Steps

### Data
- [ ] Run `data/ingest_bitext.py` or `data/ingest_kaggle.py` to populate the case base with real tickets from `customer_support_tickets.csv`
- [ ] Add a `GET /cases` list endpoint with pagination

### Retrieval
- [ ] Upgrade to `en_core_web_lg` or a sentence-transformer model for higher-quality embeddings
- [ ] Persist vectors to DB to survive server restarts (avoid re-encoding on every cold start)
- [ ] Add a configurable `min_score` threshold in the chat UI

### Adaptation
- [ ] Flesh out `_rule_replace_product` with spaCy NER or a lookup table
- [ ] Add a rule for date/time substitution

### API / UI
- [ ] `GET /cases` with pagination and search
- [ ] Multi-turn conversation context (pass previous turns in `/chat-query`)
- [ ] Authentication / rate limiting
- [ ] Docker / `docker-compose` setup

### Testing
- [ ] Add tests for `chatbot/llm.py` (mock OpenAI client)
- [ ] Add tests for `/chat-query` endpoint
- [ ] Load / performance test retrieval at scale (1 k+ cases)
- [ ] Add `pytest-cov` and set a coverage threshold
