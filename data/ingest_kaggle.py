#!/usr/bin/env python3
"""Ingest the Kaggle Customer Support Ticket Dataset into the SQLite case base.

Usage
-----
1. Download the CSV from Kaggle:
   https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset
   and place it at data/customer_support_tickets.csv

2. Run (with .venv activated):
   python data/ingest_kaggle.py
   python data/ingest_kaggle.py --csv path/to/custom.csv --limit 500
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from case_base.db import init_db, insert_case
from case_base.models import Case

# ---------------------------------------------------------------------------
# Column names as they appear in the Kaggle CSV
# ---------------------------------------------------------------------------
COL_PROBLEM = "Ticket Description"
COL_SOLUTION = "Resolution"
METADATA_COLS = [
    "Ticket Type",
    "Ticket Subject",
    "Product Purchased",
    "Ticket Priority",
    "Ticket Channel",
    "Ticket Status",
    "Customer Satisfaction Rating",
]

DEFAULT_CSV = Path(__file__).resolve().parent / "customer_support_tickets.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Kaggle CSV into case base")
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="Path to customer_support_tickets.csv (default: data/customer_support_tickets.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of rows to import (omit to import all)",
    )
    return parser.parse_args()


def ingest(csv_path: Path, limit: int | None = None) -> int:
    """Read the CSV and write valid cases to SQLite. Returns count of inserted rows."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV not found: {csv_path}\n"
            "Download it from https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset"
        )

    init_db()

    inserted = 0
    skipped = 0

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if limit is not None and inserted >= limit:
                break

            problem: str = (row.get(COL_PROBLEM) or "").strip()
            solution: str = (row.get(COL_SOLUTION) or "").strip()

            # Skip rows without both a problem description and a resolution
            if not problem or not solution:
                skipped += 1
                continue

            metadata = {
                col: (row.get(col) or "").strip()
                for col in METADATA_COLS
                if (row.get(col) or "").strip()
            }

            case = Case(problem=problem, solution=solution, metadata=metadata)
            insert_case(case)
            inserted += 1

    return inserted, skipped


def main() -> None:
    args = parse_args()
    print(f"Ingesting from: {args.csv}")
    inserted, skipped = ingest(args.csv, limit=args.limit)
    print(f"Done — {inserted} cases inserted, {skipped} rows skipped (missing problem or solution).")


if __name__ == "__main__":
    main()
