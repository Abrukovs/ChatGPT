# Sports Scheduled — portable project specification

This repository preserves the decision rules and operating procedure for a daily sports-pick workflow. It is intended to help another AI or a future software implementation reproduce and improve the process if the original ChatGPT Scheduled task becomes unavailable.

## Scope
- Sports: hockey, basketball, tennis only. Football is excluded.
- Daily goal: select at most one strongest candidate, usually at an approximate decimal price of 1.50–2.00.
- No forced picks. PASS is allowed when evidence does not support a sufficiently reliable selection.
- Compare markets, not just teams: match winner, handicaps/spreads, match/team totals, tennis games/sets and other relevant markets.
- Preserve the original pick and price/probability estimates; record later user-observed prices separately.
- Check unsettled previous picks before creating a new one.
- No stake amounts are recorded or recommended.

## Files
- STRATEGY.md: candidate screening, market selection, risk assessment and grading.
- JOURNAL.md: record schema, settlement and export rules.
- SCHEDULE.md: daily run sequence and time-zone requirements.
- CHANGELOG.md: history of project changes.

## Important limitation
This repository currently documents the workflow; it is not yet a complete automated betting-analysis application. It does not itself fetch fixtures, odds, injury reports, scores, or write to Coda. Those integrations must be implemented and tested separately. The ChatGPT Scheduled task and its schedule do not automatically transfer to GitHub.

## Operating principles
1. Verify facts and sources; never invent odds, lineups, injuries, statistics or results.
2. Separate estimated probability of success from bookmaker-implied probability.
3. Explain why the selected market is better suited than plausible alternatives.
4. Be explicit about uncertainty and what could invalidate the pick.
5. Never claim that a journal or Coda record was updated unless the write actually succeeded.
6. Keep private credentials, access tokens and API keys out of repository files and chat messages.

## Change policy
Make changes in small, understandable commits. Record meaningful strategy changes in CHANGELOG.md and preserve a clear reason for each change. Do not treat a single win or loss as proof that a strategy is good or bad; assess results over a meaningful sample.
