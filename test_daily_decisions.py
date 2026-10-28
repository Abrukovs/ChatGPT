import csv
import tempfile
import unittest
from pathlib import Path
from daily_decisions import add_decision, settle_decision


def pick():
    return dict(date_riga='2026-10-20',decision_id='20261020-001',decision='PICK',sport='tennis',competition='TEST',event='A-B',market='Over games',line='21.5',reference_odds='1.75',estimated_probability_pct='60',grade='B+',rationale='Test',risks='Test',selected_at_riga='2026-10-20T14:00:00+03:00')

class DailyDecisionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.decisions = Path(self.temp.name)/'daily_decisions.csv'
        self.settlements = Path(self.temp.name)/'settlements.csv'

    def test_one_decision_and_exact_retry(self):
        self.assertEqual(add_decision(self.decisions, pick()), 'added')
        self.assertEqual(add_decision(self.decisions, pick()), 'duplicate')
        with self.decisions.open(newline='',encoding='utf-8') as f:
            self.assertEqual(len(list(csv.DictReader(f))),1)

    def test_reject_second_decision_same_day(self):
        add_decision(self.decisions,pick())
        with self.assertRaises(ValueError):
            add_decision(self.decisions,{**pick(),'decision_id':'20261020-002','line':'22.5'})

    def test_pass(self):
        record = {k:v for k,v in pick().items() if k not in ('sport','competition','event','market','line','reference_odds','estimated_probability_pct','grade')}
        record['decision']='PASS'
        self.assertEqual(add_decision(self.decisions,record),'added')

    def test_settlement_does_not_modify_original(self):
        original = pick()
        add_decision(self.decisions,original)
        settlement=dict(decision_id=original['decision_id'],result_status='Win',final_score='7-6 6-4',settled_at_riga='2026-10-21T10:00:00+03:00',result_source_url='https://example.org/result',settlement_notes='Test only')
        self.assertEqual(settle_decision(self.decisions,self.settlements,settlement),'added')
        self.assertEqual(settle_decision(self.decisions,self.settlements,settlement),'duplicate')
        with self.decisions.open(newline='',encoding='utf-8') as f:
            self.assertEqual(next(csv.DictReader(f))['line'],'21.5')

    def test_candidate_can_be_settled_as_half_unit(self):
        original = {**pick(), 'decision':'CANDIDATE', 'grade':'B',
                    'rationale':'CANDIDATE — 0.5 virtual flat; no primary pick.'}
        self.assertEqual(add_decision(self.decisions, original), 'added')
        settlement = dict(
            decision_id=original['decision_id'],
            result_status='Win',
            final_score='2-1',
            settled_at_riga='2026-10-21T10:00:00+03:00',
            result_source_url='https://example.org/result',
            settlement_notes='CANDIDATE; settled separately as 0.5 virtual flat.',
        )
        self.assertEqual(settle_decision(self.decisions, self.settlements, settlement), 'added')

    def test_candidate_requires_explicit_half_unit_label(self):
        original = {**pick(), 'decision':'CANDIDATE', 'grade':'B', 'rationale':'Test only'}
        with self.assertRaises(ValueError):
            add_decision(self.decisions, original)

    def test_no_settlement_of_pass(self):
        record = {k:v for k,v in pick().items() if k not in ('sport','competition','event','market','line','reference_odds','estimated_probability_pct','grade')}
        record['decision']='PASS'
        add_decision(self.decisions,record)
        with self.assertRaises(ValueError):
            settle_decision(self.decisions,self.settlements,dict(decision_id=record['decision_id'],result_status='Win',settled_at_riga='2026-10-21T10:00:00+03:00',result_source_url='https://example.org'))

if __name__ == '__main__':
    unittest.main()
