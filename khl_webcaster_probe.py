"""Read-only connectivity test for KHL Webcaster JSON endpoints.

No credentials, no journal modifications. The test verifies HTTP and JSON
structure only; a later test must validate scores and period semantics.
"""
import json
import urllib.error
import urllib.request

URLS = [
    "https://khl.api.webcaster.pro/api/khl_mobile/data.json?locale=en",
    "https://khl.api.webcaster.pro/api/khl_mobile/events_v2.json?locale=en",
]


def main():
    for url in URLS:
        request = urllib.request.Request(
            url, headers={"User-Agent": "KHL-Journal-Connectivity-Test/1.0",
                          "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read(2_000_000)
                status = response.status
                content_type = response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            print(f"Endpoint failed: HTTP {exc.code}: {url}", flush=True)
            raise
        parsed = json.loads(body)
        if not isinstance(parsed, (dict, list)):
            raise ValueError("Unexpected JSON structure")
        if not body:
            raise ValueError("Empty JSON body")
        print(f"OK: HTTP {status}, bytes={len(body)}, content_type={content_type}, "
              f"JSON={type(parsed).__name__}, endpoint={url}", flush=True)
        if isinstance(parsed, dict):
            print("Top-level keys:", list(parsed)[:12], flush=True)
    print("Connectivity passed. No CSV files were changed.", flush=True)


if __name__ == "__main__":
    main()
