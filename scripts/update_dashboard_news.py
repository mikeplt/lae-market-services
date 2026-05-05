#!/usr/bin/env python3
"""Fetches latest financial news from Alpha Vantage and updates dashboard-data.json."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "")
DATA_FILE = Path(__file__).parent.parent / "outputs" / "portal" / "dashboard-data.json"
NEWS_COUNT = 5


def fetch_news(api_key: str) -> list[dict]:
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=NEWS_SENTIMENT"
        f"&topics=financial_markets"
        f"&sort=LATEST"
        f"&limit=10"
        f"&apikey={api_key}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "LAE-Dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    articles = data.get("feed", [])
    result = []
    for a in articles[:NEWS_COUNT]:
        result.append({
            "title": a.get("title", ""),
            "source": a.get("source", ""),
            "time_published": a.get("time_published", ""),
            "url": a.get("url", ""),
        })
    return result


def main():
    if not API_KEY:
        print("ERROR: ALPHAVANTAGE_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    print("Fetching news from Alpha Vantage...")
    try:
        news = fetch_news(API_KEY)
    except urllib.error.URLError as e:
        print(f"ERROR: Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not news:
        print("WARNING: No articles returned.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {}
    data["news_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    data["news"] = news
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done. {len(news)} articles written to {DATA_FILE}")


if __name__ == "__main__":
    main()
