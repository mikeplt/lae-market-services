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

SECTOR_ETFS = {
    "XLK":  "Technology",
    "XLE":  "Energy",
    "XLF":  "Financials",
    "XLV":  "Health Care",
    "XLI":  "Industrials",
    "XLP":  "Cons. Staples",
}

MACRO_ASSET_ETFS = {
    "gold": ("GLD", "Gold"),
    "oil":  ("USO", "Crude Oil"),
    "dxy":  ("UUP", "US Dollar"),
}

TOP_EARNINGS_TICKERS = {
    # Mega Cap
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA",
    "AVGO", "LLY", "JPM", "V", "UNH", "XOM", "WMT", "MA",
    # Financials
    "BAC", "GS", "MS", "WFC", "C", "SCHW", "AXP", "BLK", "SPGI",
    "MCO", "CME", "ICE", "PNC", "USB", "ADP", "FI", "FISV", "MMC", "AON",
    # Tech & Semiconductors
    "ORCL", "CRM", "ADBE", "CSCO", "IBM", "INTC", "QCOM", "TXN",
    "AMD", "MU", "AMAT", "LRCX", "KLAC", "MCHP", "ADI", "SNPS", "CDNS",
    "NOW", "PANW", "CRWD", "NET", "DDOG", "FTNT", "INTU",
    # Healthcare & Pharma
    "JNJ", "ABBV", "MRK", "LLY", "PFE", "AMGN", "GILD", "REGN",
    "VRTX", "BMY", "TMO", "ABT", "MDT", "SYK", "BSX", "ISRG", "ELV",
    "CI", "HCA", "ZTS",
    # Consumer
    "HD", "COST", "WMT", "TGT", "LOW", "TJX", "ROST", "LULU", "NKE",
    "MCD", "SBUX", "YUM", "CMG", "ABNB", "UBER",
    "KO", "PEP", "PM", "MO", "MDLZ", "CL", "KMB", "GIS", "HSY", "EL", "PG",
    # Industrials & Energy
    "CAT", "DE", "RTX", "GE", "ETN", "ITW", "HON", "MMM", "SHW",
    "XOM", "CVX", "COP", "OXY", "SLB", "HAL", "EOG", "MPC", "PSX", "VLO",
    # Communication & Media
    "GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ",
    # Real Estate & Utilities
    "PLD", "AMT", "EQIX", "CCI", "PSA", "WELL", "SPG", "CEG",
    "NEE", "SO", "DUK",
    # Other Large Cap
    "ACN", "LIN", "APD", "DHR", "PYPL", "SHOP", "MELI", "F", "GM",
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
    """Weekly % change + prior-week % change for the four main indices via TIME_SERIES_WEEKLY."""
    result = {}
    for key, (ticker, name) in INDEX_TICKERS.items():
        try:
            data = _get({"function": "TIME_SERIES_WEEKLY", "symbol": ticker})
            series = data.get("Weekly Time Series", {})
            if not series:
                raise ValueError("Empty response")
            dates = sorted(series.keys(), reverse=True)
            close_now   = float(series[dates[0]]["4. close"])
            close_prev  = float(series[dates[1]]["4. close"])
            close_prev2 = float(series[dates[2]]["4. close"])
            woche      = _pct(close_now,  close_prev)
            woche_prev = _pct(close_prev, close_prev2)
            pct_now    = (close_now  - close_prev)  / close_prev
            pct_before = (close_prev - close_prev2) / close_prev2
            result[key] = {
                "name": name,
                "woche": woche,
                "woche_prev": woche_prev,
                "positiv": close_now >= close_prev,
                "momentum_up": pct_now >= pct_before,
            }
        except Exception as e:
            print(f"    Warning [{ticker}]: {e}")
            result[key] = {"name": name, "woche": "n/a", "woche_prev": "n/a", "positiv": True, "momentum_up": True}
    return result


# ── Sector performance ────────────────────────────────────────────────────────

def get_sector_performance() -> tuple[list, list]:
    """Top-2 and Flop-2 sectors via TIME_SERIES_WEEKLY, including prior-week performance for WoW comparison."""
    performances = []
    for etf, name in SECTOR_ETFS.items():
        try:
            data = _get({"function": "TIME_SERIES_WEEKLY", "symbol": etf})
            series = data.get("Weekly Time Series", {})
            if not series:
                continue
            dates = sorted(series.keys(), reverse=True)
            close_now   = float(series[dates[0]]["4. close"])
            close_prev  = float(series[dates[1]]["4. close"])
            close_prev2 = float(series[dates[2]]["4. close"])
            pct      = (close_now  - close_prev)  / close_prev  * 100
            pct_prev = (close_prev - close_prev2) / close_prev2 * 100
            sign      = "+" if pct >= 0 else ""
            sign_prev = "+" if pct_prev >= 0 else ""
            performances.append({
                "name": name, "kuerzel": etf,
                "perf": f"{sign}{pct:.1f}%", "pct": pct,
                "perf_prev": f"{sign_prev}{pct_prev:.1f}%",
            })
        except Exception as e:
            print(f"    Warning [{etf}]: {e}")
            continue

    if not performances:
        return [], []
    performances.sort(key=lambda x: x["pct"], reverse=True)
    top  = [{"name": s["name"], "kuerzel": s["kuerzel"], "perf": s["perf"], "perf_prev": s["perf_prev"]} for s in performances[:2]]
    flop = [{"name": s["name"], "kuerzel": s["kuerzel"], "perf": s["perf"], "perf_prev": s["perf_prev"]} for s in performances[-2:]]
    return top, flop


# ── Macro assets ──────────────────────────────────────────────────────────────

def get_macro_assets() -> dict:
    """Weekly % change and current price for Gold (GLD), Oil (USO), Dollar (UUP), 10Y Yield."""
    result = {}

    for key, (ticker, name) in MACRO_ASSET_ETFS.items():
        try:
            data = _get({"function": "TIME_SERIES_WEEKLY", "symbol": ticker})
            series = data.get("Weekly Time Series", {})
            if not series:
                raise ValueError("Empty response")
            dates = sorted(series.keys(), reverse=True)
            close_now  = float(series[dates[0]]["4. close"])
            close_prev = float(series[dates[1]]["4. close"])
            result[key] = {
                "name": name,
                "price": f"{close_now:.2f}",
                "wow": _pct(close_now, close_prev),
                "positiv": close_now >= close_prev,
            }
        except Exception as e:
            print(f"    Warning [{ticker}]: {e}")
            result[key] = {"name": name, "price": "n/a", "wow": "n/a", "positiv": True}

    try:
        data = _get({"function": "TREASURY_YIELD", "interval": "weekly", "maturity": "10year"})
        yields = data.get("data", [])
        if len(yields) < 2:
            raise ValueError("Insufficient data")
        y_now  = float(yields[0]["value"])
        y_prev = float(yields[1]["value"])
        delta_bp = round((y_now - y_prev) * 100)
        sign = "+" if delta_bp >= 0 else ""
        result["yield10y"] = {
            "name": "10Y Yield",
            "price": f"{y_now:.2f}%",
            "wow": f"{sign}{delta_bp}bp",
            "positiv": y_now >= y_prev,
        }
    except Exception as e:
        print(f"    Warning [TREASURY_YIELD]: {e}")
        result["yield10y"] = {"name": "10Y Yield", "price": "n/a", "wow": "n/a", "positiv": True}

    return result


# ── Earnings calendar ─────────────────────────────────────────────────────────

def get_earnings_calendar() -> list:
    """Next week's earnings for large-cap US companies via Alpha Vantage EARNINGS_CALENDAR."""
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

        if earnings_next_week:
            return earnings_next_week[:10]

        return [{"ticker": "–", "name": "No major earnings next week", "tag": "–", "eps_erw": "–"}]

    except Exception as e:
        print(f"    Warning [EARNINGS_CALENDAR]: {e}")
        return [{"ticker": "–", "name": "No earnings data available", "tag": "–", "eps_erw": "–"}]


# ── Macro calendar ────────────────────────────────────────────────────────────

# Keywords that identify Investing.com 3-star US events (case-insensitive substring match)
_THREE_STAR_KEYWORDS = [
    "nonfarm payroll", "unemployment rate",
    "consumer price index", " cpi ",
    "core cpi", "core inflation",
    "producer price index", " ppi ",
    "pce price", "core pce", "personal income", "personal spending",
    "retail sales",
    "fomc", "federal funds rate", "fed rate",
    "gdp", "gross domestic product",
    "ism manufacturing", "ism non-manufacturing", "ism services",
    "adp non-farm", "adp employment", "adp nonfarm",
    "initial jobless claims", "jobless claims", "continuing claims",
    "philly fed", "philadelphia fed",
    "consumer confidence", "cb consumer",
    "michigan consumer sentiment", "umich",
    "flash manufacturing pmi", "flash services pmi", "flash composite pmi",
    "s&p global", "markit pmi",
    "building permits", "housing starts",
    "existing home sales", "new home sales",
    "durable goods",
    "trade balance", "goods trade balance",
    "cb leading", "leading economic index",
    "jolts", "job openings",
    "crude oil inventories", "crude oil stocks", "eia crude",
    "crude oil stock change", "petroleum status",
]

def _is_three_star(event_name: str) -> bool:
    name = f" {event_name.lower()} "
    return any(kw in name for kw in _THREE_STAR_KEYWORDS)


def _event_priority(event_name: str) -> int:
    """Lower = more important. Used to rank events when the 10-slot limit is reached."""
    n = event_name.lower()
    # Tier 1 – market-moving top releases
    if any(k in n for k in ["fomc rate", "federal funds rate", "rate decision", "interest rate decision"]): return 1
    if any(k in n for k in ["nonfarm payroll", "unemployment rate"]): return 2
    if any(k in n for k in ["consumer price index", " cpi ", "core cpi", "core inflation"]): return 3
    if any(k in n for k in ["gdp", "gross domestic product"]): return 4
    if any(k in n for k in ["pce price", "core pce", "personal income", "personal spending"]): return 5
    # Tier 2 – very important
    if any(k in n for k in ["flash", "s&p global", "markit pmi", "manufacturing pmi", "services pmi", "composite pmi"]): return 10
    if any(k in n for k in ["ism manufacturing", "ism non-manufacturing", "ism services"]): return 11
    if any(k in n for k in ["retail sales"]): return 12
    if any(k in n for k in ["fomc minutes", "fomc meeting minutes", "fomc"]): return 13
    if any(k in n for k in ["producer price index", " ppi "]): return 14
    if any(k in n for k in ["adp non-farm", "adp nonfarm", "adp employment"]): return 15
    # Tier 3 – important
    if any(k in n for k in ["initial jobless claims", "jobless claims", "continuing claims"]): return 20
    if any(k in n for k in ["philly fed", "philadelphia fed"]): return 21
    if any(k in n for k in ["consumer confidence", "cb consumer"]): return 22
    if any(k in n for k in ["michigan consumer sentiment", "umich"]): return 23
    if any(k in n for k in ["jolts", "job openings"]): return 24
    if any(k in n for k in ["durable goods"]): return 25
    if any(k in n for k in ["trade balance", "goods trade balance"]): return 26
    if any(k in n for k in ["crude oil inventories", "crude oil stocks", "eia crude", "petroleum status", "crude oil stock change"]): return 27
    # Tier 4 – standard 3-star
    if any(k in n for k in ["housing starts", "building permits"]): return 30
    if any(k in n for k in ["existing home sales", "new home sales"]): return 31
    if any(k in n for k in ["cb leading", "leading economic index"]): return 32
    return 50


def _utc_hhmm_to_et(dt_utc: datetime, event_date: date) -> str:
    """Convert UTC datetime to HH:MM ET string, respecting EDT/EST transitions."""
    year = event_date.year
    march1 = date(year, 3, 1)
    edt_start = march1 + timedelta(days=(6 - march1.weekday()) % 7) + timedelta(weeks=1)
    nov1 = date(year, 11, 1)
    edt_end = nov1 + timedelta(days=(6 - nov1.weekday()) % 7)
    offset = 4 if edt_start <= event_date < edt_end else 5
    dt_et = dt_utc - timedelta(hours=offset)
    return dt_et.strftime("%H:%M")


def _finnhub_macro_calendar(next_mon: date, next_fri: date) -> list:
    """Fetch high/medium-impact US economic events from Finnhub economic calendar API."""
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        raise ValueError("FINNHUB_API_KEY not set")

    url = "https://finnhub.io/api/v1/calendar/economic"
    params = {
        "from":  next_mon.strftime("%Y-%m-%d"),
        "to":    next_fri.strftime("%Y-%m-%d"),
        "token": api_key,
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    raw = resp.json().get("economicCalendar", [])

    events = []
    for item in raw:
        if item.get("country") != "US":
            continue
        if item.get("impact", "").lower() not in ("high", "medium"):
            continue
        event_name = item.get("event", "").strip()
        if not event_name or not _is_three_star(event_name):
            continue
        time_str = item.get("time", "")
        try:
            dt_utc = datetime.strptime(time_str[:16], "%Y-%m-%d %H:%M")
            event_date = dt_utc.date()
            if not (next_mon <= event_date <= next_fri):
                continue
            time_et = "TBA" if (dt_utc.hour == 0 and dt_utc.minute == 0) else _utc_hhmm_to_et(dt_utc, event_date)
            tag = _DAY_EN[event_date.weekday()]
        except Exception:
            continue
        events.append({
            "tag": tag, "event": event_name, "uhrzeit": time_et,
            "_date": time_str[:10], "_priority": _event_priority(event_name), "_sort": time_str,
        })

    events.sort(key=lambda x: (x["_date"], x["_priority"], x["_sort"]))
    for e in events:
        e.pop("_date")
        e.pop("_priority")
        e.pop("_sort")
    return events


def _heuristic_macro_calendar(next_mon: date, next_fri: date) -> list:
    """Last-resort fallback: recurring US events by week-of-month pattern."""
    events = []
    day = next_mon
    while day <= next_fri:
        wd, dom = day.weekday(), day.day
        tag = _DAY_EN[wd]
        if wd == 3:
            events.append({"tag": tag, "event": "Initial Jobless Claims", "uhrzeit": "08:30"})
        if wd == 4 and dom <= 7:
            events.append({"tag": tag, "event": "Nonfarm Payrolls & Unemployment Rate", "uhrzeit": "08:30"})
        if wd == 1 and 8 <= dom <= 14:
            events.append({"tag": tag, "event": "Consumer Price Index (CPI)", "uhrzeit": "08:30"})
        if wd == 2 and 8 <= dom <= 15:
            events.append({"tag": tag, "event": "PPI / Retail Sales", "uhrzeit": "08:30"})
        if wd == 0 and 15 <= dom <= 21:
            events.append({"tag": tag, "event": "NAHB Housing Market Index", "uhrzeit": "10:00"})
        if wd == 1 and 15 <= dom <= 21:
            events.append({"tag": tag, "event": "Building Permits & Housing Starts", "uhrzeit": "08:30"})
        if wd == 3 and 15 <= dom <= 21:
            events.append({"tag": tag, "event": "Philly Fed Manufacturing Index", "uhrzeit": "08:30"})
        if wd == 4 and 15 <= dom <= 21:
            events.append({"tag": tag, "event": "Flash PMI (Manufacturing & Services)", "uhrzeit": "09:45"})
        if wd == 3 and 22 <= dom <= 28:
            events.append({"tag": tag, "event": "Existing Home Sales", "uhrzeit": "10:00"})
            events.append({"tag": tag, "event": "CB Leading Economic Index", "uhrzeit": "10:00"})
        if wd == 4 and dom >= 25:
            events.append({"tag": tag, "event": "PCE Price Index / Personal Income & Spending", "uhrzeit": "08:30"})
        day += timedelta(days=1)
    if not events:
        events.append({"tag": "–", "event": "No major data releases this week", "uhrzeit": "–"})
    return events[:8]


def get_macro_calendar() -> list:
    """High-impact US economic events for next week. Sources: Finnhub → heuristic fallback."""
    next_mon, next_fri = _next_week_range()

    # Primary: Finnhub API
    try:
        events = _finnhub_macro_calendar(next_mon, next_fri)
        if events:
            return events[:10]
        print("    Warning [MACRO_CALENDAR]: Finnhub returned no events, using heuristic")
    except Exception as e:
        print(f"    Warning [MACRO_CALENDAR]: Finnhub failed ({e}), using heuristic")

    # Fallback: heuristic
    return _heuristic_macro_calendar(next_mon, next_fri)


# ── Narrative via Gemini API ──────────────────────────────────────────────────

def generate_narrative(data: dict) -> dict:
    """Generates headline and market commentary via Google Gemini."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"headline": "Weekly Review – set GEMINI_API_KEY to enable", "body": "No API key found."}
    try:
        client = genai.Client(api_key=api_key)
        idx_lines   = "\n".join(f"  {v['name']}: {v['woche']} (prev: {v['woche_prev']})" for v in data["indizes"].values())
        top_lines   = ", ".join(f"{s['name']} ({s['perf']}, prev: {s['perf_prev']})" for s in data["sektor_top"])
        flop_lines  = ", ".join(f"{s['name']} ({s['perf']}, prev: {s['perf_prev']})" for s in data["sektor_flop"])
        macro_asset_lines = ", ".join(f"{v['name']}: {v['wow']} @ {v['price']}" for v in data["macro_assets"].values())
        earn_lines  = ", ".join(f"{e['ticker']} ({e['tag']})" for e in data["earnings"][:3] if e["ticker"] != "–")
        macro_lines = ", ".join(f"{m['event']} ({m['tag']})" for m in data["makro"][:3])

        prompt = f"""You are a professional market analyst for LAE Market Services.
Write a concise English weekly market review for CW {data['kw']}.

Last week's market data:
Indices (this week / prev week):
{idx_lines}

Top sectors: {top_lines if top_lines else 'no data'}
Weakest sectors: {flop_lines if flop_lines else 'no data'}

Macro assets (WoW change @ current level): {macro_asset_lines if macro_asset_lines else 'no data'}

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

    print("  [3/5] Fetching macro assets ...")
    macro_assets = get_macro_assets()

    print("  [4/5] Fetching earnings calendar ...")
    earnings = get_earnings_calendar()

    print("  [5/6] Building macro calendar ...")
    makro = get_macro_calendar()

    data = {
        "kw":           kw,
        "datum":        datum_str,
        "indizes":      indizes,
        "sektor_top":   sektor_top,
        "sektor_flop":  sektor_flop,
        "macro_assets": macro_assets,
        "earnings":     earnings,
        "makro":        makro,
    }

    print("  [6/6] Generating narrative via Gemini API ...")
    data["narrative"] = generate_narrative(data)

    return data
