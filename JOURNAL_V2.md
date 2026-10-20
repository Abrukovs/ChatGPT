# Daily decision journal v2

Each Riga calendar day gets exactly one immutable decision: `PICK` or `PASS`. A PICK has one selected sport, event, market and line (where applicable). A PASS has no market. Do not rewrite historical selections when a line or odds change.

## Files

- `daily_decisions.csv`: original decisions. One row per Riga date, independent probability estimate (not calculated from odds), optional reference odds. No implied probability calculation.
- `settlements.csv`: verified outcomes for PICK decisions, linked by `decision_id`. Do not settle PASS days. Settlement requires source URL and timestamp.
- `predictions.csv`: legacy initial journal; retained unchanged for compatibility and audit. New daily decisions use `daily_decisions.csv`.

## Rules

- Only hockey, basketball and tennis are eligible.
- Grades A/B+/B apply to PICK; PASS is a valid daily decision.
- The first recorded decision for a Riga date is final; retries with identical data are harmless. Any changed decision or conflicting ID must be reviewed, never silently overwritten.
- The initially selected market, line, reference odds, estimate and grade are immutable.
- `settlements.csv` is append-only. Conflicting result corrections require manual review, not silent edits.
- This module does not find games, odds or final scores. GitHub Actions only tests storage; it does not automatically generate daily picks.

## Testing

Run `python -m unittest -v test_daily_decisions.py`. Tests use temporary files and do not change working CSVs.
