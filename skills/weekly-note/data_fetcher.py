"""
LAE Market Services – Weekly Note Data Fetcher
Uses Alpha Vantage API for reliable data fetching in CI/CD environments.
"""

import os
import csv
import time
import json
import requests
from datetime import datetime, timedelta, date
from google import genai


# ── Configuration ─────────────────────────────────────────────────────────────

BASE_URL = "https://www.alphavantage.co/query"

INDEX_TICKERS = {
    "sp500":   ("SPY", "S&P 500"),
    "nasdaq":  ("QQQ", "Nasdaq 100"),
    "dow":     ("DIA", "Dow Jones"),
    "russell": ("IWM", "Russell 2000"),
}

TECH_TICKERS = {
    "es": ("SPY", "S&P 500 (SPY)"),
    "nq": ("QQQ", "Nasdaq 100 (QQQ)"),
}

TOP_EARNINGS_TICKERS = {
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA",
    "JPM", "UNH", "V", "XOM", "JNJ", "PG", "MA", "HD", "COST", "LLY",
    "AVGO", "ABBV", "MRK", "KO", "PEP", "ADBE", "CRM", "AMD", "ORCL",
    "CSCO", "IBM", "INTC", "NOW", "QCOM", "TXN", "AMAT", "MU", "LRCX",
    "GS", "MS", "BAC", "WFC", "C",
}

_DAY_EN = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}


# ── API helper ────────────────────────────────────────────────────────────────

def _get(params: dict, is_csv: bool = False):
    """Rate-limited request to Alpha Vantage (max 5 requests/minute on free tier)."""
    time.sleep(13)  # 13s gap → safe margin below 5/min limit
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")
    params["apikey"] = api_key
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text if is_csv else resp.json()


# ── Helper functions ───────────────────────────────────────────────────────────

def _pct(new_val: float, old_val: float) -> str:
    if old_val == 0:
        return "n/a"
    pct = (new_val - old_val) / old_val * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def _next_week_range() -> tuple[date, date]:
    today = datetime.now()
    days_until_monday = (7 - today.weekday()) % 7 or 7
    next_monday = (today + timedelta(days=days_until_monday)).date()
    return next_monday, next_monday + timedelta(days=4)


# ── Index performance ──────────────────────────────────────────────────────────

def get_index_performance() -> dict:
    """Weekly % change for the four main indices via TIME_SERIES_WEEKLY."""
    result = {}
    for key, (ticker, name) in INDEX_TICKERS.items():
        try:
            data = _get({"function": "TIME_SERIES_WEEKLY", "symbol": ticker})
            series = data.get("Weekly Time Series", {})
            if not series:
                raise ValueError("Empty response")
            dates = sorted(series.keys(), reverse=True)
            close_now  = float(series[dates[0]]["4. close"])
            close_prev = float(series[dates[1]]["4. close"])
            perf = _pct(close_now, close_prev)
            result[key] = {"name": name, "woche": perf, "positiv": close_now >= close_prev}
        except Exception as e:
            print(f"    Warning [{ticker}]: {e}")
            result[key] = {"name": name, "woche": "n/a", "positiv": True}
    return result


# ── Sector performance ────────────────────────────────────────────────────────

def get_sector_performance() -> tuple[list, list]:
    """Top-2 and Flop-2 sectors via Alpha Vantage SECTOR endpoint (5-day = weekly)."""
    try:
        data = _get({"function": "SECTOR"})
        week_perf = data.get("Rank C: 5 Day Performance", {})
        if not week_perf:
            return [], []

        performances = []
        for name, pct_str in week_perf.items():
            try:
                pct = float(pct_str.replace("%", ""))
                sign = "+" if pct >= 0 else ""
                performances.append({"name": name, "kuerzel": "", "perf": f"{sign}{pct:.1f}%", "pct": pct})
            except Exception:
                continue

        performances.sort(key=lambda x: x["pct"], reverse=True)
        top  = [{"name": s["name"], "kuerzel": s["kuerzel"], "perf": s["perf"]} for s in performances[:2]]
        flop = [{"name": s["name"], "kuerzel": s["kuerzel"], "perf": s["perf"]} for s in performances[-2:]]
        return top, flop
    except Exception as e:
        print(f"    Warning [SECTOR]: {e}")
        return [], []


