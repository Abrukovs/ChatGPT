import csv
import json
import tempfile
import unittest
from pathlib import Path

from journal_import import import_record


class JournalImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source = self.folder / "input.json"

    def write(self, data):
        self.source.write_text(json.dumps(data), encoding="utf-8")

    def test_decision_import_is_idempotent(self):
        self.write({
            "date_riga": "2026-10-20",
            "decision_id": "TEST-20261020",
            "decision": "PASS",
            "selected_at_riga": "2026-10-20T12:00:00+03:00",
            "rationale": "Test only",
        })
        self.assertEqual(import_record("decision", self.source, self.folder), "added")
        self.assertEqual(import_record("decision", self.source, self.folder), "duplicate")
        with (self.folder / "daily_decisions.csv").open(newline="", encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 1)

    def test_settlement_without_pick_rejected(self):
        self.write({
            "decision_id": "NOT-EXIST",
            "result_status": "Win",
            "settled_at_riga": "2026-10-21T12:00:00+03:00",
            "result_source_url": "https://example.org/test",
        })
        with self.assertRaises(ValueError):
            import_record("settlement", self.source, self.folder)

    def test_rejects_non_object(self):
        self.write([{"decision": "PASS"}])
        with self.assertRaises(ValueError):
            import_record("decision", self.source, self.folder)


if __name__ == "__main__":
    unittest.main()
