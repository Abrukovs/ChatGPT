# Changelog

## 2026-10-16 — Candidate comparison prototype
- Added a standard-library Python tool to validate analyst/AI-supplied candidates, calculate implied probability and rank eligible candidates transparently.
- Added fictional sample input and unit tests.
- Documented that the prototype is decision support only and does not fetch live data or predict outcomes.

## 2026-10-15 — Initial portable specification
- Preserved the supplied Scheduled instructions for daily selection across hockey, basketball and tennis.
- Documented candidate screening, market comparison, independent probability estimates, approximate odds handling, qualitative grades and PASS.
- Documented immutable prediction records, result verification, duplicate prevention, Coda fallback and CSV/XLSX export requirements.
- Clarified that the repository is a specification, not yet an automated application; scheduling and data integrations remain separate implementation work.
