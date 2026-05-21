"""
LAE Market Services – Daily Note Data Fetcher
Pre-market sentiment dashboard: VIX, Fear & Greed, Expected Move, Macro Events, Narrative.
"""

import os
import math
import json
import requests
from datetime import datetime, date, timedelta
from google import genai


FINNHUB_BASE = "https://finnhub.io/api/v1"


# ── Finnhub helper ─────────────────────────────────────────────────────────────

def _finnhub(endpoint: str, params: dict) -> dict:
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    params["token"] = api_key
    resp = requests.get(f"{FINNHUB_BASE}/{endpoint}", params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


# ── VIX ────────────────────────────────────────────────────────────────────────

def _vix_zone(v: float) -> str:
    if v < 15:
        return "Low"
    elif v < 25:
        return "Elevated"
    else:
        return "High"


def get_vix() -> dict:
    try:
        data = _finnhub("quote", {"symbol": "^VIX"})
        current = data.get("c")
        prev = data.get("pc")
        if current and prev:
            delta = current - prev
            sign = "+" if delta >= 0 else ""
            return {
                "value": round(current, 2),
                "prev": round(prev, 2),
                "delta": round(delta, 2),
                "delta_str": f"{sign}{delta:.2f}",
                "zone": _vix_zone(current),
                "up": current >= prev,
            }
    except Exception as e:
        print(f"  Warning [VIX]: {e}")
    return {"value": None, "prev": None, "delta": 0, "delta_str": "n/a", "zone": "n/a", "up": False}


# ── SPX ────────────────────────────────────────────────────────────────────────

def get_spx() -> dict:
    try:
        data = _finnhub("quote", {"symbol": "^GSPC"})
        current = data.get("c")
        prev = data.get("pc")
        if current and prev:
            return {"value": round(current, 2), "prev": round(prev, 2)}
    except Exception as e:
        print(f"  Warning [SPX]: {e}")
    return {"value": None, "prev": None}


# ── Expected Move ─────────────────────────────────────────────────────────────

def calc_expected_move(spx_val, vix_val) -> dict:
    """1-day expected move: SPX × (VIX% / √252)"""
    if not spx_val or not vix_val:
        return {"pts": None, "pct": None, "low": None, "high": None}
    em_pts = spx_val * (vix_val / 100) / math.sqrt(252)
    em_pct = (vix_val / 100) / math.sqrt(252) * 100
    return {
        "pts": round(em_pts),
        "pct": round(em_pct, 2),
        "low": round(spx_val - em_pts),
        "high": round(spx_val + em_pts),
    }


# ── Fear & Greed Index ────────────────────────────────────────────────────────

def _fng_zone(v: float) -> str:
    if v <= 25:
        return "Extreme Fear"
    elif v <= 45:
        return "Fear"
    elif v <= 55:
        return "Neutral"
    elif v <= 75:
        return "Greed"
    else:
        return "Extreme Greed"


def get_fear_greed() -> dict:
    try:
        resp = requests.get(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.raise_for_status()
        fg = resp.json().get("fear_and_greed", {})
        value = fg.get("score")
        prev = fg.get("previous_close")
        if value is not None:
            trend_up = (value > prev) if prev else False
            return {
                "value": round(value),
                "prev": round(prev) if prev else None,
                "label": _fng_zone(value),
                "trend_up": trend_up,
            }
    except Exception as e:
        print(f"  Warning [F&G]: {e}")
    return {"value": None, "prev": None, "label": "n/a", "trend_up": False}


# ── Macro Events (3-star only) ────────────────────────────────────────────────

def _utc_to_et(time_str: str, event_date: date) -> str:
    """Convert UTC datetime string to ET, respecting EDT/EST."""
    try:
        dt_utc = datetime.strptime(time_str[:16], "%Y-%m-%d %H:%M")
        if dt_utc.hour == 0 and dt_utc.minute == 0:
            return "TBA"
        year = event_date.year
        march1 = date(year, 3, 1)
        edt_start = march1 + timedelta(days=(6 - march1.weekday()) % 7) + timedelta(weeks=1)
        nov1 = date(year, 11, 1)
        edt_end = nov1 + timedelta(days=(6 - nov1.weekday()) % 7)
        offset = 4 if edt_start <= event_date < edt_end else 5
        dt_et = dt_utc - timedelta(hours=offset)
        return dt_et.strftime("%H:%M ET")
    except Exception:
        return "TBA"


def get_today_events() -> list:
    """Today's 3-star US macro events from Finnhub (impact=3 or 'high')."""
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        return []
    today = date.today()
    try:
        resp = requests.get(
            f"{FINNHUB_BASE}/calendar/economic",
            params={"from": today.isoformat(), "to": today.isoformat(), "token": api_key},
            timeout=20,
        )
        resp.raise_for_status()
        raw = resp.json().get("economicCalendar", [])
        events = []
        for item in raw:
            if item.get("country") != "US":
                continue
            impact = item.get("impact", 0)
            if isinstance(impact, (int, float)) and int(impact) < 3:
                continue
            if isinstance(impact, str) and impact.lower() not in ("high", "3"):
                continue
            name = item.get("event", "").strip()
            if not name:
                continue
            time_str = item.get("time", "")
            time_et = _utc_to_et(time_str, today)
            events.append({"event": name, "time": time_et})
        return events
    except Exception as e:
        print(f"  Warning [EVENTS]: {e}")
    return []


# ── Narrative via Gemini ──────────────────────────────────────────────────────

def generate_narrative(vix: dict, fng: dict, em: dict, events: list) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"yesterday": "–", "sentiment": "–", "outlook": "–"}
    try:
        client = genai.Client(api_key=api_key)

        vix_str = (f"{vix['value']} ({vix['zone']}), prev close: {vix['prev']}, delta: {vix['delta_str']}"
                   if vix["value"] else "n/a")
        fng_str = (f"{fng['value']} ({fng['label']}), prev: {fng['prev']}, trend: {'up' if fng['trend_up'] else 'down'}"
                   if fng["value"] else "n/a")
        em_str = (f"±{em['pts']} pts (±{em['pct']}%), range: {em['low']:,}–{em['high']:,}"
                  if em["pts"] else "n/a")
        events_str = "; ".join(f"{e['time']} {e['event']}" for e in events) if events else "No high-impact events today"

        prompt = f"""You are a professional market analyst for LAE Market Services.
Analyze market sentiment for a pre-market daily briefing.

Indicators (previous close):
- VIX: {vix_str}
- Fear & Greed Index: {fng_str}
- Expected Move SPX today: {em_str}
- Today's high-impact events (3-star): {events_str}

Write exactly three short sections in English (2–3 sentences each):
1. "yesterday" – What do the indicators reveal about yesterday's session? What was the market tone?
2. "sentiment" – What do VIX, Fear & Greed, and the Expected Move signal together? Is today's implied range large or small?
3. "outlook" – What should traders watch today? If high-impact events exist, reference them specifically.

Be direct, professional, actionable. No fluff.
Reply ONLY in this JSON (no markdown, no code blocks):
{{"yesterday": "...", "sentiment": "...", "outlook": "..."}}"""

        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)
        return {
            "yesterday": parsed.get("yesterday", "–"),
            "sentiment": parsed.get("sentiment", "–"),
            "outlook":   parsed.get("outlook", "–"),
        }
    except Exception as e:
        print(f"  Warning [GEMINI]: {e}")
        return {"yesterday": "–", "sentiment": "–", "outlook": f"Narrative unavailable: {e}"}


# ── Main ──────────────────────────────────────────────────────────────────────

def fetch_all() -> dict:
    now = datetime.now()
    weekdays = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday",6:"Sunday"}
    months   = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
                7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"}
    datum_str = f"{weekdays[now.weekday()]}, {months[now.month]} {now.day}, {now.year}"

    print("  [1/4] Fetching VIX from Finnhub ...")
    vix = get_vix()

    print("  [2/4] Fetching SPX from Finnhub ...")
    spx = get_spx()
    em = calc_expected_move(spx.get("value"), vix.get("value"))

    print("  [3/4] Fetching Fear & Greed Index ...")
    fng = get_fear_greed()

    print("  [4/5] Fetching today's macro events ...")
    events = get_today_events()

    print("  [5/5] Generating narrative via Gemini ...")
    narrative = generate_narrative(vix, fng, em, events)

    return {
        "datum":    datum_str,
        "date_iso": now.strftime("%Y-%m-%d"),
        "vix":      vix,
        "spx":      spx,
        "em":       em,
        "fng":      fng,
        "events":   events,
        "narrative": narrative,
    }
