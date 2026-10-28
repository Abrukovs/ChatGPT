# Connecting daily decisions to the GitHub journal

The workflow `.github/workflows/record-daily-decision.yml` provides a manual, auditable entry point for one JSON decision or one settlement.

## Workflow

1. Complete the sports analysis outside GitHub. Save exactly one decision per Riga date: **PICK** when the main standard is met; otherwise **CANDIDATE** when a defensible fallback remains; otherwise **PASS**. A CANDIDATE is not a main pick and is tracked as **0.5 virtual flat** only.
2. Prepare a JSON object using the field names in `daily_decisions.csv`. For PICK or CANDIDATE provide sport, competition, event, market, independent probability, grade and initial line/odds when available. For CANDIDATE, `decision` must be `CANDIDATE` and `rationale` must explicitly include `CANDIDATE` and `0.5 virtual flat`, plus state that no primary pick was found. For PASS, leave all selection fields empty and provide date, decision ID, selection time and optionally rationale/risks.
3. In GitHub Actions select **Record daily decision**, **Run workflow**, choose `decision`, paste the JSON into `record_json`, and start it.
4. The workflow validates and saves the record to `daily_decisions.csv` in `main`. Exact duplicates are no-ops; a different decision for the same Riga date is rejected.
5. On the following day, verify any completed PICK or CANDIDATE using an official/reliable score source. For the result use `settlement` and a JSON object with decision_id, result_status, settled_at_riga, result_source_url, final_score and settlement_notes. Mark candidate settlements as CANDIDATE / 0.5 virtual flat in `settlement_notes`. The original decision is never modified.

Example PASS (illustrative only; do not submit it as a real decision):

```json
{"date_riga":"2026-10-21","decision_id":"EXAMPLE-20261021","decision":"PASS","selected_at_riga":"2026-10-21T12:00:00+03:00","rationale":"EXAMPLE ONLY"}
```

**Limitations:** No automatic transfer from a ChatGPT scheduled task to GitHub has been configured. This workflow is manually triggered and does not fetch sports schedules, odds or results. Do not invent missing data or create a PASS merely because no external prediction arrived. For fully automatic transfer, a separately authorized integration is needed.

The workflow uses the built-in GitHub Actions token with `contents: write`; the repository's Actions settings and branch protection must allow the push. Runs are serialized to reduce concurrent writes. No external API key is required for manual entry.
