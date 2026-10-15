# Daily Scheduled run

## Time zone
Use the IANA time zone Europe/Riga for all selection timestamps, scheduled start times, odds-check times and settlement timestamps. Respect daylight-saving changes automatically; do not hard-code a UTC offset.

## Run sequence
1. Identify the current local date and time in Europe/Riga.
2. Review all previously recorded predictions that remain pending and settle them first using reliable score sources.
3. Scan current and upcoming fixtures for hockey, basketball and tennis only. Exclude football.
4. Shortlist the strongest candidates; compare 3–5 in depth when the slate supports it.
5. Compare plausible markets for each candidate rather than defaulting to match winner.
6. Check recent form, opponent quality, availability/lineups, rest/load, relevant matchup context, market prices and risks.
7. Choose at most one pick if it meets the strategy standard; otherwise report PASS.
8. Record the original selection and all required fields without modifying historical records.
9. Write to Coda only if the required actions are actually available and the write succeeds. Otherwise return a structured record/CSV row and disclose the limitation.
10. Summarize the result checks and the new selection, including sources and unresolved uncertainties.

## Reliability rules
- Never invent a fixture, odds quote, injury, lineup, result or source.
- Include a time checked for odds and clearly label unconfirmed prices as approximate.
- If the market price has moved materially, re-evaluate the selection.
- If a result or settlement rule cannot be verified, mark it accordingly rather than guessing.
- Do not claim that this specification alone runs on a schedule. A separate scheduler and data integrations are required for a portable automated implementation.
