# Copilot Instructions

## Project Overview

This is a **Case-Based Reasoning (CBR) customer support chatbot** in Python. It retrieves similar past support cases from a knowledge base and adapts their solutions to answer new queries.

## Architecture

Core CBR pipeline:
1. **Case Base** – stores past support cases as `{problem: str, solution: str, metadata: dict}` records in **SQLite** (via `sqlite3` or SQLAlchemy)
2. **Retrieval** – uses NLP similarity (spaCy or NLTK) to find the top-k most similar past cases for a new query
3. **Adaptation** – adjusts retrieved solutions to fit the new context (e.g., replacing version numbers, product names)
4. **Response** – presents the adapted solution to the user

Expected module layout:
```
getting-started/
├── case_base/       # Case storage and CRUD
├── retrieval/       # NLP similarity engine
├── adaptation/      # Solution adaptation logic
├── api/             # FastAPI app – routes, request/response models
├── chatbot/         # CBR orchestrator (no I/O dependency)
├── data/            # Sample case base (JSON/CSV)
└── tests/
```

## Code Style

- Python 3.11+, type hints throughout
- Prefer `dataclasses` or `pydantic` for case schemas
- NLP library of choice: **spaCy** (`en_core_web_md` or larger for word vectors); fall back to NLTK only when spaCy is unavailable
- Similarity metric: cosine similarity on sentence/document vectors

## Build and Test

```bash
# Create and activate virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (required for retrieval)
python -m spacy download en_core_web_md

# Run the API (development)
uvicorn api.main:app --reload

# Run tests
pytest tests/
```

## Project Conventions

- Case records must be serialisable to JSON; avoid storing raw NLP objects in the case base
- Similarity scores should be normalised to `[0.0, 1.0]`; retrieval returns a list of `(case, score)` tuples sorted descending
- Adaptation rules live in `adaptation/` and should be independently testable (pure functions where possible)
- FastAPI app lives in `api/`; route handlers call into `chatbot/` orchestrator only — no CBR logic in routes
- Use Pydantic models for all API request/response schemas (FastAPI's native integration)
- SQLite DB path configurable via env var `CBR_DB_PATH` (default: `data/cases.db`)
- Keep the CBR engine decoupled from FastAPI so it can be tested without running the server

## Integration Points

- **spaCy** – NLP pipeline for tokenisation and vector similarity
- **NLTK** – fallback tokenisation / stemming if needed
- **FastAPI + Uvicorn** – HTTP API layer; key endpoints: `POST /query`, `POST /cases`, `GET /cases/{id}`
- **SQLite** – persistent case base; schema managed in `case_base/db.py`
