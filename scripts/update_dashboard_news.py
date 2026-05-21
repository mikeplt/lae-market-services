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
NEWS_COUNT = 6
FETCH_LIMIT = 50  # Fetch more to have enough after filtering

# Preferred sources in priority order – max 1 article per source
PREFERRED_SOURCES = [
    "Reuters",
    "Bloomberg",
    "CNBC",
    "The Wall Street Journal",
    "Financial Times",
    "MarketWatch",
    "Barron's",
    "Forbes",
    "Yahoo Finance",
    "Business Insider",
    "Benzinga",
    "Seeking Alpha",
    "The Motley Fool",
    "Zacks",
    "InvestorPlace",
    "TheStreet",
    "MarketBeat",
    "Stock Titan",
    "Investopedia",
    "Market Index",
]


def fetch_news(api_key: str) -> list[dict]:
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=NEWS_SENTIMENT"
        f"&topics=financial_markets"
        f"&sort=LATEST"
        f"&limit={FETCH_LIMIT}"
        f"&apikey={api_key}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "LAE-Dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if "feed" not in data:
        note = data.get("Note") or data.get("Information") or data.get("message") or str(data)
        print(f"WARNING: Alpha Vantage returned no feed. API response: {note}", file=sys.stderr)
    return data.get("feed", [])


def select_articles(articles: list[dict]) -> list[dict]:
    """Pick up to NEWS_COUNT articles, preferred sources first (max 1 per source), then fallback."""
    seen_sources = set()
    result = []

    # Pass 1: preferred sources, max 1 per source
    for source_name in PREFERRED_SOURCES:
        if len(result) >= NEWS_COUNT:
            break
        for a in articles:
            if len(result) >= NEWS_COUNT:
                break
            src = a.get("source", "")
            if source_name.lower() in src.lower() and src not in seen_sources:
                seen_sources.add(src)
                result.append({
                    "title": a.get("title", ""),
                    "source": src,
                    "time_published": a.get("time_published", ""),
                    "url": a.get("url", ""),
                })

    # Pass 2: fill remaining slots with any unused article
    if len(result) < NEWS_COUNT:
        used_titles = {r["title"] for r in result}
        for a in articles:
            if len(result) >= NEWS_COUNT:
                break
            title = a.get("title", "")
            if title not in used_titles:
                used_titles.add(title)
                result.append({
                    "title": title,
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
        articles = fetch_news(API_KEY)
    except urllib.error.URLError as e:
        print(f"ERROR: Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not articles:
        print("WARNING: No articles returned – keeping existing news data.", file=sys.stderr)
        sys.exit(0)

    news = select_articles(articles)
    sources = [n["source"] for n in news]
    print(f"Selected {len(news)} articles from: {', '.join(sources)}")

    data = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {}
    data["news_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    data["news"] = news
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done. {len(news)} articles written to {DATA_FILE}")


if __name__ == "__main__":
    main()
