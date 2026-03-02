# CBR Customer Support Chatbot

A **Case-Based Reasoning (CBR)** customer support chatbot built in Python. It retrieves similar past support cases from a knowledge base using NLP similarity and adapts their solutions to answer new queries — optionally refined by an OpenAI LLM for a natural, conversational reply.

---

## How It Works

```
User query
    │
    ▼  Retrieval (spaCy cosine similarity)
Top-k matching cases from SQLite case base
    │
    ▼  Adaptation (rule pipeline)
Solution adjusted to the new context
    │
    ▼  Refinement (optional — OpenAI GPT-4o-mini)
Natural-language response → Chat UI
```

1. **Retrieve** — spaCy `en_core_web_md` document vectors + cosine similarity find the closest past cases. Falls back to Jaccard token overlap when vectors are unavailable.
2. **Adapt** — A rule pipeline substitutes order/ticket numbers, product names, and strips unfilled template placeholders from the retrieved solution.
3. **Refine** — When `OPENAI_API_KEY` is set, GPT-4o-mini rephrases the answer naturally. Gracefully skipped if the key is absent.

---

## Features

- Browser-based chat UI (served at `/`)
- REST API with Swagger docs at `/docs`
- SQLite case base — no extra database to install
- Pre-warmed vector cache for fast first-query response
- Fully decoupled CBR engine — testable without the HTTP server
- 26 k+ Bitext customer support cases ingestable out of the box

---

## Tech Stack

| | |
|---|---|
| Language | Python 3.11+ |
| API | FastAPI + Uvicorn |
| Schemas | Pydantic v2 |
| NLP | spaCy 3.x (`en_core_web_md`) |
| LLM (optional) | OpenAI SDK (`gpt-4o-mini`) |
| Database | SQLite (`sqlite3` stdlib) |
| Testing | pytest + httpx |

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/gpad1234/Customer-Chatbot-CBR.git
cd Customer-Chatbot-CBR

# 2. Create and activate virtual environment
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the spaCy model
python -m spacy download en_core_web_md

# 5. Configure environment (optional)
cp .env.example .env
# Edit .env and set OPENAI_API_KEY to enable AI-enhanced replies

# 6. Start the server
uvicorn api.main:app --reload
```

Open **http://localhost:8000** in your browser.

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Chat UI |
| `POST` | `/chat-query` | UI endpoint — returns answer + intent/category metadata |
| `POST` | `/query` | JSON API — returns answer + top-k matched cases with scores |
| `POST` | `/cases` | Add a new case to the case base |
| `GET` | `/cases/{id}` | Fetch a case by ID |
| `DELETE` | `/cases/{id}` | Remove a case by ID |
| `GET` | `/docs` | Interactive Swagger UI |

### Example

```bash
# Add a case
curl -X POST http://localhost:8000/cases \
  -H "Content-Type: application/json" \
  -d '{"problem": "I cannot reset my password", "solution": "Use the Forgot Password link on the login page.", "metadata": {}}'

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"problem": "How do I change my password?", "top_k": 3}'
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | _(unset)_ | Enables GPT-4o-mini answer refinement |
| `CBR_DB_PATH` | `data/cases.db` | Path to the SQLite case base |

---

## Project Structure

```
├── api/                  # FastAPI app, routes, Pydantic schemas, static UI
├── case_base/            # Case dataclass, SQLite CRUD
├── retrieval/            # spaCy similarity engine
├── adaptation/           # Rule-based solution adaptation
├── chatbot/              # CBR orchestrator + OpenAI LLM layer
├── data/                 # Sample CSV + ingestion scripts
├── tests/                # pytest suite (API, case base, retrieval, adaptation)
├── requirements.txt
├── .env.example
└── SESSION_NOTES.md      # Sprint 1 tech specs and next steps
```

---

## Loading the Sample Case Base

See [data/DATA_SOURCES.md](data/DATA_SOURCES.md) for the full ingestion guide (data sources, column mappings, managing the DB, and adding a custom CSV).

```bash
# Ingest the bundled Bitext customer support dataset (~26 k cases)
source .venv/bin/activate
python data/ingest_bitext.py

# Or load a subset for faster startup
python data/ingest_bitext.py --limit 1000
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Ontology & Knowledge Graph

Sprint 2 adds an ontology-aware retrieval layer. See [docs/ONTOLOGY.md](docs/ONTOLOGY.md) for the full design, concept hierarchy, composite similarity formula, and extension guide.

## Roadmap

- [ ] `GET /cases` with pagination and keyword search
- [ ] Persist spaCy vectors to DB (faster cold starts at scale)
- [ ] Multi-turn conversation context
- [ ] Upgrade to sentence-transformer embeddings
- [ ] Docker / docker-compose setup
- [ ] Authentication and rate limiting
