"""Read-only structural audit of KHL Webcaster event data.

Prints schema and limited matching records for two known fixtures.
Does not infer betting results or change CSV files.
"""
import json
import urllib.request
from collections import Counter

URL = "https://khl.api.webcaster.pro/api/khl_mobile/events_v2.json?locale=en"
TARGETS = [
    ("2026-10-21", ("metallurg", "salavat")),
    ("2026-10-22", ("ska", "sibir")),
]


def get_events():
    request = urllib.request.Request(URL, headers={
        "User-Agent": "KHL-Journal-ReadOnly-Audit/1.0",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.load(response)
    if not isinstance(data, list):
        raise ValueError("Expected a list of events")
    return data


def shape(value, depth=0):
    if isinstance(value, dict):
        return {k: shape(v, depth + 1) for k, v in list(value.items())[:35]} if depth < 2 else "object"
    if isinstance(value, list):
        return {"type": "list", "length": len(value), "first": shape(value[0], depth + 1) if value and depth < 2 else None}
    return type(value).__name__


def main():
    events = get_events()
    print("Events returned:", len(events))
    print("Event types:", dict(Counter(type(x).__name__ for x in events)))
    if events:
        print("First event schema:", json.dumps(shape(events[0]), ensure_ascii=False))
        if isinstance(events[0], dict):
            # Print only date/status/score/team-relevant fields, not opaque metadata.
            safe_words = ("date", "time", "team", "home", "away", "score", "goal", "period", "status", "state", "id", "stage")
            sample = {k: v for k, v in events[0].items()
                      if any(w in k.lower() for w in safe_words)
                      and isinstance(v, (str, int, float, bool, type(None)))}
            print("First event selected scalar fields:", json.dumps(sample, ensure_ascii=False)[:2000])
    serialized = [(e, json.dumps(e, ensure_ascii=False).lower()) for e in events]
    for date, teams in TARGETS:
        matching = [(e, s) for e, s in serialized
                    if all(name in s for name in teams)]
        dated = [(e, s) for e, s in matching if date in s or date.replace("-", "") in s]
        print(f"Target {date}, teams {teams}: team_matches={len(matching)}, date_matches={len(dated)}")
        for event, _ in dated[:2]:
            print("Matching event:", json.dumps(event, ensure_ascii=False)[:4500])
    print("AUDIT ONLY: no scores interpreted and no journal files changed.")


if __name__ == "__main__":
    main()
