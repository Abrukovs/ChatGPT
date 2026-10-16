# Sports Scheduled — portable project specification

This repository preserves the decision rules and operating procedure for a daily sports-pick workflow, so another AI or future software implementation can continue the work if the original ChatGPT Scheduled task becomes unavailable.

## Scope
- Sports: hockey, basketball, tennis only. Football is excluded.
- Daily goal: select at most one strongest candidate, usually at an approximate decimal price of 1.50–2.00.
- No forced picks. PASS is allowed when evidence does not support a sufficiently reliable selection.
- Compare markets, not just teams: match winner, handicaps/spreads, match/team totals, tennis games/sets and other relevant markets.
- Preserve the original pick and price/probability estimates; record later user-observed prices separately.
- Check unsettled previous picks before creating a new one.
- No stake amounts are recorded or recommended.

## Current project status
The strategy documents are in place. A small Python candidate-comparison prototype now validates candidate records, calculates bookmaker-implied probability and ranks eligible candidates using an estimate supplied by an analyst or AI. It does **not** generate predictions or fetch live sports data.

## Quick start
Requires Python 3.10 or newer; no third-party packages are needed.

From the repository root:
```bash
python -m unittest test_sports_picker -v
python sports_picker.py candidates.example.json
```

The sample data is fictional and must not be treated as betting advice.

## Files
- [STRATEGY.md](STRATEGY.md): candidate screening, market selection, risk assessment and grading.
- [JOURNAL.md](JOURNAL.md): record schema, settlement and export rules.
- [SCHEDULE.md](SCHEDULE.md): daily run sequence and time-zone requirements.
- [CHANGELOG.md](CHANGELOG.md): history of project changes.
- [sports_picker.py](sports_picker.py): transparent candidate validation and ranking prototype.
- [candidates.example.json](candidates.example.json): fictional sample input.
- [test_sports_picker.py](test_sports_picker.py): unit tests using Python's standard library.

## Important limitations
This is not yet a complete automated betting-analysis application. It does not fetch fixtures, odds, injury reports, scores, or write to Coda. It does not independently estimate the probability of a market winning. Those integrations must be implemented and tested separately. The ChatGPT Scheduled task and its schedule do not automatically transfer to GitHub.

## Operating principles
1. Verify facts and sources; never invent odds, lineups, injuries, statistics or results.
2. Separate estimated probability of success from bookmaker-implied probability.
3. Explain why the selected market is better suited than plausible alternatives.
4. Be explicit about uncertainty and what could invalidate the pick.
5. Never claim that a journal or Coda record was updated unless the write actually succeeded.
6. Keep private credentials, access tokens and API keys out of repository files and chat messages.

## Change policy
Make changes in small, understandable commits. Record meaningful strategy changes in CHANGELOG.md and preserve a clear reason for each change. Do not treat a single win or loss as proof that a strategy is good or bad; assess results over a meaningful sample.
