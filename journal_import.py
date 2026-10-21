"""Safely import one daily decision or one verified settlement from JSON.

Usage:
  python journal_import.py decision path/to/decision.json
  python journal_import.py settlement path/to/settlement.json

Input JSON is never generated automatically; no fixture or odds data is fetched.
"""
import argparse
import json
from pathlib import Path
from daily_decisions import add_decision, settle_decision


def import_record(kind, source, directory=Path(".")):
    source = Path(source)
    directory = Path(directory)
    with source.open(encoding="utf-8") as handle:
        record = json.load(handle)
    if not isinstance(record, dict):
        raise ValueError("Expected one JSON object")
    if kind == "decision":
        return add_decision(directory / "daily_decisions.csv", record)
    if kind == "settlement":
        return settle_decision(
            directory / "daily_decisions.csv",
            directory / "settlements.csv",
            record,
        )
    raise ValueError("Expected decision or settlement")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["decision", "settlement"])
    parser.add_argument("source", type=Path)
    parser.add_argument("--directory", type=Path, default=Path("."))
    args = parser.parse_args()
    print(import_record(args.kind, args.source, args.directory))


if __name__ == "__main__":
    main()
