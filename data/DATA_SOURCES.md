# Case Base — Data Sources & Ingestion Guide

This document describes where the CBR case base data comes from, what shape it takes, and how to load it.

---

## Case Schema

Every case stored in SQLite has three fields:

| Field | Type | Description |
|---|---|---|
| `problem` | `str` | The customer's problem description (maps to the query at retrieval time) |
| `solution` | `str` | The resolution / answer to that problem |
| `metadata` | `dict` | Arbitrary key-value context (intent, category, product, priority, etc.) |

The primary key `case_id` is assigned automatically by SQLite on insert.

Cases are stored in `data/cases.db` (configurable via `CBR_DB_PATH` env var).

---

## Data Source 1 — Bitext Customer Support LLM Dataset (HuggingFace) ⭐ Recommended

**URL:** https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset  
**Size:** ~26,872 rows  
**Licence:** Apache 2.0  
**Format:** HuggingFace `datasets` library (downloaded automatically on first run)

### Column mapping

| CSV / HF field | Case field | Notes |
|---|---|---|
| `instruction` | `problem` | The customer's question |
| `response` | `solution` | The support agent's answer |
| `category` | `metadata["category"]` | High-level topic (e.g. `ORDER`, `ACCOUNT`) |
| `intent` | `metadata["intent"]` | Fine-grained intent (e.g. `track_order`, `reset_password`) |
| `flags` | `metadata["flags"]` | Data-quality flags from Bitext |

### How to ingest

```bash
# Make sure the venv is active
source .venv/bin/activate

# Full dataset (~26 k cases) — downloads ~20 MB from HuggingFace
python data/ingest_bitext.py

# Limit to first 5 000 cases (faster for dev/testing)
python data/ingest_bitext.py --limit 5000

# Wipe the DB first, then ingest (clean slate)
python data/ingest_bitext.py --clear

# Combine flags
python data/ingest_bitext.py --clear --limit 5000
```

> **Requires:** `datasets` package — already in `requirements.txt`.  
> On first run HuggingFace downloads the dataset to `~/.cache/huggingface/`. Subsequent runs use the cache.

---

## Data Source 2 — Kaggle Customer Support Ticket Dataset

**URL:** https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset  
**File:** `data/customer_support_tickets.csv` (bundled in this repo)  
**Size:** ~29,807 rows (but many `Resolution` fields are empty template strings — see note below)  
**Licence:** CC BY 4.0

### Column mapping

| CSV column | Case field | Notes |
|---|---|---|
| `Ticket Description` | `problem` | Raw ticket text (some contain `{product_purchased}` placeholders) |
| `Resolution` | `solution` | Can be empty — those rows are skipped automatically |
| `Ticket Type` | `metadata["Ticket Type"]` | e.g. `Technical issue`, `Billing inquiry` |
| `Ticket Subject` | `metadata["Ticket Subject"]` | Short subject line |
| `Product Purchased` | `metadata["Product Purchased"]` | e.g. `GoPro Hero`, `Dell XPS 15` |
| `Ticket Priority` | `metadata["Ticket Priority"]` | `Low` / `Medium` / `High` / `Critical` |
| `Ticket Channel` | `metadata["Ticket Channel"]` | `Email`, `Chat`, `Phone`, `Social media` |
| `Ticket Status` | `metadata["Ticket Status"]` | `Open`, `Closed`, `Pending Customer Response` |
| `Customer Satisfaction Rating` | `metadata["Customer Satisfaction Rating"]` | 1–5 scale |

> **Note:** Many rows in this dataset have an empty `Resolution` field or only contain unfilled template tokens like `{product_purchased}`. The ingestion script automatically skips any row where `Ticket Description` or `Resolution` is blank. The adaptation rule `_rule_strip_placeholder_brackets` cleans remaining `{{…}}` tokens at query time.

### How to ingest

```bash
source .venv/bin/activate

# Default CSV path (data/customer_support_tickets.csv)
python data/ingest_kaggle.py

# Custom CSV path
python data/ingest_kaggle.py --csv /path/to/tickets.csv

# Limit rows
python data/ingest_kaggle.py --limit 500
```

> The CSV is already present in `data/`. No Kaggle account needed to use the bundled file.

---

## Data Source 3 — Manual / API

Individual cases can be added at any time via the REST API without any ingestion script:

```bash
curl -X POST http://localhost:8000/cases \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "I cannot log in after changing my email address",
    "solution": "Clear your browser cookies and try again. If the issue persists, use the Forgot Password link.",
    "metadata": {
      "category": "ACCOUNT",
      "intent": "login_issue"
    }
  }'
```

Or programmatically:

```python
from case_base.db import insert_case
from case_base.models import Case

insert_case(Case(
    problem="I cannot log in after changing my email address",
    solution="Clear your browser cookies and try again.",
    metadata={"category": "ACCOUNT", "intent": "login_issue"},
))
```

---

## Choosing a Dataset

| Scenario | Recommended source |
|---|---|
| Quick demo / first run | Bitext (`--limit 1000`) |
| Full production-quality NLP | Bitext full (~26 k cases) |
| Testing product-specific adaptation rules | Kaggle (has `Product Purchased` metadata) |
| Domain-specific deployment | Manual API / custom CSV via `ingest_kaggle.py --csv` |

---

## Managing the Case Base

```bash
# Check how many cases are loaded
sqlite3 data/cases.db "SELECT COUNT(*) FROM cases;"

# Inspect sample cases
sqlite3 data/cases.db "SELECT id, substr(problem,1,60), substr(solution,1,60) FROM cases LIMIT 10;"

# Wipe and reload from scratch
python data/ingest_bitext.py --clear

# Delete a single case via API
curl -X DELETE http://localhost:8000/cases/{id}
```

---

## Adding a Custom CSV Source

To ingest from your own CSV, copy `data/ingest_kaggle.py` and adjust the three constants at the top:

```python
COL_PROBLEM  = "your_problem_column_name"
COL_SOLUTION = "your_solution_column_name"
METADATA_COLS = ["col1", "col2", ...]   # optional extra columns to store
```

Then run:

```bash
python data/ingest_kaggle.py --csv path/to/your_data.csv
```
