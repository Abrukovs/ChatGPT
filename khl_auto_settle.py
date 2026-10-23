"""Automatically settle *unambiguous* KHL regulation team-total picks.

All other markets are left untouched. Requires exact match of team names,
date (Europe/Riga), stage, home/away and unique completed event.
"""
import csv
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from daily_decisions import FIELDS, SETTLEMENT_FIELDS, _read, settle_decision

API = "https://khl.api.webcaster.pro/api/khl_mobile/events_v2.json"
RIGA = ZoneInfo("Europe/Riga")
TEAM_ALIASES = {
    "metallurg magnitogorsk": "Metallurg Mg",
    "salavat yulaev": "Salavat Yulaev",
    "ska saint petersburg": "SKA",
    "sibir novosibirsk": "Sibir",
}
MARKET_RE = re.compile(r"^(.+?) team total (over|under) ([0-9]+(?:[.][0-9]+)?) goals in regulation$", re.I)


def parse_market(row):
    match = MARKET_RE.fullmatch(row["market"].strip())
    if not match:
        return None
    team, direction, threshold = match.groups()
    names = row["event"].split(" - ")
    if len(names) != 2:
        return None
    if team.lower() in (names[0].lower(), names[0].split()[0].lower()):
        side = "home"
    elif team.lower() in (names[1].lower(), names[1].split()[0].lower()):
        side = "away"
    else:
        return None
    if float(row["line"]) != float(threshold):
        raise ValueError("Market threshold disagrees with stored line")
    return side, direction.lower(), float(threshold)


def events_for_day(date):
    start = datetime.fromisoformat(date).replace(tzinfo=RIGA).astimezone(timezone.utc)
    end = (datetime.fromisoformat(date) + timedelta(days=1)).replace(tzinfo=RIGA).astimezone(timezone.utc)
    args = {"locale": "en",
            "q[start_at_gt_time_from_unixtime]": int(start.timestamp()),
            "q[start_at_lt_time_from_unixtime]": int(end.timestamp()),
            "order_direction": "asc", "page": 1}
    output = []
    for page in range(1, 6):
        args["page"] = page
        req = urllib.request.Request(API + "?" + urllib.parse.urlencode(args),
                headers={"User-Agent": "KHL-Journal-Settlement/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=25) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError("Unexpected KHL response")
        output.extend(v.get("event", v) for v in batch if isinstance(v, dict))
        if len(batch) < 16:
            return output
    raise RuntimeError("Archive pagination limit reached; refusing incomplete match search")


def regulation_goals(event):
    scores = event.get("scores")
    if not isinstance(scores, dict):
        raise ValueError("Missing period scores")
    result = [0, 0]
    for period in ("first_period", "second_period", "third_period"):
        value = scores.get(period)
        if not isinstance(value, str):
            raise ValueError("Missing period breakdown")
        pieces = value.split(":")
        if len(pieces) != 2 or not all(x.isdigit() for x in pieces):
            raise ValueError("Invalid period score")
        result[0] += int(pieces[0])
        result[1] += int(pieces[1])
    return result


def assess(decision, events):
    parsed = parse_market(decision)
    if parsed is None:
        return None
    side, direction, total = parsed
    names = [TEAM_ALIASES.get(s.strip().lower(), s.strip()) for s in decision["event"].split(" - ")]
    if len(names) != 2:
        return None
    matches = [e for e in events
               if e.get("team_a", {}).get("name") == names[0]
               and e.get("team_b", {}).get("name") == names[1]
               and e.get("game_state_key") == "finished"
               and e.get("stage_id") == 407]
    if len(matches) != 1:
        return None
    event = matches[0]
    regulation = regulation_goals(event)
    goals = regulation[0 if side == "home" else 1]
    success = (goals > total) if direction == "over" else (goals < total)
    return {
        "decision_id": decision["decision_id"],
        "result_status": "Win" if success else "Loss",
        "final_score": f"{regulation[0]}:{regulation[1]} regulation",
        "result_source_url": f"https://khl.api.webcaster.pro/api/khl_mobile/events_v2.json?locale=en",
        "settlement_notes": f"KHL event {event.get('khl_id')}; three periods; {goals} {side} goals; original market {decision['market']}",
    }


def main():
    decisions_path = Path("daily_decisions.csv")
    settlements_path = Path("settlements.csv")
    decisions = _read(decisions_path, FIELDS)
    existing = {r["decision_id"] for r in _read(settlements_path, SETTLEMENT_FIELDS)}
    cache = {}
    count = 0
    for row in decisions:
        if row["decision"] != "PICK" or row["sport"] != "hockey" or row["decision_id"] in existing:
            continue
        if parse_market(row) is None:
            print("Unsupported market; manual review:", row["decision_id"])
            continue
        date = row["date_riga"]
        if date not in cache:
            cache[date] = events_for_day(date)
        candidate = assess(row, cache[date])
        if not candidate:
            print("Match not uniquely confirmed:", row["decision_id"])
            continue
        candidate["settled_at_riga"] = datetime.now(RIGA).isoformat(timespec="seconds")
        print("Verified candidate:", candidate["decision_id"], candidate["result_status"], candidate["final_score"])
        if os.environ.get("DRY_RUN", "true").lower() != "false":
            continue
        settle_decision(decisions_path, settlements_path, candidate)
        existing.add(row["decision_id"])
        count += 1
    print("New settlements:", count, "dry-run:", os.environ.get("DRY_RUN", "true"))


if __name__ == "__main__":
    main()
