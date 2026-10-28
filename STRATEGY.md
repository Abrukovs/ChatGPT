# Strategy: daily sports selection

## 1. Objective and scope
Analyze hockey, basketball and tennis only; exclude football. Record exactly one decision per Riga calendar date. First apply the unchanged main-pick standard (PICK, grades A/B+/B). If no main pick qualifies, select one **CANDIDATE** only when a defensible evidence-backed fallback remains; track it as **0.5 virtual flat**, not as a real-money recommendation. If even that standard is not met, record PASS. The target price is approximately 1.50–2.00, with 1.50 as a guide rather than a hard rule. Do not select a high price merely because it is high.

## 2. Workflow: scan, shortlist, compare
1. Scan the relevant day's fixtures and available markets in the three allowed sports.
2. Quickly eliminate candidates with major unresolved risks, unreliable data, poor market fit, or prices outside the intended range without a compensating reason.
3. Compare the best 3–5 remaining candidates in more depth, where the slate permits. If fewer than three credible candidates exist, do not pad the shortlist with weak events.
4. Compare multiple market types for each serious candidate; do not assume the match-winner market is automatically best.
5. If a market clears the main standard, select one PICK. If none does, choose one CANDIDATE only if the strongest fallback is still evidence-backed and its key risks are explicit; mark it `CANDIDATE — 0.5 virtual flat; no primary pick`. If no defensible fallback remains, select PASS. Never upgrade a candidate into a main pick just to avoid PASS.

## 3. Evidence to evaluate
Use the most relevant available information, normally including:
- Recent 5–6 matches, with opponent strength and context considered rather than raw win/loss counts alone.
- Relevant head-to-head matches only when conditions and participants make them informative.
- Hockey: likely/confirmed starting goaltender, team scoring and conceding patterns, special teams where reliable, travel and rest.
- Basketball: home court, pace and matchup, rotations, injury/availability reports, schedule congestion and rest.
- Tennis: surface, recent opponent quality, fitness/retirements, workload, serve/return matchup and relevant surface-specific form.
- Confirmed lineups, injuries, suspensions or late changes where reliable reports are available.
- Motivation and tactical matchups only when there is concrete context; do not invent psychological narratives.
- Current odds, differences between bookmakers and line movement where observable.
- Data freshness, source quality and any important missing information.

Use official league/team/tournament sources and reputable specialist reporting where relevant. State when lineups or other information are not confirmed. Never claim to have checked a source or market that was not actually accessible.

## 4. Market comparison
Consider, as relevant:
- Match winner / moneyline (including whether overtime or a shootout counts).
- Regulation-time result or double chance, when available and appropriate.
- Puck handicaps or basketball spreads.
- Match totals and team totals.
- Tennis game totals, set totals, game handicaps or match winner.
- Other markets only when their settlement rules are clear and the matchup supports them.

For each leading market, consider:
- Estimated probability of the selection winning.
- The exact line and settlement conditions.
- Approximate current price and whether it is confirmed.
- The downside scenario most likely to defeat the selection.
- Whether another market offers a more robust route to the same underlying view.

Do not select an artificial or unnecessarily complicated total just to find a bet. Do not prefer a market only because its odds look attractive.

## 5. Probability and price
- Give an estimated probability of success as an independent assessment, not merely the inverse of bookmaker odds.
- Calculate decimal-odds implied probability as 100 divided by decimal odds, before adjusting for bookmaker margin.
- For a price range, calculate implied probability at the quoted reference price or show the range clearly.
- Label unverified prices as **ориентировочная** (approximate). Give the source or examples and the time checked when possible.
- Never present an approximate price as guaranteed to be available at a particular bookmaker.
- The user checks their own available price. If it differs materially from the reference price, reassess implied probability, risk and suitability instead of blindly retaining the original recommendation.
- Do not claim positive expected value unless the analysis actually supports that claim; the main current goal is a credible chance of success, not value hunting alone.

## 6. Grades
Use the following labels consistently:
- **A** — rare, exceptionally strong candidate after comparing the slate.
- **B+** — high-grade candidate with a strong evidence base and manageable risks.
- **B** — reasonable candidate, but with meaningful limitations or uncertainty.
- **PASS** — neither a main pick nor a defensible fallback candidate meets the minimum standard.

`CANDIDATE` is a decision type, not a grade. Keep its underlying grade at A/B+/B as justified by the evidence, but clearly distinguish it from a main PICK. The 0.5 virtual flat is a tracking convention, not a real stake or instruction to wager.

Do not inflate a grade because a pick won, downgrade it solely because it lost, or force a B+ or A to appear every day. Explain the grade in terms of evidence and risks. These are qualitative internal grades, not calibrated probability bands.

## 7. Required output for a selected pick
Record and report:
- Selection timestamp in Riga time.
- Sport, competition, event and scheduled start time in Riga time.
- Market and exact line, including overtime/settlement conditions.
- Approximate decimal odds or range, price source/examples if available, and time checked.
- Estimated probability of success.
- Implied probability based on the quoted reference price.
- Grade: A / B+ / B.
- Main supporting reasons, main failure scenarios and unresolved uncertainties.
- A note that the user should verify their actual price.

If no main selection qualifies, report the best CANDIDATE if one is defensible, explicitly stating that no primary pick exists and that it is tracked at 0.5 virtual flat. If no defensible candidate exists, report PASS. Do not manufacture a candidate simply to satisfy the daily target.

## 8. Integrity
No fabricated statistics, prices, injuries, lineups, sources or results. Distinguish confirmed facts from estimates. Never promise a result or describe a pick as guaranteed. Do not provide stake amounts.

## 9. Pre-match scenario stress test (added 2026-10-23)
These checks are **prospective safeguards**, not claims that past losses could certainly have been predicted. Apply them before kickoff and document sources and uncertainties.

1. **Failure scenario:** For every finalist, identify at least one plausible, specific way the exact market loses (e.g. a favorite wins by 2+, an early deficit opens the game, a goalie change). State what evidence supports that scenario; do not infer its likelihood from a final score.
2. **Alternative markets:** Compare at least one materially different market for the same event when prices and settlement rules are available. Explain why the proposed market is more robust. If no comparable market quote is available, mark this as an evidence gap, not a fictitious comparison.
3. **Sensitivity:** Give a realistic lower and upper estimate for the market's success probability, based on named uncertainties such as goalie, lineup, pace, surface, or early-score dynamics. Treat this as an analyst-provided scenario range, **not** a computed confidence interval. If the low case is materially worse than the central estimate, mark the pick for manual review.
4. **No automatic veto from normal uncertainty:** A plausible failure scenario does not alone force PASS; it informs the final judgment. Reserve hard blocks for genuinely unresolved critical risks.
5. **Avoid hindsight:** Store assumptions and scenario estimates with their pre-match timestamps. Never backfill a pre-match risk using information first learned from the result.

The Python prototype flags scenario gaps and sensitivity, but it does not invent estimates, verify market availability, or assign grades automatically. A candidate with incomplete scenario inputs remains reviewable and should not be presented as a confirmed final pick without analyst review.
