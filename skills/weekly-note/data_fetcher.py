"""
LAE Market Services – Weekly Note Data Fetcher
Fetches all market data automatically and returns it in generate.py format.
"""

import os
import math
import time
import requests
from datetime import datetime, timedelta

import yfinance as yf
from google import genai


# ── Configuration ─────────────────────────────────────────────────────────────

INDEX_TICKERS = {
    "sp500":   ("^GSPC",   "S&P 500"),
    "nasdaq":  ("^IXIC",   "Nasdaq"),
    "dow":     ("^DJI",    "Dow"),
    "russell": ("^RUT",    "Russell"),
}

SECTOR_ETFS = {
    "XLK":  "Technology",
    "XLE":  "Energy",
    "XLF":  "Financials",
    "XLY":  "Cons. Discretionary",
    "XLP":  "Cons. Staples",
    "XLV":  "Health Care",
    "XLU":  "Utilities",
    "XLB":  "Materials",
    "XLI":  "Industrials",
    "XLRE": "Real Estate",
}

FUTURES = {
    "es": ("ES=F",  "ES (S&P Futures)"),
    "nq": ("NQ=F",  "NQ (Nasdaq Futures)"),
}

TOP_EARNINGS_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "BRK-B",
    "JPM", "UNH", "V", "XOM", "JNJ", "PG", "MA", "HD", "COST", "LLY",
    "AVGO", "ABBV", "MRK", "KO", "PEP", "ADBE", "CRM", "AMD", "ORCL",
    "CSCO", "IBM", "INTC", "NOW", "QCOM", "TXN", "AMAT", "MU", "LRCX",
    "GS", "MS", "BAC", "WFC", "C",
]

_DAY_EN = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

# Browser-like session to reduce Yahoo Finance blocking on CI/CD environments
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
})


# ── Helper functions ───────────────────────────────────────────────────────────

def _pct(new_val: float, old_val: float) -> str:
    if old_val == 0:
        return "n/a"
    pct = (new_val - old_val) / old_val * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def _woche_start_ende() -> tuple[datetime, datetime]:
    """Returns start and end of the last trading week (Mon–Fri)."""
    today = datetime.now()
    weekday = today.weekday()  # 0=Mon, 6=Sun
    days_since_friday = (weekday - 4) % 7
    last_friday = today - timedelta(days=days_since_friday)
    last_monday = last_friday - timedelta(days=4)
    return last_monday, last_friday


def _next_week_range() -> tuple[datetime, datetime]:
    """Next trading week Mon–Fri."""
    today = datetime.now()
    weekday = today.weekday()
    days_until_monday = (7 - weekday) % 7 or 7
    next_monday = today + timedelta(days=days_until_monday)
    next_friday = next_monday + timedelta(days=4)
    return next_monday, next_friday


def _format_level(val: float, ticker: str) -> str:
    if val >= 1000:
        return f"{val:,.0f}"
    return f"{val:,.2f}"