# ── Technical levels ──────────────────────────────────────────────────────────

def get_technical_levels() -> dict:
    """Bias, support and resistance for SPY and QQQ via TIME_SERIES_DAILY."""
    result = {}
    for key, (ticker, label) in TECH_TICKERS.items():
        try:
            data = _get({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
            series = data.get("Time Series (Daily)", {})
            if not series:
                raise ValueError("Empty response")

            dates = sorted(series.keys(), reverse=True)[:60]
            closes = [float(series[d]["4. close"]) for d in dates]
            highs  = [float(series[d]["2. high"])  for d in dates]
            lows   = [float(series[d]["3. low"])   for d in dates]

            current    = closes[0]
            ma20       = sum(closes[:20]) / 20
            support    = min(lows[:14])
            resistance = max(highs[:14])
            bias       = "Uptrend" if current > ma20 else "Downtrend"

            result[key] = {
                "label":      label,
                "bias":       bias,
                "support":    f"{support:,.2f}",
                "resistance": f"{resistance:,.2f}",
            }
        except Exception as e:
            print(f"    Warning [{ticker}]: {e}")
            result[key] = {"label": label, "bias": "n/a", "support": "n/a", "resistance": "n/a"}
    return result


# ── Earnings calendar ─────────────────────────────────────────────────────────

def get_earnings_calendar() -> list:
    """Upcoming earnings for next week via Alpha Vantage EARNINGS_CALENDAR."""
    next_mon, next_fri = _next_week_range()
    try:
        csv_text = _get({"function": "EARNINGS_CALENDAR", "horizon": "3month"}, is_csv=True)
        reader = csv.DictReader(csv_text.splitlines())
        earnings_next_week = []

        for row in reader:
            symbol = row.get("symbol", "")
            if symbol not in TOP_EARNINGS_TICKERS:
                continue
            try:
                report_date = datetime.strptime(row["reportDate"], "%Y-%m-%d").date()
            except Exception:
                continue
            if not (next_mon <= report_date <= next_fri):
                continue

            eps_str = "n/a"
            try:
                eps_val = float(row.get("estimate", ""))
                eps_str = f"{eps_val:.2f}"
            except Exception:
                pass

            earnings_next_week.append({
                "ticker":  symbol,
                "name":    row.get("name", symbol),
                "tag":     _DAY_EN.get(report_date.weekday(), "?"),
                "eps_erw": eps_str,
                "datum":   report_date,
            })

        earnings_next_week.sort(key=lambda x: x["datum"])
        for e in earnings_next_week:
            e.pop("datum", None)

        if not earnings_next_week:
            return [{"ticker": "–", "name": "No earnings data available", "tag": "–", "eps_erw": "–"}]
        return earnings_next_week[:5]

    except Exception as e:
        print(f"    Warning [EARNINGS_CALENDAR]: {e}")
        return [{"ticker": "–", "name": "No earnings data available", "tag": "–", "eps_erw": "–"}]


# ── Macro calendar ────────────────────────────────────────────────────────────

def get_macro_calendar() -> list:
    """Heuristic macro calendar for next week based on recurring US data releases."""
    next_mon, next_fri = _next_week_range()
    events = []
    day = next_mon
    while day <= next_fri:
        wd, dom = day.weekday(), day.day
        if wd == 3:
            events.append({"tag": "Thu", "event": "Initial Jobless Claims", "uhrzeit": "08:30"})
        if wd == 4 and dom <= 7:
            events.append({"tag": "Fri", "event": "Nonfarm Payrolls (NFP) – Employment & Unemployment Rate", "uhrzeit": "08:30"})
        if wd == 1 and 8 <= dom <= 14:
            events.append({"tag": "Tue", "event": "Consumer Price Index (CPI)", "uhrzeit": "08:30"})
        if wd == 2 and 8 <= dom <= 15:
            events.append({"tag": "Wed", "event": "Producer Price Index (PPI) / Retail Sales", "uhrzeit": "08:30"})
        if wd == 3 and 15 <= dom <= 21:
            events.append({"tag": "Thu", "event": "Philly Fed Manufacturing Index", "uhrzeit": "08:30"})
        if wd == 4 and 15 <= dom <= 21:
            events.append({"tag": "Fri", "event": "Flash PMI (Manufacturing & Services)", "uhrzeit": "09:45"})
        day += timedelta(days=1)

    if not events:
        events.append({"tag": "–", "event": "No major data releases this week", "uhrzeit": "–"})
    return events[:5]


# ── Narrative via Gemini API ──────────────────────────────────────────────────

def generate_narrative(data: dict) -> dict:
    """Generates headline and market commentary via Google Gemini."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"headline": "Weekly Review – set GEMINI_API_KEY to enable", "body": "No API key found."}
    try:
        client = genai.Client(api_key=api_key)
        idx_lines   = "\n".join(f"  {v['name']}: {v['woche']}" for v in data["indizes"].values())
        top_lines   = ", ".join(f"{s['name']} ({s['perf']})" for s in data["sektor_top"])
        flop_lines  = ", ".join(f"{s['name']} ({s['perf']})" for s in data["sektor_flop"])
        earn_lines  = ", ".join(f"{e['ticker']} ({e['tag']})" for e in data["earnings"][:3] if e["ticker"] != "–")
        macro_lines = ", ".join(f"{m['event']} ({m['tag']})" for m in data["makro"][:3])

        prompt = f"""You are a professional market analyst for LAE Market Services.
Write a concise English weekly market review for CW {data['kw']}.

Last week's market data:
Indices:
{idx_lines}

Top sectors: {top_lines if top_lines else 'no data'}
Weakest sectors: {flop_lines if flop_lines else 'no data'}

Next week:
Earnings: {earn_lines if earn_lines else 'no major releases'}
Macro: {macro_lines if macro_lines else 'no major data'}

Create:
1. A punchy headline (max 12 words, no quotes)
2. A market commentary (4–5 sentences, factual, professional, in English, tone: direct and clear)

Format – reply ONLY in this JSON format without markdown blocks:
{{"headline": "...", "body": "..."}}"""

        response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)
        return {"headline": parsed.get("headline", "Weekly Review"), "body": parsed.get("body", "")}
    except Exception as e:
        return {"headline": f"Weekly Review CW {data['kw']}", "body": f"Narrative could not be generated: {e}"}


# ── Main function ─────────────────────────────────────────────────────────────

def fetch_all() -> dict:
    now = datetime.now()
    kw  = now.isocalendar()[1]
    months_en = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
                 7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"}
    datum_str = f"{months_en[now.month]} {now.day}, {now.year}"

    print("  [1/5] Fetching index performance ...")
    indizes = get_index_performance()

    print("  [2/5] Fetching sector performance ...")
    sektor_top, sektor_flop = get_sector_performance()

    print("  [3/5] Calculating technical levels ...")
    technisch = get_technical_levels()

    print("  [4/5] Fetching earnings calendar ...")
    earnings = get_earnings_calendar()

    print("  [5/6] Building macro calendar ...")
    makro = get_macro_calendar()

    data = {
        "kw":          kw,
        "datum":       datum_str,
        "indizes":     indizes,
        "sektor_top":  sektor_top,
        "sektor_flop": sektor_flop,
        "technisch":   technisch,
        "earnings":    earnings,
        "makro":       makro,
    }

    print("  [6/6] Generating narrative via Gemini API ...")
    data["narrative"] = generate_narrative(data)

    return data
