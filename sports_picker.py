#!/usr/bin/env python3
"""Transparent decision-support prototype for sports-pick candidates.

This tool does not fetch fixtures, odds, injury news, or scores and does not
predict outcomes. It validates analyst/AI-supplied candidates, calculates
bookmaker-implied probabilities, flags hard blockers, and ranks eligible
candidates by supplied estimated probability and documented risk.
"""
import argparse
import json
import sys
from pathlib import Path

ALLOWED_SPORTS = {"hockey", "basketball", "tennis"}
DEFAULT_MIN_ODDS = 1.50
DEFAULT_MAX_ODDS = 2.00


def validate_candidate(candidate):
    errors = []
    required = ("id", "sport", "competition", "event", "market", "odds", "estimated_probability_pct")
    for field in required:
        if field not in candidate:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors
    if str(candidate["sport"]).strip().lower() not in ALLOWED_SPORTS:
        errors.append("sport must be hockey, basketball, or tennis")
    try:
        odds = float(candidate["odds"])
        if odds <= 1.0:
            errors.append("decimal odds must be greater than 1.0")
    except (TypeError, ValueError):
        errors.append("odds must be a number")
    try:
        probability = float(candidate["estimated_probability_pct"])
        if not 0.0 <= probability <= 100.0:
            errors.append("estimated_probability_pct must be between 0 and 100")
    except (TypeError, ValueError):
        errors.append("estimated_probability_pct must be a number")
    for field in ("critical_risks", "evidence_gaps", "failure_scenarios", "alternative_markets"):
        if not isinstance(candidate.get(field, []), list):
            errors.append(f"{field} must be a list")
    bounds = candidate.get("scenario_probability_pct")
    if bounds is not None:
        if not isinstance(bounds, dict) or "low" not in bounds or "high" not in bounds:
            errors.append("scenario_probability_pct must contain low and high")
        else:
            try:
                low, high = float(bounds["low"]), float(bounds["high"])
                center = float(candidate["estimated_probability_pct"])
                if not (0 <= low <= center <= high <= 100):
                    errors.append("scenario bounds must satisfy 0 <= low <= estimate <= high <= 100")
            except (TypeError, ValueError):
                errors.append("scenario bounds must be numeric")
    return errors


def scenario_review(candidate, central_probability):
    """Flags incomplete scenario work; does not calculate probabilities."""
    failure = candidate.get("failure_scenarios", [])
    alternatives = candidate.get("alternative_markets", [])
    bounds = candidate.get("scenario_probability_pct")
    flags = []
    if not failure:
        flags.append("failure scenario not documented")
    if not alternatives:
        flags.append("alternative market comparison not documented")
    if bounds is None:
        flags.append("sensitivity range not documented")
    elif central_probability - float(bounds["low"]) >= 10:
        flags.append("low-case estimate is at least 10 percentage points below central estimate")
    return flags


def evaluate_candidate(candidate, min_odds=DEFAULT_MIN_ODDS, max_odds=DEFAULT_MAX_ODDS):
    errors = validate_candidate(candidate)
    if errors:
        return {"id": candidate.get("id", "unknown"), "valid": False, "errors": errors}
    odds = float(candidate["odds"])
    probability = float(candidate["estimated_probability_pct"])
    critical_risks = candidate.get("critical_risks", [])
    evidence_gaps = candidate.get("evidence_gaps", [])
    blockers = []
    if str(candidate["sport"]).strip().lower() not in ALLOWED_SPORTS:
        blockers.append("sport excluded by project rules")
    if odds < min_odds:
        blockers.append(f"odds below guide minimum ({min_odds:.2f})")
    if critical_risks:
        blockers.append("unresolved critical risk(s) present")
    review_flags = scenario_review(candidate, probability)
    return {
        "id": str(candidate["id"]),
        "valid": True,
        "sport": str(candidate["sport"]).lower(),
        "competition": candidate["competition"],
        "event": candidate["event"],
        "market": candidate["market"],
        "odds": round(odds, 4),
        "estimated_probability_pct": round(probability, 2),
        "implied_probability_pct": round(100.0 / odds, 2),
        "in_preferred_odds_range": min_odds <= odds <= max_odds,
        "critical_risks": critical_risks,
        "evidence_gaps": evidence_gaps,
        "blockers": blockers,
        "eligible": not blockers,
        "failure_scenarios": candidate.get("failure_scenarios", []),
        "alternative_markets": candidate.get("alternative_markets", []),
        "scenario_probability_pct": candidate.get("scenario_probability_pct"),
        "scenario_review_flags": review_flags,
        "requires_manual_review": bool(review_flags),
        "notes": candidate.get("notes", ""),
    }


def rank_candidates(candidates, min_odds=DEFAULT_MIN_ODDS, max_odds=DEFAULT_MAX_ODDS):
    evaluated = [evaluate_candidate(c, min_odds, max_odds) for c in candidates]
    invalid = [item for item in evaluated if not item.get("valid")]
    valid = [item for item in evaluated if item.get("valid")]
    eligible = [item for item in valid if item["eligible"]]
    # No synthetic composite score: rank by the supplied probability, then
    # fewer evidence gaps. This is decision support, not a probability model.
    eligible.sort(key=lambda item: (
        -item["estimated_probability_pct"],
        len(item["scenario_review_flags"]),
        len(item["evidence_gaps"]),
        0 if item["in_preferred_odds_range"] else 1,
    ))
    return {
        "method_note": (
            "Ranking uses the supplied probability estimate; this program does not "
            "estimate probabilities or verify evidence. Implied probability is "
            "100 / decimal odds and does not remove bookmaker margin."
        ),
        "preferred_odds_range": [min_odds, max_odds],
        "eligible_candidates": eligible,
        "ineligible_candidates": [item for item in valid if not item["eligible"]],
        "invalid_candidates": invalid,
        "suggested_lead": eligible[0] if eligible else None,
        "final_pick_approved": False,
        "decision": "REVIEW_CANDIDATES" if eligible else "PASS_OR_COLLECT_MORE_EVIDENCE",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON file containing a list of candidate objects")
    parser.add_argument("--min-odds", type=float, default=DEFAULT_MIN_ODDS)
    parser.add_argument("--max-odds", type=float, default=DEFAULT_MAX_ODDS)
    args = parser.parse_args()
    if args.min_odds <= 1.0 or args.max_odds < args.min_odds:
        parser.error("odds range must satisfy 1 < min-odds <= max-odds")
    try:
        candidates = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read input JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(candidates, list):
        print("Input JSON must contain a list of candidates.", file=sys.stderr)
        return 2
    print(json.dumps(rank_candidates(candidates, args.min_odds, args.max_odds), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
