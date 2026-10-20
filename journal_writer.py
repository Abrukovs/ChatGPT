#!/usr/bin/env python3
"""Append prediction records to predictions.csv without duplicate IDs.

This module only manages journal storage; it does not fetch odds, fixtures,
news, or results and does not generate betting recommendations.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping, Sequence

JOURNAL_FIELDS = [
    "prediction_id", "selected_at_riga", "sport", "competition", "event",
    "scheduled_start_riga", "market", "line", "reference_odds", "odds_status",
    "odds_source", "odds_checked_at_riga", "estimated_probability_pct",
    "implied_probability_pct", "grade", "rationale", "risks", "user_actual_odds",
    "result_status", "final_score", "settled_at_riga", "result_source_url",
    "settlement_notes",
]
REQUIRED_FIELDS = ("prediction_id", "sport", "competition", "event", "market", "grade")
ALLOWED_SPORTS = {"hockey", "basketball", "tennis"}
ALLOWED_GRADES = {"A", "B+", "B"}
ALLOWED_RESULTS = {
    "", "Pending", "Win", "Loss", "Push/Refund", "Void/Cancelled", "Unable to verify"
}


class JournalError(ValueError):
    """Raised when a journal record is invalid or the journal schema is wrong."""


def append_prediction(path: str | Path, record: Mapping[str, object]) -> str:
    """Append a valid record once; return 'added' or 'duplicate'."""
    path = Path(path)
    missing = [name for name in REQUIRED_FIELDS if not str(record.get(name, "")).strip()]
    if missing:
        raise JournalError("Missing required fields: " + ", ".join(missing))

    sport = str(record["sport"]).strip().lower()
    if sport not in ALLOWED_SPORTS:
        raise JournalError("sport must be hockey, basketball, or tennis")
    if str(record["grade"]).strip() not in ALLOWED_GRADES:
        raise JournalError("grade must be A, B+, or B; PASS is not a recorded pick")

    result_status = str(record.get("result_status", "Pending")).strip()
    if result_status not in ALLOWED_RESULTS:
        raise JournalError("Invalid result_status")
    unknown = set(record) - set(JOURNAL_FIELDS)
    if unknown:
        raise JournalError("Unknown journal fields: " + ", ".join(sorted(unknown)))

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=JOURNAL_FIELDS).writeheader()

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != JOURNAL_FIELDS:
            raise JournalError("CSV header does not match the expected journal schema")
        existing_ids = {row["prediction_id"] for row in reader}

    prediction_id = str(record["prediction_id"]).strip()
    if prediction_id in existing_ids:
        return "duplicate"

    row = {field: "" for field in JOURNAL_FIELDS}
    row.update({key: "" if value is None else str(value) for key, value in record.items()})
    row["sport"] = sport
    if not row["result_status"]:
        row["result_status"] = "Pending"
    with path.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=JOURNAL_FIELDS).writerow(row)
    return "added"
