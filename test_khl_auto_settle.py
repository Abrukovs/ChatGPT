import unittest
from khl_auto_settle import parse_market, assess, regulation_goals

def decision(market, event="SKA Saint Petersburg - Sibir Novosibirsk", line="3.5"):
    return {"market":market,"event":event,"line":line,"decision_id":"test"}

def event(home="SKA", away="Sibir", scores=None):
    return {"team_a":{"name":home},"team_b":{"name":away},"game_state_key":"finished",
            "stage_id":407,"khl_id":902168,"scores":scores or {
            "first_period":"4:3","second_period":"1:0","third_period":"1:0",
            "overtime":None,"bullitt":None}}

class SettlementTests(unittest.TestCase):
    def test_original_ska_loss(self):
        row=decision("SKA team total under 3.5 goals in regulation")
        self.assertEqual(assess(row,[event()])["result_status"],"Loss")
    def test_original_metallurg_win(self):
        row=decision("Metallurg team total over 2.5 goals in regulation",
                     "Metallurg Magnitogorsk - Salavat Yulaev","2.5")
        game=event("Metallurg Mg","Salavat Yulaev",{
            "first_period":"3:1","second_period":"0:0","third_period":"1:3",
            "overtime":"0:0","bullitt":"0:1"})
        self.assertEqual(assess(row,[game])["result_status"],"Win")
        self.assertEqual(assess(row,[game])["final_score"],"4:4 regulation")
    def test_missing_period_rejected(self):
        with self.assertRaises(ValueError):
            regulation_goals(event(scores={"first_period":"1:0"}))
    def test_wrong_line_rejected(self):
        with self.assertRaises(ValueError):
            parse_market(decision("SKA team total under 2.5 goals in regulation"))
    def test_unsupported_market_skipped(self):
        self.assertIsNone(parse_market(decision("SKA moneyline")))
    def test_ambiguous_matches_skipped(self):
        row=decision("SKA team total under 3.5 goals in regulation")
        self.assertIsNone(assess(row,[event(),event()]))
    def test_away_total(self):
        row=decision("Sibir team total over 2.5 goals in regulation", line="2.5")
        self.assertEqual(assess(row,[event()])["result_status"],"Win")

if __name__=="__main__":
    unittest.main()
