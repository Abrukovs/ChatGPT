"""Read-only connectivity probe for official KHL data endpoints.

Never updates predictions or settlements. Exit nonzero on failed checks.
"""
import json
import urllib.request
import urllib.parse
from html.parser import HTMLParser

BASE = "https://www.khl.ru/"
API = "https://www.khl.ru/rest/calendar/list/"


def main():
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor()
    )
    headers = {"User-Agent": "Mozilla/5.0 (compatible; KHLJournalProbe/1.0)"}
    with opener.open(urllib.request.Request(BASE, headers=headers), timeout=20) as response:
        page = response.read(1000000)
        print("KHL homepage HTTP:", response.status, "bytes:", len(page))
    data = urllib.parse.urlencode({"season": "2027", "stage": "regular"}).encode()
    request = urllib.request.Request(API, data=data, headers={
        **headers, "Content-Type": "application/x-www-form-urlencoded",
        "Referer": BASE,
    })
    with opener.open(request, timeout=25) as response:
        body = response.read(2000000)
        print("KHL calendar HTTP:", response.status, "bytes:", len(body),
              "content type:", response.headers.get("Content-Type"))
    if not body:
        raise RuntimeError("Empty response from KHL calendar")
    try:
        parsed = json.loads(body)
    except ValueError as exc:
        raise RuntimeError("Calendar response is not JSON; inspect API access") from exc
    print("KHL calendar JSON type:", type(parsed).__name__)
    if isinstance(parsed, dict):
        print("Top-level keys:", list(parsed)[:15])
    elif isinstance(parsed, list):
        print("Number of top-level items:", len(parsed))
    else:
        raise RuntimeError("Unexpected calendar response type")
    print("Read-only connectivity test complete; no journal data changed.")


if __name__ == "__main__":
    main()