def _download_with_retry(ticker: str, start: str, end: str, retries: int = 3) -> object:
    """Downloads yfinance data with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                progress=False,
                auto_adjust=True,
                session=_SESSION,
            )
            if not df.empty:
                return df
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(2 ** attempt)  # 1s, 2s, 4s
    return None


# ── Index performance ──────────────────────────────────────────────────────────

def get_index_performance() -> dict:
    """Weekly performance of the four main indices."""
    result = {}
    _, last_fri = _woche_start_ende()

    start = (last_fri - timedelta(days=10)).strftime("%Y-%m-%d")
    end   = (last_fri + timedelta(days=1)).strftime("%Y-%m-%d")

    for key, (ticker, name) in INDEX_TICKERS.items():
        df = _download_with_retry(ticker, start, end)
        if df is None or len(df) < 2:
            result[key] = {"name": name, "woche": "n/a", "positiv": True}
            continue
        try:
            close_now  = float(df["Close"].iloc[-1])
            close_prev = float(df["Close"].iloc[-6]) if len(df) >= 6 else float(df["Close"].iloc[0])
            perf = _pct(close_now, close_prev)
            result[key] = {
                "name":    name,
                "woche":   perf,
                "positiv": close_now >= close_prev,
            }
        except Exception:
            result[key] = {"name": name, "woche": "n/a", "positiv": True}

    return result


# ── Sector performance ────────────────────────────────────────────────────────

def get_sector_performance() -> tuple[list, list]:
    """Returns Top-2 and Flop-2 sectors of the last week."""
    _, last_fri = _woche_start_ende()
    start = (last_fri - timedelta(days=10)).strftime("%Y-%m-%d")
    end   = (last_fri + timedelta(days=1)).strftime("%Y-%m-%d")

    performances = []
    for etf, name in SECTOR_ETFS.items():
        df = _download_with_retry(etf, start, end)
        if df is None or len(df) < 2:
            continue
        try:
            close_now  = float(df["Close"].iloc[-1])
            close_prev = float(df["Close"].iloc[-6]) if len(df) >= 6 else float(df["Close"].iloc[0])
            pct = (close_now - close_prev) / close_prev * 100
            sign = "+" if pct >= 0 else ""
            performances.append({
                "name":    name,
                "kuerzel": etf,
                "perf":    f"{sign}{pct:.1f}%",
                "pct":     pct,
            })
        except Exception:
            continue

    performances.sort(key=lambda x: x["pct"], reverse=True)
    top  = [{"name": s["name"], "kuerzel": s["kuerzel"], "perf": s["perf"]} for s in performances[:2]]
    flop = [{"name": s["name"], "kuerzel": s["kuerzel"], "perf": s["perf"]} for s in performances[-2:]]
    return top, flop


# ── Technical levels ──────────────────────────────────────────────────────────

def get_technical_levels() -> dict:
    """Calculates bias, support and resistance for ES and NQ from price history."""
    result = {}
    end_dt   = datetime.now()
    start_dt = end_dt - timedelta(days=60)

    for key, (ticker, label) in FUTURES.items():
        df = _download_with_retry(
            ticker,
            start_dt.strftime("%Y-%m-%d"),
            (end_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
        )
        if df is None or len(df) < 10:
            result[key] = {"bias": "n/a", "support": "n/a", "resistance": "n/a"}
            continue
        try:
            close = df["Close"]
            low   = df["Low"]
            high  = df["High"]

            current = float(close.iloc[-1])
            ma20    = float(close.rolling(20).mean().iloc[-1])

            support    = float(low.iloc[-14:].min())
            resistance = float(high.iloc[-14:].max())

            bias = "Uptrend" if current > ma20 else "Downtrend"

            result[key] = {
                "bias":       bias,
                "support":    _format_level(support, ticker),
                "resistance": _format_level(resistance, ticker),
            }
        except Exception:
            result[key] = {"bias": "n/a", "support": "n/a", "resistance": "n/a"}

    return result


# ── Earnings calendar ─────────────────────────────────────────────────────────

def get_earnings_calendar() -> list:
    """Finds earnings dates for next week from a top-ticker list."""
    next_mon, next_fri = _next_week_range()
    earnings_next_week = []

    for symbol in TOP_EARNINGS_TICKERS:
        try:
            t = yf.Ticker(symbol, session=_SESSION)
            cal = t.calendar
            if cal is None:
                continue

            dates = cal.get("Earnings Date", [])
            if not dates:
                continue

            date_list = list(dates) if hasattr(dates, "__iter__") and not isinstance(dates, str) else [dates]

            for ed in date_list:
                if ed is None:
                    continue
                if hasattr(ed, "date"):
                    ed_date = ed.date()
                else:
                    try:
                        ed_date = datetime.strptime(str(ed)[:10], "%Y-%m-%d").date()
                    except Exception:
                        continue

                if next_mon.date() <= ed_date <= next_fri.date():
                    eps_erw = cal.get("Earnings Average", "n/a")
                    if isinstance(eps_erw, (int, float)) and not math.isnan(float(eps_erw)):
                        eps_str = f"{float(eps_erw):.2f}"
                    else:
                        eps_str = "n/a"

                    earnings_next_week.append({
                        "ticker":  symbol,
                        "name":    t.info.get("shortName", symbol) if hasattr(t, "info") else symbol,
                        "tag":     _DAY_EN.get(ed_date.weekday(), "?"),
                        "eps_erw": eps_str,
                        "datum":   ed_date,
                    })
                    break
        except Exception:
            continue

    earnings_next_week.sort(key=lambda x: x["datum"])
    for e in earnings_next_week:
        e.pop("datum", None)

    if not earnings_next_week:
        earnings_next_week = [{"ticker": "n/a", "name": "No data available", "tag": "-", "eps_erw": "-"}]

    return earnings_next_week[:5]


# ── Macro calendar ────────────────────────────────────────────────────────────

def get_macro_calendar() -> list:
    """
    Generates a heuristic macro calendar for next week based on known
    recurring US economic data releases.
    """
    next_mon, next_fri = _next_week_range()
    events = []

    day = next_mon
    while day <= next_fri:
        wd  = day.weekday()
        dom = day.day

        if wd == 3:
            events.append({
                "tag":     "Thu",
                "event":   "Initial Jobless Claims",
                "uhrzeit": "08:30",
            })

        if wd == 4 and dom <= 7:
            events.append({
                "tag":     "Fri",
                "event":   "Nonfarm Payrolls (NFP) – Employment & Unemployment Rate",
                "uhrzeit": "08:30",
            })

        if wd == 1 and 8 <= dom <= 14:
            events.append({
                "tag":     "Tue",
                "event":   "Consumer Price Index (CPI)",
                "uhrzeit": "08:30",
            })

        if wd == 2 and 8 <= dom <= 15:
            events.append({
                "tag":     "Wed",
                "event":   "Producer Price Index (PPI) / Retail Sales",
                "uhrzeit": "08:30",
            })

        if wd == 3 and 15 <= dom <= 21:
            events.append({
                "tag":     "Thu",
                "event":   "Philly Fed Manufacturing Index",
                "uhrzeit": "08:30",
            })

        if wd == 4 and 15 <= dom <= 21:
            events.append({
                "tag":     "Fri",
                "event":   "Flash PMI (Manufacturing & Services)",
                "uhrzeit": "09:45",
            })

        day += timedelta(days=1)

    if not events:
        events.append({
            "tag":     "-",
            "event":   "No major data releases this week",
            "uhrzeit": "-",
        })

    return events[:5]


# ── Narrative via Gemini API ──────────────────────────────────────────────────

def generate_narrative(data: dict) -> dict:
    """Generates headline and market commentary via Google Gemini."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "headline": "Weekly Review – set GEMINI_API_KEY to enable",
            "body":     "No API key found. Set the GEMINI_API_KEY environment variable to enable automatic narrative generation.",
        }

    try:
        client = genai.Client(api_key=api_key)

        idx_lines   = "\n".join(f"  {v['name']}: {v['woche']}" for v in data["indizes"].values())
        top_lines   = ", ".join(f"{s['name']} ({s['perf']})" for s in data["sektor_top"])
        flop_lines  = ", ".join(f"{s['name']} ({s['perf']})" for s in data["sektor_flop"])
        earn_lines  = ", ".join(f"{e['ticker']} ({e['tag']})" for e in data["earnings"][:3])
        macro_lines = ", ".join(f"{m['event']} ({m['tag']})" for m in data["makro"][:3])

        prompt = f"""You are a professional market analyst for LAE Market Services.
Write a concise English weekly market review for CW {data['kw']}.

Last week's market data:
Indices:
{idx_lines}

Top sectors: {top_lines}
Weakest sectors: {flop_lines}

Next week:
Earnings: {earn_lines if earn_lines else 'no major releases'}
Macro: {macro_lines if macro_lines else 'no major data'}

Create:
1. A punchy headline (max 12 words, no quotes)
2. A market commentary (4–5 sentences, factual, professional, in English, tone: direct and clear)

Format – reply ONLY in this JSON format without markdown blocks:
{{"headline": "...", "body": "..."}}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )

        import json
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)
        return {
            "headline": parsed.get("headline", "Weekly Review"),
            "body":     parsed.get("body", ""),
        }

    except Exception as e:
        return {
            "headline": f"Weekly Review CW {data['kw']}",
            "body":     f"Narrative could not be generated: {e}",
        }


# ── Main function ─────────────────────────────────────────────────────────────

def fetch_all() -> dict:
    """Aggregates all data and returns the complete data dict."""
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
