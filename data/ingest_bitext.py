#!/usr/bin/env python3
"""Ingest the Bitext Customer Service LLM Dataset into the SQLite case base.

Dataset: https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset
Fields used:
  instruction -> problem
  response    -> solution
  category    -> metadata["category"]
  intent      -> metadata["intent"]
  flags       -> metadata["flags"]

Usage
-----
    python data/ingest_bitext.py
    python data/ingest_bitext.py --limit 5000
    python data/ingest_bitext.py --clear   # wipe DB first, then ingest
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from case_base.db import DB_PATH, init_db, insert_case
from case_base.models import Case


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Bitext dataset into case base")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to import")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete all existing cases before ingesting",
    )
    return parser.parse_args()


def clear_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM cases")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='cases'")
    print("Cleared existing cases.")


def ingest(limit: int | None = None) -> tuple[int, int]:
    from datasets import load_dataset  # imported here so the module is importable without datasets installed

    print("Downloading Bitext dataset from HuggingFace (may take a moment)…")
    ds = load_dataset(
        "bitext/Bitext-customer-support-llm-chatbot-training-dataset",
        split="train",
    )

    init_db()
    inserted = skipped = 0

    for row in ds:
        if limit is not None and inserted >= limit:
            break

        problem: str = (row.get("instruction") or "").strip()
        solution: str = (row.get("response") or "").strip()

        if not problem or not solution:
            skipped += 1
            continue

        metadata = {
            k: (row.get(k) or "").strip()
            for k in ("category", "intent", "flags")
            if (row.get(k) or "").strip()
        }

        insert_case(Case(problem=problem, solution=solution, metadata=metadata))
        inserted += 1

    return inserted, skipped


def main() -> None:
    args = parse_args()

    if args.clear:
        init_db()  # ensure table exists before trying to clear it
        clear_db()

    inserted, skipped = ingest(limit=args.limit)
    print(f"Done — {inserted} cases inserted, {skipped} rows skipped.")


if __name__ == "__main__":
    main()
