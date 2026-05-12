#!/usr/bin/env python3
"""LAE Macro Analysis – Datenfunktionen
Gemeinsame Daten, Signale und HTML-Bausteine für generate.py.
"""

import os, json
from datetime import datetime, timedelta
from pathlib import Path

# .env laden (falls vorhanden)
_env_file = Path(__file__).parents[2] / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

try:
    import requests
    import pandas as pd
    import yfinance as yf
except ImportError as e:
    print(f"Fehler: {e}\nBitte ausfuehren: pip install yfinance pandas requests")
    import sys; sys.exit(1)

# ── Paths & Dates ─────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parents[2]
OUTPUT_DIR = ROOT / "outputs" / "macro-analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY    = datetime.today()
DATE_STR = TODAY.strftime("%Y-%m-%d")
START_2Y = (TODAY - timedelta(days=730)).strftime("%Y-%m-%d")

# ── Brand Colors (für Signale & HTML-Bausteine) ───────────────────────────────
GREEN = "#39ff14"
WHITE = "#f0f4f8"
GRAY  = "#7a8899"
RED   = "#ff4d4d"
AMBER = "#ffc93c"

# ── Economic Calendar ─────────────────────────────────────────────────────────
ECON_CALENDAR = [
    {"label": "CPI / Core CPI",      "icon": "📊", "dates": [
        "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12",
        "2026-09-11", "2026-10-14", "2026-11-10", "2026-12-10",
    ]},
    {"label": "Non-Farm Payrolls",   "icon": "👷", "dates": [
        "2026-05-08", "2026-06-05", "2026-07-02", "2026-08-07",
        "2026-09-04", "2026-10-02", "2026-11-06", "2026-12-04",
    ]},
    {"label": "Fed Decision (FOMC)", "icon": "🏦", "dates": [
        "2026-06-17", "2026-07-29", "2026-09-16",
        "2026-10-28", "2026-12-09",
    ]},
    {"label": "GDP",                 "icon": "📈", "dates": [
        "2026-04-30", "2026-07-30", "2026-10-29",
    ]},
]

# ── Data Fetching ─────────────────────────────────────────────────────────────
def yahoo(ticker: str, period: str = "2y") -> pd.Series:
    try:
        df = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=True)
        s = df["Close"].rename(ticker)
        s.index = s.index.tz_localize(None)
        return s.dropna()
    except Exception as e:
        print(f"  [Yahoo] {ticker}: {e}")
        return pd.Series(name=ticker, dtype=float)

def _parse_bls_rows(rows: list, name: str) -> pd.Series:
    data = {}
    for row in rows:
        if not row["period"].startswith("M"):
            continue
        month = int(row["period"][1:])
        if month < 1 or month > 12:
            continue
        try:
            val = float(row["value"])
        except (ValueError, TypeError):
            continue
        data[pd.Timestamp(year=int(row["year"]), month=month, day=1)] = val
    return pd.Series(data, name=name).sort_index().dropna()

