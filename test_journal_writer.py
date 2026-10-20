import csv
import tempfile
import unittest
from pathlib import Path

from journal_writer import JOURNAL_FIELDS, JournalError, append_prediction


def sample(**overrides):
    row = {
        "prediction_id": "TEST-2026-10-20-001",
        "selected_at_riga": "2026-10-20T15:00:00+03:00",
        "sport": "hockey",
        "competition": "TEST ONLY",
        "event": "TEST TEAM A - TEST TEAM B",
        "scheduled_start_riga": "",
        "market": "TEST market",
        "line": "TEST line",
        "reference_odds": "1.70",
        "odds_status": "TEST - not a real price",
        "odds_source": "",
        "odds_checked_at_riga": "",
        "estimated_probability_pct": "65",
        "implied_probability_pct": "58.82",
        "grade": "B",
        "rationale": "AUTOMATED TEST RECORD; NOT A REAL PICK",
        "risks": "Test only",
        "user_actual_odds": "",
        "result_status": "Pending",
        "final_score": "",
        "settled_at_riga": "",
        "result_source_url": "",
        "settlement_notes": "",
    }
    row.update(overrides)
    return row


class JournalWriterTests(unittest.TestCase):
    def test_adds_one_record_with_expected_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.csv"
            self.assertEqual(append_prediction(path, sample()), "added")
            with path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(reader.fieldnames, JOURNAL_FIELDS)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["prediction_id"], "TEST-2026-10-20-001")

    def test_same_id_is_not_added_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.csv"
            self.assertEqual(append_prediction(path, sample()), "added")
            self.assertEqual(append_prediction(path, sample()), "duplicate")
            with path.open(newline="", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 1)

    def test_rejects_football(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(JournalError):
                append_prediction(Path(tmp) / "predictions.csv", sample(sport="football"))

    def test_rejects_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(JournalError):
                append_prediction(Path(tmp) / "predictions.csv", sample(event=""))

    def test_rejects_pass_as_recorded_pick(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(JournalError):
                append_prediction(Path(tmp) / "predictions.csv", sample(grade="PASS"))


if __name__ == "__main__":
    unittest.main()
