import unittest
from sports_picker import evaluate_candidate, rank_candidates


def candidate(**overrides):
    base = {
        "id": "candidate-1", "sport": "hockey", "competition": "Test League",
        "event": "Team A - Team B", "market": "Team A +1.5", "odds": 1.65,
        "estimated_probability_pct": 67, "critical_risks": [], "evidence_gaps": []
    }
    base.update(overrides)
    return base


class SportsPickerTests(unittest.TestCase):
    def test_implied_probability(self):
        self.assertEqual(evaluate_candidate(candidate(odds=2.0))["implied_probability_pct"], 50.0)

    def test_football_is_invalid(self):
        self.assertFalse(evaluate_candidate(candidate(sport="football"))["valid"])

    def test_below_minimum_odds_is_ineligible(self):
        self.assertFalse(evaluate_candidate(candidate(odds=1.42))["eligible"])

    def test_critical_risk_blocks_candidate(self):
        self.assertFalse(evaluate_candidate(candidate(critical_risks=["goalie unknown"]))["eligible"])

    def test_highest_supplied_probability_leads(self):
        result = rank_candidates([candidate(id="low", estimated_probability_pct=61),
                                  candidate(id="high", estimated_probability_pct=69)])
        self.assertEqual(result["suggested_lead"]["id"], "high")

    def test_no_eligible_candidate_has_no_lead(self):
        result = rank_candidates([candidate(odds=1.30)])
        self.assertIsNone(result["suggested_lead"])

    def test_invalid_probability_is_reported(self):
        self.assertFalse(evaluate_candidate(candidate(estimated_probability_pct=120))["valid"])


if __name__ == "__main__":
    unittest.main()