def bls_batch(series_ids: list[str]) -> dict[str, pd.Series]:
    """BLS Public API v1 – Batch-Request mit lokalem Tages-Cache."""
    cache_file = OUTPUT_DIR / f"_bls_cache_{DATE_STR}.json"
    empty = {sid: pd.Series(name=sid, dtype=float) for sid in series_ids}

    if cache_file.exists():
        print("  [BLS]   Verwende Cache vom heutigen Tag.")
        try:
            raw = json.loads(cache_file.read_text(encoding="utf-8"))
            return {sid: _parse_bls_rows(raw[sid], sid) for sid in series_ids if sid in raw}
        except Exception:
            pass

    try:
        r = requests.post(
            "https://api.bls.gov/publicAPI/v1/timeseries/data/",
            json={"seriesid": series_ids},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        body = r.json()
        if body.get("status") != "REQUEST_SUCCEEDED":
            print(f"  [BLS]   Fehler: {body.get('message', body.get('status'))}")
            return empty
        raw = {s["seriesID"]: s["data"] for s in body["Results"]["series"]}
        cache_file.write_text(json.dumps(raw), encoding="utf-8")
        result = {}
        for s in body["Results"]["series"]:
            result[s["seriesID"]] = _parse_bls_rows(s["data"], s["seriesID"])
        for sid in series_ids:
            if sid not in result:
                result[sid] = pd.Series(name=sid, dtype=float)
        return result
    except Exception as e:
        print(f"  [BLS]   Batch-Fehler: {e}")
        return empty

def fred(series: str, api_key: str, start: str = START_2Y) -> pd.Series:
    if not api_key:
        return pd.Series(name=series, dtype=float)
    try:
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params=dict(series_id=series, api_key=api_key,
                        observation_start=start, file_type="json"),
            timeout=20
        )
        r.raise_for_status()
        obs = r.json().get("observations", [])
        data = {o["date"]: float(o["value"]) for o in obs if o["value"] != "."}
        s = pd.Series(data, name=series)
        s.index = pd.to_datetime(s.index)
        return s.dropna()
    except Exception as e:
        print(f"  [FRED]  {series}: {e}")
        return pd.Series(name=series, dtype=float)

_GDP_FALLBACK = {
    "2026-01-01": 2.0, "2025-10-01": 2.4, "2025-07-01": 2.8,
    "2025-04-01": 2.0, "2025-01-01": 2.4, "2024-10-01": 2.4,
    "2024-07-01": 2.8, "2024-04-01": 3.0, "2024-01-01": 1.4,
    "2023-10-01": 3.3, "2023-07-01": 4.9, "2023-04-01": 2.1,
    "2023-01-01": 2.2, "2022-10-01": 2.6, "2022-07-01": -0.6,
    "2022-04-01": -2.0, "2022-01-01": -1.6,
}

def fetch_gdp(api_key: str = "") -> pd.Series:
    """Real GDP QoQ annualisiert (%). FRED falls Key vorhanden, sonst Fallback."""
    if api_key:
        s = fred("A191RL1Q225SBEA", api_key, "2022-01-01")
        if not s.empty:
            return s
    return pd.Series(
        {pd.Timestamp(k): v for k, v in _GDP_FALLBACK.items()},
        name="GDP_growth"
    ).sort_index()

# ── Scoring ───────────────────────────────────────────────────────────────────
def sig(label: str, value: float, bull_fn, bear_fn) -> dict:
    if bull_fn(value):
        return {"label": label, "value": value, "signal": "bullish", "color": GREEN, "icon": "UP"}
    elif bear_fn(value):
        return {"label": label, "value": value, "signal": "bearish", "color": RED,   "icon": "DOWN"}
    return         {"label": label, "value": value, "signal": "neutral", "color": AMBER, "icon": "NEU"}

def macro_score(signals: list) -> int:
    if not signals:
        return 50
    return round(sum(100 if s["signal"] == "bullish" else (50 if s["signal"] == "neutral" else 0)
                     for s in signals) / len(signals))

def last_val(s: pd.Series) -> float | None:
    if s.empty: return None
    return float(s.dropna().iloc[-1])

# ── Economic Calendar HTML ────────────────────────────────────────────────────
def build_calendar_html() -> str:
    today = TODAY.date()
    cards = []
    for event in ECON_CALENDAR:
        future = [d for d in event["dates"]
                  if datetime.strptime(d, "%Y-%m-%d").date() >= today]
        if not future:
            continue
        next_date = datetime.strptime(future[0], "%Y-%m-%d").date()
        days = (next_date - today).days
        badge = "" if days <= 7 else ""
        cls   = "cal-soon" if days <= 7 else "cal-later"
        date_fmt   = next_date.strftime("%d.%m.%Y")
        badge_html = f'<div class="cal-badge">{badge}</div>' if badge else ""
        cards.append(
            f'<div class="cal-card {cls}">'
            f'<div class="cal-icon">{event["icon"]}</div>'
            f'<div class="cal-body">'
            f'<div class="cal-name">{event["label"]}</div>'
            f'<div class="cal-date">{date_fmt}</div>'
            f'</div>'
            f'{badge_html}'
            f'</div>'
        )
    return "\n".join(cards)

