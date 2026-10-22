"""Read-only KHL Webcaster archive audit for Oct 21-22 2026.

Uses documented time-range filters, pages and stage_id. Does not write journals.
"""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://khl.api.webcaster.pro/api/khl_mobile/"
HEADERS = {"User-Agent": "KHL-Journal-Archive-Audit/1.0", "Accept": "application/json"}

def fetch(endpoint, params):
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=25) as response:
        data = json.load(response)
    return data

def describe(x):
    if isinstance(x, dict):
        return {k: describe(v) for k, v in x.items() if k in ("id", "khl_id", "name", "location", "score", "scores", "start_at", "game_state_key", "team_a", "team_b", "event", "stage_id", "first_period", "second_period", "third_period", "overtime", "bullitt", "period", "title")}
    if isinstance(x, list):
        return [describe(v) for v in x[:3]]
    return x

def main():
    data = fetch("data.json", {"locale":"en"})
    stages = data.get("stages_v2", [])
    print("Stage collection type:", type(stages).__name__)
    if isinstance(stages, list):
        for s in stages:
            label = json.dumps(s, ensure_ascii=False).lower()
            if any(t in label for t in ("26/27", "2026/2027", "2026-2027")):
                print("Candidate stage:", json.dumps(s, ensure_ascii=False)[:1300])
    # Moscow calendar dates 21 and 22 Oct, inclusive, in UTC:
    start = int(datetime(2026, 10, 20, 21, tzinfo=timezone.utc).timestamp())
    end = int(datetime(2026, 10, 22, 21, tzinfo=timezone.utc).timestamp())
    params = {
        "locale":"en", "q[start_at_gt_time_from_unixtime]":start,
        "q[start_at_lt_time_from_unixtime]":end,
        "order_direction":"asc", "page":1,
    }
    events = fetch("events_v2.json", params)
    print("Time-filtered page 1 count:", len(events), "type:", type(events).__name__)
    for obj in events[:16]:
        event = obj.get("event", obj) if isinstance(obj, dict) else obj
        print("Event:", json.dumps(describe(event), ensure_ascii=False)[:2400])
    if len(events) == 16:
        params["page"] = 2
        page2 = fetch("events_v2.json", params)
        print("Time-filtered page 2 count:", len(page2))
        for obj in page2[:16]:
            event = obj.get("event", obj) if isinstance(obj, dict) else obj
            print("Event:", json.dumps(describe(event), ensure_ascii=False)[:2400])
    print("READ ONLY: scores are not settled; CSV unchanged")

if __name__ == "__main__":
    main()