# ── AI Interpretation ─────────────────────────────────────────────────────────
def ai_interpretation(signals: list, score: int) -> str:
    """Generiert den Macro Assessment Text per Gemini API. Fallback auf Template."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return _generate_interpretation(signals, score)

    try:
        from google import genai

        signal_lines = "\n".join(
            f"- {s['label']}: {s['value']:.2f} → {s['signal'].upper()}"
            for s in signals if s.get("value") is not None
        )
        score_label = "BULLISH" if score >= 60 else ("NEUTRAL" if score >= 40 else "BEARISH")

        prompt = f"""You are a professional macro analyst writing a concise assessment for a financial dashboard.

Current US Macro indicators (today):
{signal_lines}

Overall Macro Score: {score}/100 ({score_label})

Write a Macro Assessment in English (4–6 short paragraphs). Requirements:
- Be specific and concrete – reference the actual indicator values
- Identify the current macro regime (e.g. Goldilocks, Disinflation, Overheating, Stagflation, Recessionary)
- Explain key relationships between indicators (e.g. how inflation interacts with GDP and Fed policy)
- Mention market implications for risk assets where relevant
- Use <strong> tags to highlight key terms or regimes (not numbers)
- Do NOT use markdown (no #, *, **, bullet points) – only plain text and <strong> tags
- Each paragraph should be wrapped in <p>...</p>
- Keep total length to roughly 150–200 words"""

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        text = response.text.strip()
        if "<p>" not in text:
            text = "".join(f"<p>{p.strip()}</p>" for p in text.split("\n\n") if p.strip())
        return text

    except Exception as e:
        print(f"  [AI]    Fallback auf Template ({e})")
        return _generate_interpretation(signals, score)


def _generate_interpretation(signals: list, score: int) -> str:
    """Template-Fallback für die Macro Assessment Zusammenfassung."""
    by_key = {s["label"]: s for s in signals}

    cpi_sig   = by_key.get("CPI YoY")
    core_sig  = by_key.get("Core CPI YoY")
    gdp_sig   = by_key.get("Real GDP QoQ")
    yc_sig    = by_key.get("Yield Curve 10Y-3M")
    tnx_sig   = by_key.get("10Y Yield")
    unemp_sig = by_key.get("Unemployment Rate")
    nfp_sig   = by_key.get("NFP Monthly Change")
    vix_sig   = by_key.get("VIX")
    dxy_sig   = by_key.get("DXY")

    cpi_v   = cpi_sig["value"]   if cpi_sig   else None
    core_v  = core_sig["value"]  if core_sig  else None
    gdp_v   = gdp_sig["value"]   if gdp_sig   else None
    spread  = yc_sig["value"]    if yc_sig    else None
    tnx_v   = tnx_sig["value"]   if tnx_sig   else None
    unemp_v = unemp_sig["value"] if unemp_sig else None
    nfp_v   = nfp_sig["value"]   if nfp_sig   else None
    vix_v   = vix_sig["value"]   if vix_sig   else None
    dxy_v   = dxy_sig["value"]   if dxy_sig   else None

    parts = []

    if score >= 65:
        parts.append("The US macro picture is currently <strong>constructive</strong>. The majority of key indicators are sending positive signals – an environment that broadly supports risk assets.")
    elif score >= 45:
        parts.append("The US macro picture is <strong>mixed</strong>. Positive and negative signals are roughly balanced – elevated selectivity is warranted.")
    else:
        parts.append("The US macro picture is currently sending <strong>predominantly cautious signals</strong>. A majority of indicators are under pressure – defensive positioning appears prudent.")

    if cpi_v is not None and gdp_v is not None:
        inflation_hot  = cpi_v > 3.5
        inflation_warm = 2.5 < cpi_v <= 3.5
        inflation_cool = cpi_v <= 2.5
        growth_strong  = gdp_v >= 2.5
        growth_ok      = 0 <= gdp_v < 2.5
        growth_neg     = gdp_v < 0

        if   inflation_cool and growth_strong:
            regime = (f"The combination of declining inflation (CPI {cpi_v:.1f}% YoY) and solid growth (Real GDP {gdp_v:+.1f}% QoQ ann.) represents a <strong>Goldilocks scenario</strong> – the ideal environment for equities and risk assets.")
        elif inflation_warm and growth_strong:
            regime = (f"Growth (Real GDP {gdp_v:+.1f}%) and inflation (CPI {cpi_v:.1f}%) are both elevated – an <strong>overheating signal</strong>. The Fed is under pressure to remain restrictive.")
        elif inflation_hot  and growth_strong:
            regime = (f"Strong growth (Real GDP {gdp_v:+.1f}%) alongside persistently high inflation (CPI {cpi_v:.1f}%) signals an <strong>overheated economy</strong>. The Fed has little room to cut rates.")
        elif inflation_hot  and growth_neg:
            regime = (f"The most dangerous combination: High inflation (CPI {cpi_v:.1f}%) meets contracting growth (Real GDP {gdp_v:+.1f}%) – classic <strong>stagflation risk</strong>.")
        elif inflation_cool and growth_neg:
            regime = (f"Deflationary tendencies: Inflation (CPI {cpi_v:.1f}%) is cooling, growth is negative (Real GDP {gdp_v:+.1f}%) – a <strong>recessionary environment</strong>.")
        elif inflation_warm and growth_ok:
            regime = (f"Moderate growth (Real GDP {gdp_v:+.1f}%) with still-elevated inflation (CPI {cpi_v:.1f}%) – the <strong>disinflation phase</strong> is underway but not yet complete.")
        else:
            regime = (f"Growth (Real GDP {gdp_v:+.1f}%) and inflation (CPI {cpi_v:.1f}%) are sending mixed signals – the macroeconomic regime remains unclear.")
        parts.append(regime)

        if core_v is not None and abs(core_v - cpi_v) > 0.4:
            if core_v > cpi_v:
                parts.append(f"Notable: Core CPI ({core_v:.1f}%) is above Headline CPI ({cpi_v:.1f}%) – price pressures are <strong>more broadly anchored</strong> than energy prices alone explain.")
            else:
                parts.append(f"Core CPI ({core_v:.1f}%) is below Headline CPI ({cpi_v:.1f}%) – energy or food prices are currently driving overall inflation. The Fed views this as a <strong>temporary effect</strong>.")
    elif cpi_v is not None:
        if cpi_v <= 2.5:
            parts.append(f"Inflation (CPI {cpi_v:.1f}%) is near the Fed's target – there is monetary policy room for easing.")
        elif cpi_v <= 3.5:
            parts.append(f"Inflation (CPI {cpi_v:.1f}%) remains above the Fed's 2% target – a restrictive stance remains likely.")
        else:
            parts.append(f"Inflation (CPI {cpi_v:.1f}%) is clearly elevated – rate cuts are unrealistic in this environment.")

    if unemp_v is not None and nfp_v is not None:
        if unemp_v > 5.0 or nfp_v < 0:
            labor_txt = f"The labor market is weakening noticeably – Unemployment {unemp_v:.1f}%, NFP {nfp_v:+,.0f}k."
            if gdp_v is not None and gdp_v < 0:
                labor_txt += " Combined with negative GDP growth, the picture of an <strong>emerging recession</strong> is consolidating."
        elif unemp_v > 4.2 or nfp_v < 100:
            labor_txt = f"The labor market is gradually cooling: Unemployment {unemp_v:.1f}%, NFP {nfp_v:+,.0f}k."
            if cpi_v is not None and cpi_v > 3.0:
                labor_txt += " From the Fed's perspective, this cooling is <strong>welcome</strong>."
        else:
            labor_txt = f"The labor market remains a pillar of strength: Unemployment at {unemp_v:.1f}%, NFP last at +{nfp_v:,.0f}k."
            if gdp_v is not None and gdp_v >= 2.0:
                labor_txt += " Together with solid GDP growth, this confirms the <strong>strength of the business cycle</strong>."
        parts.append(labor_txt)

    if spread is not None and tnx_v is not None:
        if spread > 0.1:
            zins_txt = f"The yield curve (10Y–3M: {spread:+.2f}%) has normalized – a positive sign for the economic outlook."
            if cpi_v is not None and cpi_v <= 3.0:
                zins_txt += f" Combined with moderate inflation, this opens a potential <strong>rate-cut path</strong> for the Fed."
        elif spread > -0.1:
            zins_txt = f"The yield curve (10Y–3M: {spread:+.2f}%) is nearly flat – no clear growth signal. The 10Y yield at {tnx_v:.2f}% constrains equity valuations."
        else:
            zins_txt = f"The yield curve remains inverted at {spread:+.2f}% (10Y–3M) – historically a reliable leading indicator of economic slowdown."
            if gdp_v is not None and gdp_v < 0:
                zins_txt += " Negative GDP growth confirms this signal and materially increases <strong>recession probability</strong>."
        parts.append(zins_txt)

    if vix_v is not None or dxy_v is not None:
        sent_parts = []
        if vix_v is not None:
            if vix_v <= 15:
                sent_parts.append(f"VIX at {vix_v:.1f} signals <strong>low risk aversion</strong> – the market is currently pricing in very little uncertainty.")
            elif vix_v <= 25:
                sent_parts.append(f"VIX at {vix_v:.1f} shows elevated nervousness – hedging demand in the market is rising.")
            else:
                sent_parts.append(f"VIX at {vix_v:.1f} signals <strong>pronounced risk aversion</strong> – capital is seeking safe havens.")
        if dxy_v is not None:
            if dxy_v < 100:
                dxy_txt = f"A weak dollar (DXY {dxy_v:.1f}) benefits international corporate earnings, commodities and emerging markets."
            elif dxy_v <= 107:
                dxy_txt = f"The dollar (DXY {dxy_v:.1f}) is in neutral territory – no dominant currency signal."
            else:
                dxy_txt = f"A strong dollar (DXY {dxy_v:.1f}) weighs on commodity prices and reduces the competitiveness of US exporters."
            if vix_v is not None and vix_v > 25 and dxy_v > 105:
                dxy_txt += " The combination of high VIX and a strong dollar is a classic <strong>risk-off signal</strong>."
            elif vix_v is not None and vix_v <= 15 and dxy_v < 100:
                dxy_txt += " Low VIX and a weak dollar point to a pronounced <strong>risk-on environment</strong>."
            sent_parts.append(dxy_txt)
        parts.append(" ".join(sent_parts))

    return " ".join(f"<p>{p}</p>" for p in parts)

# ── HTML-Bausteine ────────────────────────────────────────────────────────────
def kpi_card(label: str, value: str, sub: str = "", color: str = WHITE) -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (f'<div class="kpi-card">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value" style="color:{color}">{value}</div>'
            f'{sub_html}</div>')

def signal_card(s: dict) -> str:
    icon_map = {"UP": "&#9650;", "DOWN": "&#9660;", "NEU": "&#9679;"}
    lbl = s["label"]
    v   = s["value"]
    if lbl in ("CPI YoY", "Core CPI YoY", "Real GDP QoQ", "Unemployment Rate"):
        fmt = f"{v:.1f}%"
    elif lbl in ("10Y Yield", "Yield Curve 10Y-3M"):
        fmt = f"{v:.2f}%"
    elif lbl == "NFP Monthly Change":
        fmt = f"{v:,.0f}k"
    elif lbl in ("VIX", "DXY"):
        fmt = f"{v:.1f}"
    else:
        fmt = f"{v:.2f}"
    return (f'<div class="sig-card sig-{s["signal"]}">'
            f'<div class="sig-label">{lbl}</div>'
            f'<div class="sig-val" style="color:{s["color"]}">{icon_map[s["icon"]]} {fmt}</div>'
            f'<div class="sig-badge badge-{s["signal"]}">{s["signal"].upper()}</div>'
            f'</div>')
