#!/usr/bin/env python3
"""
LAE Market Services - Macro Analysis Generator
Senior Data Visualisation · Plotly · LAE Brand Design

Kein API-Key notwendig fuer Basisdaten.
Optional: FRED API Key fuer erweiterte Daten (Jobless Claims, Core PCE, Fed Funds Rate)

Aufruf:
  python generate.py
  python generate.py --api-key DEIN_FRED_KEY

Dependencies: pip install plotly yfinance pandas requests
"""

import os, sys, json, argparse
from datetime import datetime, timedelta
from pathlib import Path

# .env laden (falls vorhanden)
_env_file = Path(__file__).parent.parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

try:
    import requests
    import pandas as pd
    import yfinance as yf
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.io as pio
except ImportError as e:
    print(f"Fehler: {e}\nBitte ausfuehren: pip install plotly yfinance pandas requests")
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parents[2]
OUTPUT_DIR = ROOT / "outputs" / "macro-analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY    = datetime.today()
DATE_STR = TODAY.strftime("%Y-%m-%d")
KW       = TODAY.strftime("CW%W")
START_2Y = (TODAY - timedelta(days=730)).strftime("%Y-%m-%d")
START_3Y = (TODAY - timedelta(days=1095)).strftime("%Y-%m-%d")

# ── LAE Brand ─────────────────────────────────────────────────────────────────
BG    = "#090c11"
BG2   = "#0d111a"
BG3   = "#111720"
GREEN = "#39ff14"
WHITE = "#f0f4f8"
GRAY  = "#7a8899"
RED   = "#ff4d4d"
AMBER = "#ffc93c"
BLUE  = "#4da6ff"
GRID  = "rgba(255,255,255,0.03)"
LINE  = "rgba(255,255,255,0.08)"
MONO  = "JetBrains Mono, Courier New, monospace"
BODY  = "Inter, system-ui, -apple-system, sans-serif"

# ── Economic Calendar ─────────────────────────────────────────────────────────
ECON_CALENDAR = [
    {"label": "CPI / Core CPI",      "icon": "📊", "dates": [
        "2026-05-13", "2026-06-11", "2026-07-14", "2026-08-12",
        "2026-09-11", "2026-10-14", "2026-11-12", "2026-12-11",
    ]},
    {"label": "Non-Farm Payrolls",   "icon": "👷", "dates": [
        "2026-05-08", "2026-06-05", "2026-07-02", "2026-08-07",
        "2026-09-04", "2026-10-02", "2026-11-06", "2026-12-04",
    ]},
    {"label": "Fed Decision (FOMC)",  "icon": "🏦", "dates": [
        "2026-05-06", "2026-06-17", "2026-07-29", "2026-09-16",
        "2026-10-28", "2026-12-09",
    ]},
    {"label": "GDP",                   "icon": "📈", "dates": [
        "2026-04-30", "2026-07-30", "2026-10-29",
    ]},
]

BASE = dict(
    paper_bgcolor=BG2,
    plot_bgcolor=BG2,
    font=dict(family=MONO, color=WHITE, size=11),
    hoverlabel=dict(bgcolor=BG3, bordercolor=LINE, font=dict(family=MONO, size=11, color=WHITE)),
    hovermode="x unified",
    legend=dict(
        bgcolor="rgba(0,0,0,0)", bordercolor=LINE, borderwidth=1,
        font=dict(size=10, color=GRAY), orientation="h",
        yanchor="bottom", y=1.01, xanchor="right", x=1
    ),
)

def ax(**kw):
    return dict(
        gridcolor=GRID, linecolor=LINE, zerolinecolor=LINE,
        tickfont=dict(family=MONO, size=10, color=GRAY),
        showspikes=True, spikecolor=LINE, spikethickness=1, spikesnap="cursor",
        **kw
    )

def t(text):
    return dict(text=f"<b style='color:{WHITE}'>{text}</b>",
                font=dict(family=BODY, size=12), x=0.0, xanchor="left",
                pad=dict(l=6, b=2))

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
    """BLS Public API v1 - ein Batch-Request, mit lokalem Tages-Cache"""
    cache_file = OUTPUT_DIR / f"_bls_cache_{DATE_STR}.json"
    empty = {sid: pd.Series(name=sid, dtype=float) for sid in series_ids}

    # Cache lesen falls vorhanden
    if cache_file.exists():
        print("  [BLS]   Verwende Cache vom heutigen Tag.")
        try:
            raw = json.loads(cache_file.read_text(encoding="utf-8"))
            return {sid: _parse_bls_rows(raw[sid], sid) for sid in series_ids if sid in raw}
        except Exception:
            pass

    # Frisch laden
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
        # Cache schreiben
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

# Realistische US Real-GDP-Wachstumsraten (QoQ annualisiert, %) – Fallback ohne API-Key
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
    s = pd.Series(
        {pd.Timestamp(k): v for k, v in _GDP_FALLBACK.items()},
        name="GDP_growth"
    ).sort_index()
    return s

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
        if days == 0:
            badge, cls = "Today", "cal-today"
        elif days <= 7:
            badge, cls = "", "cal-soon"
        else:
            badge, cls = "", "cal-later"
        date_fmt = next_date.strftime("%d.%m.%Y")
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

# ── AI Interpretation (Gemini API) ────────────────────────────────────────────
def ai_interpretation(signals: list, score: int) -> str:
    """Generiert den Macro Assessment Text per Gemini API. Fallback auf Template."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return generate_interpretation(signals, score)

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
        return generate_interpretation(signals, score)


# ── Interpretation (Template-Fallback) ────────────────────────────────────────
def generate_interpretation(signals: list, score: int) -> str:
    """Analytische Makro-Zusammenfassung mit Zusammenhangs-Erkennung zwischen Indikatoren."""
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

    # ── 1. Gesamtbild ─────────────────────────────────────────────────────────
    if score >= 65:
        intro = "The US macro picture is currently <strong>constructive</strong>. The majority of key indicators are sending positive signals – an environment that broadly supports risk assets."
    elif score >= 45:
        intro = "The US macro picture is <strong>mixed</strong>. Positive and negative signals are roughly balanced – elevated selectivity is warranted."
    else:
        intro = "The US macro picture is currently sending <strong>predominantly cautious signals</strong>. A majority of indicators are under pressure – defensive positioning appears prudent."
    parts.append(intro)

    # ── 2. Wachstum & Inflation: Makroregime bestimmen ────────────────────────
    if cpi_v is not None and gdp_v is not None:
        inflation_hot  = cpi_v > 3.5
        inflation_warm = 2.5 < cpi_v <= 3.5
        inflation_cool = cpi_v <= 2.5
        growth_strong  = gdp_v >= 2.5
        growth_ok      = 0 <= gdp_v < 2.5
        growth_neg     = gdp_v < 0

        if inflation_cool and growth_strong:
            regime = (f"The combination of declining inflation (CPI {cpi_v:.1f}% YoY) "
                      f"and solid growth (Real GDP {gdp_v:+.1f}% QoQ ann.) represents a "
                      f"<strong>Goldilocks scenario</strong> – the ideal environment for equities and risk assets. "
                      f"The Fed has room to act without having to trade off between growth and price stability.")
        elif inflation_warm and growth_strong:
            regime = (f"Growth (Real GDP {gdp_v:+.1f}%) and inflation (CPI {cpi_v:.1f}%) are both elevated – "
                      f"an <strong>overheating signal</strong>. The Fed is under pressure to remain restrictive. "
                      f"Risk assets benefit short-term as long as earnings hold up, "
                      f"but higher rates constrain valuations over the medium term.")
        elif inflation_hot and growth_strong:
            regime = (f"Strong growth (Real GDP {gdp_v:+.1f}%) alongside persistently high inflation (CPI {cpi_v:.1f}%) "
                      f"signals an <strong>overheated economy</strong>. The Fed has little room to cut rates – "
                      f"the market must brace for a prolonged restrictive rate environment.")
        elif inflation_hot and growth_neg:
            regime = (f"The most dangerous combination: High inflation (CPI {cpi_v:.1f}%) meets contracting growth "
                      f"(Real GDP {gdp_v:+.1f}%) – classic <strong>stagflation risk</strong>. "
                      f"The Fed can neither ease nor tighten clearly without worsening the other problem. "
                      f"Commodities and inflation-protected assets gain relevance in this regime.")
        elif inflation_cool and growth_neg:
            regime = (f"Deflationary tendencies: Inflation (CPI {cpi_v:.1f}%) is cooling, growth is negative "
                      f"(Real GDP {gdp_v:+.1f}%) – a <strong>recessionary environment</strong>. "
                      f"The Fed theoretically has room to cut rates, which favors bonds and defensive sectors.")
        elif inflation_warm and growth_ok:
            regime = (f"Moderate growth (Real GDP {gdp_v:+.1f}%) with still-elevated inflation (CPI {cpi_v:.1f}%) – "
                      f"the <strong>disinflation phase</strong> is underway but not yet complete. "
                      f"The Fed is waiting for additional data points before easing monetary policy.")
        else:
            regime = (f"Growth (Real GDP {gdp_v:+.1f}%) and inflation (CPI {cpi_v:.1f}%) are sending mixed signals – "
                      f"the macroeconomic regime remains unclear. Heightened attention to upcoming data releases is warranted.")
        parts.append(regime)

        if core_v is not None and abs(core_v - cpi_v) > 0.4:
            if core_v > cpi_v:
                parts.append(f"Notable: Core CPI ({core_v:.1f}%) is above Headline CPI ({cpi_v:.1f}%) – "
                              f"price pressures are <strong>more broadly anchored</strong> than energy prices alone explain. "
                              f"The Fed treats the core reading as its primary policy guide, which increases monetary pressure.")
            else:
                parts.append(f"Core CPI ({core_v:.1f}%) is below Headline CPI ({cpi_v:.1f}%) – "
                              f"energy or food prices are currently driving overall inflation. "
                              f"The Fed views this as a <strong>temporary effect</strong> as long as core inflation remains moderate.")
    elif cpi_v is not None:
        if cpi_v <= 2.5:
            parts.append(f"Inflation (CPI {cpi_v:.1f}%) is near the Fed's target – "
                         f"there is monetary policy room for easing.")
        elif cpi_v <= 3.5:
            parts.append(f"Inflation (CPI {cpi_v:.1f}%) remains above the Fed's 2% target – "
                         f"a restrictive stance from the central bank remains likely.")
        else:
            parts.append(f"Inflation (CPI {cpi_v:.1f}%) is clearly elevated – "
                         f"rate cuts are unrealistic in this environment.")

    # ── 3. Arbeitsmarkt & Wachstums-Check ─────────────────────────────────────
    if unemp_v is not None and nfp_v is not None:
        labor_strong  = unemp_v <= 4.2 and nfp_v >= 150
        labor_cooling = unemp_v > 4.2 or nfp_v < 100
        labor_weak    = unemp_v > 5.0 or nfp_v < 0

        if labor_weak:
            labor_txt = (f"The labor market is weakening noticeably – Unemployment {unemp_v:.1f}%, "
                         f"NFP {nfp_v:+,.0f}k.")
            if gdp_v is not None and gdp_v < 0:
                labor_txt += (" Combined with negative GDP growth, the picture of an "
                              "<strong>emerging recession</strong> is consolidating.")
            else:
                labor_txt += " Economic concerns are growing – defensive positioning is gaining relevance."
        elif labor_cooling:
            labor_txt = (f"The labor market is gradually cooling: Unemployment {unemp_v:.1f}%, "
                         f"NFP {nfp_v:+,.0f}k.")
            if cpi_v is not None and cpi_v > 3.0:
                labor_txt += (" From the Fed's perspective, this cooling is <strong>welcome</strong>, "
                              "as softening demand helps reduce inflationary pressure.")
            else:
                labor_txt += (" Should this trend accelerate, pressure on the Fed to ease monetary policy will grow.")
        else:
            labor_txt = (f"The labor market remains a pillar of strength: Unemployment at {unemp_v:.1f}%, "
                         f"NFP last at +{nfp_v:,.0f}k.")
            if gdp_v is not None and gdp_v >= 2.0:
                labor_txt += (" Together with solid GDP growth, this confirms the <strong>strength of the business cycle</strong> – "
                              "a consumer pullback is unlikely in the near term.")
            elif gdp_v is not None and gdp_v < 0:
                labor_txt += (" The divergence from negative GDP growth is a <strong>warning signal</strong>: "
                              "Typically, the labor market weakens with a lag – "
                              "job data could come under pressure in the coming quarters.")
            else:
                labor_txt += " Consumer spending and domestic demand remain structurally supported."
        parts.append(labor_txt)

    # ── 4. Zinsen & Yield Curve ────────────────────────────────────────────────
    if spread is not None and tnx_v is not None:
        if spread > 0.1:
            zins_txt = (f"The yield curve (10Y–3M: {spread:+.2f}%) has normalized – "
                        f"a positive sign for the economic outlook.")
            if cpi_v is not None and cpi_v <= 3.0:
                zins_txt += (f" Combined with moderate inflation, this opens a potential "
                             f"<strong>rate-cut path</strong> for the Fed.")
        elif spread > -0.1:
            zins_txt = (f"The yield curve (10Y–3M: {spread:+.2f}%) is nearly flat – "
                        f"no clear growth signal. The 10Y yield at {tnx_v:.2f}% "
                        f"constrains equity valuations.")
            if gdp_v is not None and gdp_v >= 2.0:
                zins_txt += f" However, solid GDP growth significantly reduces the immediate recession risk."
        else:
            zins_txt = (f"The yield curve remains inverted at {spread:+.2f}% (10Y–3M) – "
                        f"historically a reliable leading indicator of economic slowdown.")
            if gdp_v is not None and gdp_v < 0:
                zins_txt += (" Negative GDP growth confirms this signal and materially increases "
                             "<strong>recession probability</strong>.")
            elif gdp_v is not None and gdp_v >= 2.0:
                zins_txt += (f" Current GDP growth ({gdp_v:+.1f}%) still contradicts the signal – "
                             f"the typical lag between inversion and slowdown is 12–18 months.")
        parts.append(zins_txt)

    # ── 5. Sentiment, Dollar & Risikobereitschaft ─────────────────────────────
    if vix_v is not None or dxy_v is not None:
        sent_parts = []
        if vix_v is not None:
            if vix_v <= 15:
                sent_parts.append(f"VIX at {vix_v:.1f} signals <strong>low risk aversion</strong> – "
                                  f"the market is currently pricing in very little uncertainty.")
            elif vix_v <= 25:
                sent_parts.append(f"VIX at {vix_v:.1f} shows elevated nervousness – "
                                  f"hedging demand in the market is rising.")
            else:
                sent_parts.append(f"VIX at {vix_v:.1f} signals <strong>pronounced risk aversion</strong> – "
                                  f"capital is seeking safe havens.")
        if dxy_v is not None:
            if dxy_v < 100:
                dxy_txt = (f"A weak dollar (DXY {dxy_v:.1f}) benefits international corporate earnings, "
                           f"commodities and emerging markets.")
            elif dxy_v <= 107:
                dxy_txt = f"The dollar (DXY {dxy_v:.1f}) is in neutral territory – no dominant currency signal."
            else:
                dxy_txt = (f"A strong dollar (DXY {dxy_v:.1f}) weighs on commodity prices "
                           f"and reduces the competitiveness of US exporters.")
            if vix_v is not None and vix_v > 25 and dxy_v > 105:
                dxy_txt += (" The combination of high VIX and a strong dollar is a classic "
                            "<strong>risk-off signal</strong> – investors are fleeing into the US dollar as a safe haven.")
            elif vix_v is not None and vix_v <= 15 and dxy_v < 100:
                dxy_txt += (" Low VIX and a weak dollar point to a pronounced "
                            "<strong>risk-on environment</strong>.")
            sent_parts.append(dxy_txt)
        parts.append(" ".join(sent_parts))

    return " ".join(f"<p>{p}</p>" for p in parts)

# ── Chart Helpers ─────────────────────────────────────────────────────────────
def last_val(s: pd.Series) -> float | None:
    if s.empty: return None
    return float(s.dropna().iloc[-1])

def current_annotation(fig, s: pd.Series, fmt: str = ".2f", prefix: str = "", suffix: str = ""):
    v = last_val(s)
    if v is None: return
    fig.add_annotation(
        x=1, y=v, xref="paper", yref="y",
        text=f"<b>{prefix}{v:{fmt}}{suffix}</b>",
        showarrow=False, xanchor="left",
        font=dict(family=MONO, size=10, color=WHITE),
        bgcolor=BG3, bordercolor=LINE, borderpad=4,
    )

# ── Charts ────────────────────────────────────────────────────────────────────
def chart_gauge(score: int) -> go.Figure:
    color = GREEN if score >= 60 else (AMBER if score >= 40 else RED)
    label = "BULLISH" if score >= 60 else ("NEUTRAL" if score >= 40 else "BEARISH")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0.05, 0.95], "y": [0.05, 0.95]},
        title={"text": f"MACRO SIGNAL<br><span style='color:{color};font-size:13px;letter-spacing:4px;font-weight:700'>{label}</span>",
               "font": {"family": BODY, "size": 11, "color": GRAY}},
        number={"font": {"family": MONO, "size": 44, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": LINE,
                     "tickfont": {"size": 9, "color": GRAY}, "nticks": 6},
            "bar": {"color": color, "thickness": 0.22},
            "bgcolor": BG3,
            "borderwidth": 1, "bordercolor": LINE,
            "steps": [
                {"range": [0, 35],  "color": "rgba(255,77,77,0.10)"},
                {"range": [35, 65], "color": "rgba(255,201,60,0.07)"},
                {"range": [65, 100],"color": "rgba(57,255,20,0.09)"},
            ],
            "threshold": {"line": {"color": color, "width": 3},
                          "thickness": 0.8, "value": score},
        },
    ))
    fig.update_layout(**BASE, height=290, margin=dict(l=5, r=10, t=24, b=16))
    return fig

def chart_yield_curve(tnx: pd.Series, irx: pd.Series) -> go.Figure:
    # Yield curve: 10Y minus ~3M T-Bill as short-rate proxy
    spread = (tnx - irx.reindex(tnx.index, method="ffill")).dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spread.index, y=spread.clip(lower=0),
        fill="tozeroy", fillcolor="rgba(57,255,20,0.07)",
        line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=spread.index, y=spread.clip(upper=0),
        fill="tozeroy", fillcolor="rgba(255,77,77,0.10)",
        line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=spread.index, y=spread,
        line=dict(color=GREEN, width=2),
        name="10Y - 3M", hovertemplate="%{x|%d.%m.%Y}  %{y:+.2f}%<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=LINE, width=1, dash="dot"))
    fig.update_layout(**BASE, title=t("Yield Curve · 10Y - 3M"), height=320,
        margin=dict(l=50, r=70, t=62, b=40),
        xaxis=ax(showgrid=False, rangeslider=dict(visible=False)),
        yaxis=ax(ticksuffix="%", zeroline=True, zerolinewidth=1))
    current_annotation(fig, spread, "+.2f", suffix="%")
    return fig

def chart_yields(tnx: pd.Series, fvx: pd.Series, irx: pd.Series) -> go.Figure:
    fig = go.Figure()
    traces = [
        (irx, GRAY,  "3M T-Bill"),
        (fvx, AMBER, "5Y"),
        (tnx, GREEN, "10Y"),
    ]
    for s, color, name in traces:
        if s.empty: continue
        fig.add_trace(go.Scatter(x=s.index, y=s,
            line=dict(color=color, width=1.8), name=name,
            hovertemplate=f"%{{x|%d.%m.%Y}}  {name}: %{{y:.2f}}%<extra></extra>"))
    fig.update_layout(**BASE, title=t("Treasury Yields"), height=320,
        margin=dict(l=50, r=70, t=62, b=40),
        xaxis=ax(showgrid=False), yaxis=ax(ticksuffix="%"))
    current_annotation(fig, tnx, ".2f", suffix="%")
    return fig

def chart_inflation(cpi: pd.Series, core_cpi: pd.Series) -> go.Figure:
    cpi_yoy      = cpi.pct_change(12).mul(100).dropna()
    core_cpi_yoy = core_cpi.pct_change(12).mul(100).dropna()
    fig = go.Figure()
    fig.add_hline(y=2.0, line=dict(color=GREEN, width=1, dash="dot"),
                  annotation_text="Fed Target 2%",
                  annotation_font=dict(color=GREEN, size=9, family=MONO),
                  annotation_position="bottom right")
    if not cpi_yoy.empty:
        fig.add_trace(go.Scatter(x=cpi_yoy.index, y=cpi_yoy,
            line=dict(color=WHITE, width=2), name="CPI",
            hovertemplate="%{x|%b %Y}  CPI: %{y:.1f}%<extra></extra>"))
    if not core_cpi_yoy.empty:
        fig.add_trace(go.Scatter(x=core_cpi_yoy.index, y=core_cpi_yoy,
            line=dict(color=AMBER, width=2, dash="dash"), name="Core CPI",
            hovertemplate="%{x|%b %Y}  Core CPI: %{y:.1f}%<extra></extra>"))
    fig.update_layout(**BASE, title=t("Inflation · CPI & Core CPI YoY"), height=320,
        margin=dict(l=50, r=75, t=62, b=40),
        xaxis=ax(showgrid=False), yaxis=ax(ticksuffix="%"))
    current_annotation(fig, cpi_yoy, ".1f", suffix="%")
    return fig

def chart_gdp(gdp: pd.Series) -> go.Figure:
    # Kategorische X-Achse: Q1 '23, Q2 '23, ...
    quarter_map = {1: "Q1", 4: "Q2", 7: "Q3", 10: "Q4"}
    labels  = [f"{quarter_map.get(ts.month, '?')}'{ts.strftime('%y')}" for ts in gdp.index]
    values  = gdp.values.tolist()

    # Farbe: über 2% Trend = Blau, 0–2% = gedämpftes Grau-Blau, negativ = Rot
    def bar_color(v):
        if v >= 2.0:  return "#4da6ff"
        if v >= 0:    return "#6b8fa8"
        return RED

    colors     = [bar_color(v) for v in values]
    text_vals  = [f"{v:+.1f}%" for v in values]
    text_pos   = ["outside" if v >= 0 else "outside" for v in values]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=colors, opacity=0.9, line=dict(width=0)),
        text=text_vals,
        textposition="outside",
        textfont=dict(family=MONO, size=9, color=GRAY),
        hovertemplate="%{x}  <b>%{y:+.1f}%</b><extra></extra>",
        cliponaxis=False,
    ))

    # Nulllinie
    fig.add_hline(y=0, line=dict(color=LINE, width=1))
    # Trend-Linie bei 2% – Annotation links außerhalb der Balken
    fig.add_hline(y=2.0, line=dict(color="#4da6ff", width=1, dash="dot"))
    fig.add_annotation(
        x=0, y=2.0, xref="paper", yref="y",
        text="Ø-Trend 2%",
        showarrow=False, xanchor="left",
        font=dict(family=MONO, size=9, color="#4da6ff"),
        bgcolor=BG2, borderpad=2,
        yshift=8,
    )

    # Y-Range mit Luft für Textwerte außerhalb der Balken
    y_min = min(values) - abs(min(values)) * 0.5 - 1.0
    y_max = max(values) + abs(max(values)) * 0.4 + 1.2

    fig.update_layout(**BASE, title=t("Real GDP · QoQ annualisiert (%)"), height=320,
        margin=dict(l=50, r=30, t=62, b=40),
        xaxis=ax(showgrid=False, tickangle=0, type="category"),
        yaxis=ax(ticksuffix="%", dtick=2, range=[y_min, y_max]),
        showlegend=False, bargap=0.45)
    return fig

def chart_nfp(nfp: pd.Series) -> go.Figure:
    monthly = nfp.diff().dropna().iloc[-24:]
    BLUE_BAR = "#4da6ff"
    colors   = [BLUE_BAR if v >= 0 else RED for v in monthly]
    # X-Achse: nur ausgewählte Monate beschriften (Jan, Apr, Jul, Okt, Dez)
    tick_vals, tick_text = [], []
    for ts in monthly.index:
        if ts.month in (1, 4, 7, 10):
            tick_vals.append(ts)
            tick_text.append(ts.strftime("%m/%y"))
    fig = go.Figure(go.Bar(
        x=monthly.index, y=monthly,
        marker=dict(color=colors, opacity=0.9, line=dict(width=0)),
        hovertemplate="%{x|%m/%Y}  %{y:+,.0f}k Jobs<extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color=LINE, width=1))
    avg = monthly.mean()
    fig.add_hline(y=avg, line=dict(color=AMBER, width=1, dash="dot"),
                  annotation_text=f"Ø {avg:+,.0f}k",
                  annotation_font=dict(color=AMBER, size=9, family=MONO),
                  annotation_position="top right")
    fig.update_layout(**BASE, title=t("Non-Farm Payrolls · Monthly Change"), height=320,
        margin=dict(l=55, r=20, t=62, b=40),
        xaxis=ax(showgrid=False, tickmode="array", tickvals=tick_vals, ticktext=tick_text, tickangle=0),
        yaxis=ax(ticksuffix="k"),
        showlegend=False, bargap=0.2)
    return fig

def chart_unemployment(unemp: pd.Series) -> go.Figure:
    fig = go.Figure()
    if not unemp.empty:
        tick_vals, tick_text = [], []
        for ts in unemp.index:
            if ts.month in (1, 4, 7, 10):
                tick_vals.append(ts)
                tick_text.append(ts.strftime("%m/%y"))
        mn = float(unemp.min())
        mx = float(unemp.max())
        padding = (mx - mn) * 0.3
        y_min = max(0, mn - padding)
        y_max = mx + padding
        fig.add_trace(go.Scatter(x=unemp.index, y=unemp,
            line=dict(color=AMBER, width=2),
            fill="tozeroy", fillcolor="rgba(255,201,60,0.06)",
            hovertemplate="%{x|%m/%Y}  %{y:.1f}%<extra></extra>",
            showlegend=False))
        fig.update_layout(**BASE, title=t("Unemployment Rate"), height=320,
            margin=dict(l=50, r=70, t=62, b=40),
            xaxis=ax(showgrid=False, tickmode="array", tickvals=tick_vals, ticktext=tick_text, tickangle=0),
            yaxis=ax(ticksuffix="%", dtick=0.1, range=[y_min, y_max]))
    else:
        fig.update_layout(**BASE, title=t("Unemployment Rate"), height=320,
            margin=dict(l=50, r=70, t=62, b=40),
            xaxis=ax(showgrid=False), yaxis=ax(ticksuffix="%"))
    current_annotation(fig, unemp, ".1f", suffix="%")
    return fig

def chart_vix(vix: pd.Series) -> go.Figure:
    fig = go.Figure()
    fig.add_hrect(y0=0,  y1=15,  fillcolor="rgba(57,255,20,0.04)",  line_width=0, layer="below")
    fig.add_hrect(y0=15, y1=25,  fillcolor="rgba(255,201,60,0.04)", line_width=0, layer="below")
    fig.add_hrect(y0=25, y1=100, fillcolor="rgba(255,77,77,0.05)",  line_width=0, layer="below")
    if not vix.empty:
        fig.add_trace(go.Scatter(x=vix.index, y=vix,
            line=dict(color=WHITE, width=1.8),
            hovertemplate="%{x|%d.%m.%Y}  VIX: %{y:.1f}<extra></extra>",
            showlegend=False))
    for level, col, lbl in [(15, GREEN, "15 — Low Vol"), (25, RED, "25 — Fear")]:
        fig.add_hline(y=level, line=dict(color=col, width=0.8, dash="dot"),
                      annotation_text=lbl,
                      annotation_font=dict(color=col, size=9, family=MONO),
                      annotation_position="top right")
    ymax = max(55, float(vix.max()) * 1.1) if not vix.empty else 50
    fig.update_layout(**BASE, title=t("VIX · Volatility Index"), height=320,
        margin=dict(l=45, r=20, t=62, b=40),
        xaxis=ax(showgrid=False), yaxis=ax(range=[0, ymax]),
        showlegend=False)
    current_annotation(fig, vix, ".1f")
    return fig

def chart_dxy_gold(dxy: pd.Series, gold: pd.Series) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if not dxy.empty:
        fig.add_trace(go.Scatter(x=dxy.index, y=dxy,
            line=dict(color=AMBER, width=1.8), name="DXY",
            hovertemplate="DXY: %{y:.1f}<extra></extra>"), secondary_y=False)
    if not gold.empty:
        fig.add_trace(go.Scatter(x=gold.index, y=gold,
            line=dict(color=GREEN, width=1.8), name="Gold",
            hovertemplate="Gold: $%{y:,.0f}<extra></extra>"), secondary_y=True)
    fig.update_layout(**BASE, title=t("DXY · Gold"), height=320,
        margin=dict(l=50, r=65, t=62, b=40))
    _ax = dict(gridcolor=GRID, linecolor=LINE, tickfont=dict(family=MONO, size=10, color=GRAY),
               showspikes=True, spikecolor=LINE, spikethickness=1)
    fig.update_yaxes(**_ax, secondary_y=False)
    fig.update_yaxes(**_ax, tickprefix="$", secondary_y=True)
    fig.update_xaxes(gridcolor=GRID, linecolor=LINE, showgrid=False,
                     tickfont=dict(family=MONO, size=10, color=GRAY))
    return fig

def chart_oil_copper(oil: pd.Series, copper: pd.Series) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if not oil.empty:
        fig.add_trace(go.Scatter(x=oil.index, y=oil,
            line=dict(color="#ff8c42", width=1.8), name="WTI Crude",
            hovertemplate="WTI: $%{y:.1f}<extra></extra>"), secondary_y=False)
    if not copper.empty:
        fig.add_trace(go.Scatter(x=copper.index, y=copper,
            line=dict(color="#d4944a", width=1.8), name="Copper",
            hovertemplate="Copper: $%{y:.3f}<extra></extra>"), secondary_y=True)
    fig.update_layout(**BASE, title=t("WTI Crude · Copper"), height=320,
        margin=dict(l=50, r=70, t=62, b=40))
    _ax = dict(gridcolor=GRID, linecolor=LINE, tickfont=dict(family=MONO, size=10, color=GRAY),
               showspikes=True, spikecolor=LINE, spikethickness=1)
    fig.update_yaxes(**_ax, tickprefix="$", secondary_y=False)
    fig.update_yaxes(**_ax, tickprefix="$", secondary_y=True)
    fig.update_xaxes(gridcolor=GRID, linecolor=LINE, showgrid=False,
                     tickfont=dict(family=MONO, size=10, color=GRAY))
    return fig

def chart_sp500(sp: pd.Series) -> go.Figure:
    fig = go.Figure()
    if not sp.empty:
        ma200 = sp.rolling(200).mean()
        above = sp >= ma200
        fig.add_trace(go.Scatter(x=sp.index, y=sp,
            line=dict(color=GREEN, width=1.8),
            fill="tozeroy", fillcolor="rgba(57,255,20,0.04)",
            hovertemplate="%{x|%d.%m.%Y}  S&P 500: %{y:,.0f}<extra></extra>",
            name="S&P 500"))
        fig.add_trace(go.Scatter(x=ma200.index, y=ma200,
            line=dict(color=GRAY, width=1.2, dash="dot"),
            hovertemplate="200 MA: %{y:,.0f}<extra></extra>",
            name="200 MA"))
    fig.update_layout(**BASE, title=t("S&P 500 · 200-Tage MA"), height=320,
        margin=dict(l=55, r=70, t=62, b=40),
        xaxis=ax(showgrid=False), yaxis=ax(tickprefix="$"))
    current_annotation(fig, sp, ",.0f", prefix="$")
    return fig

# ── HTML Builder ──────────────────────────────────────────────────────────────
def div(fig: go.Figure, div_id: str) -> str:
    return pio.to_html(fig, full_html=False, include_plotlyjs=False,
                       div_id=div_id, config={"staticPlot": True, "displayModeBar": False, "responsive": True})

def kpi_card(label: str, value: str, sub: str = "", color: str = WHITE) -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""<div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value" style="color:{color}">{value}</div>
      {sub_html}
    </div>"""

def signal_card(s: dict) -> str:
    icon_map = {"UP": "&#9650;", "DOWN": "&#9660;", "NEU": "&#9679;"}
    lbl = s['label']
    v   = s['value']
    if lbl in ("CPI YoY", "Core CPI YoY", "Real GDP QoQ", "Unemployment Rate"):
        fmt = f"{v:.1f}%"
    elif lbl in ("10Y Yield", "Yield Curve 10Y-3M"):
        fmt = f"{v:.2f}%"
    elif lbl == "NFP Monthly Change":
        fmt = f"{v:,.0f}k"
    elif lbl == "VIX":
        fmt = f"{v:.1f}"
    elif lbl == "DXY":
        fmt = f"{v:.1f}"
    else:
        fmt = f"{v:.2f}"
    return f"""<div class="sig-card sig-{s['signal']}">
      <div class="sig-label">{s['label']}</div>
      <div class="sig-val" style="color:{s['color']}">{icon_map[s['icon']]} {fmt}</div>
      <div class="sig-badge badge-{s['signal']}">{s['signal'].upper()}</div>
    </div>"""

def build(charts: dict, signals: list, score: int, data: dict) -> str:
    sc = GREEN if score >= 60 else (AMBER if score >= 40 else RED)
    sl = "BULLISH" if score >= 60 else ("NEUTRAL" if score >= 40 else "BEARISH")
    bull = sum(1 for s in signals if s["signal"] == "bullish")
    neut = sum(1 for s in signals if s["signal"] == "neutral")
    interp_html = ai_interpretation(signals, score)
    bear = sum(1 for s in signals if s["signal"] == "bearish")

    def fmt(s, f=".2f", pre="", suf=""):
        v = last_val(s)
        return f"{pre}{v:{f}}{suf}" if v else "N/A"

    def yoy(s):
        d = s.pct_change(12).mul(100).dropna()
        v = last_val(d)
        return f"{v:.1f}%" if v else "N/A"

    tnx_val   = fmt(data["tnx"], ".2f", suf="%")
    irx_val   = fmt(data["irx"], ".2f", suf="%")
    spread_v  = last_val(data["tnx"]) - last_val(data["irx"]) if last_val(data["tnx"]) and last_val(data["irx"]) else None
    spread_s  = f"{spread_v:+.2f}%" if spread_v is not None else "N/A"
    cpi_s     = yoy(data["cpi"])
    core_s    = yoy(data["core_cpi"])
    unemp_s   = fmt(data["unemp"], ".1f", suf="%")
    vix_s     = fmt(data["vix"],  ".1f")
    dxy_s     = fmt(data["dxy"],  ".1f")
    gold_s    = fmt(data["gold"], ",.0f", pre="$")
    sp_s      = fmt(data["sp"],   ",.0f", pre="$")

    kpis = "".join([
        kpi_card("10Y Treasury", tnx_val,  f"3M: {irx_val}",  AMBER if last_val(data["tnx"]) and last_val(data["tnx"]) > 4.5 else GREEN),
        kpi_card("Yield Curve", spread_s, "10Y - 3M",         GREEN if spread_v and spread_v > 0 else RED),
        kpi_card("CPI YoY",    cpi_s,    f"Core: {core_s}",   GREEN if cpi_s != "N/A" and float(cpi_s[:-1]) < 3 else RED),
        kpi_card("Unemployment", unemp_s, "Letzte Meldung",   GREEN if unemp_s != "N/A" and float(unemp_s[:-1]) < 4.5 else AMBER),
        kpi_card("VIX",        vix_s,    "Volatilitaet",      GREEN if vix_s != "N/A" and float(vix_s) < 15 else (AMBER if float(vix_s) < 25 else RED)),
        kpi_card("DXY",        dxy_s,    "US Dollar Index",   WHITE),
        kpi_card("Gold",       gold_s,   "XAU/USD",           GREEN),
        kpi_card("S&P 500",    sp_s,     "Letzter Kurs",      GREEN),
    ])

    sig_html = "".join(signal_card(s) for s in signals)
    cal_html = build_calendar_html()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LAE Macro Analysis · {DATE_STR}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#090c11;--bg2:#0d111a;--bg3:#111720;
  --g:#39ff14;--w:#f0f4f8;--gr:#7a8899;
  --r:#ff4d4d;--a:#ffc93c;
  --b:rgba(255,255,255,0.07);--bg:rgba(57,255,20,0.2);
  --gl:rgba(57,255,20,0.08);--radius:14px;
}}
html{{background:#090c11;scroll-behavior:smooth}}
body{{background:#090c11;color:var(--w);font-family:'Inter',sans-serif;font-size:14px;min-height:100vh}}

/* Header */
.hdr{{background:rgba(13,17,26,0.92);border-bottom:1px solid rgba(255,255,255,0.07);
  backdrop-filter:blur(20px);position:sticky;top:0;z-index:100}}
.hdr-i{{padding:0 40px;
  display:flex;align-items:center;justify-content:space-between;height:60px}}
.logo{{display:flex;align-items:center;gap:10px;text-decoration:none}}
.logo-txt{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px}}
.logo-lae{{color:var(--g)}}
.logo-rest{{color:var(--w)}}
.logo-claim{{font-size:10px;color:var(--gr);letter-spacing:0.05em;
  font-family:'JetBrains Mono',monospace;margin-top:2px}}
.hdr-right{{display:flex;align-items:center;gap:16px;
  font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--gr)}}
.chip{{background:#111720;border:1px solid rgba(255,255,255,0.07);
  padding:5px 12px;border-radius:8px;color:var(--w)}}
.score-pill{{background:#111720;border:1px solid rgba(57,255,20,0.25);
  padding:5px 14px;border-radius:8px;font-weight:700;color:{sc};
  box-shadow:0 0 14px rgba(57,255,20,0.08)}}

/* Layout */
.wrap{{padding:28px 40px 64px}}

/* Section */
.sec-hdr{{display:flex;align-items:center;gap:10px;
  margin:36px 0 16px;padding-bottom:12px;
  border-bottom:1px solid rgba(255,255,255,0.06)}}
.sec-dot{{width:6px;height:6px;border-radius:50%;background:var(--g);
  box-shadow:0 0 8px var(--g);flex-shrink:0}}
.sec-title{{font-size:10px;font-weight:700;letter-spacing:0.16em;
  color:var(--gr);text-transform:uppercase}}
.sec-hdr:first-child{{margin-top:0}}

/* Macro Score Card */
.macro-card{{background:#0d111a;border:1px solid rgba(57,255,20,0.18);
  border-radius:var(--radius);box-shadow:0 0 50px rgba(57,255,20,0.05);
  overflow:hidden}}
.macro-top{{display:flex;align-items:stretch;
  border-bottom:1px solid rgba(255,255,255,0.06)}}
.gauge-col{{flex:0 0 340px;padding:8px 0;
  display:flex;align-items:center;justify-content:center}}
.divider{{flex:0 0 1px;background:rgba(255,255,255,0.06)}}
.info-col{{flex:1;min-width:0;padding:28px 32px;
  display:flex;flex-direction:column;justify-content:center;gap:20px}}
.text-col{{padding:24px 32px}}
.text-col-label{{font-size:9px;font-weight:700;letter-spacing:0.16em;
  text-transform:uppercase;color:var(--gr);margin-bottom:14px}}
.text-col-label{{font-size:9px;font-weight:700;letter-spacing:0.16em;
  text-transform:uppercase;color:var(--gr);margin-bottom:14px}}
.interp{{font-size:12px;line-height:1.75;color:var(--gr)}}
.interp p{{margin-bottom:10px}}
.interp p:last-child{{margin-bottom:0}}
.interp strong{{color:var(--w);font-weight:600}}
.score-headline{{font-size:13px;font-weight:700;letter-spacing:0.14em;
  text-transform:uppercase;color:var(--gr)}}
.score-signal{{font-family:'JetBrains Mono',monospace;font-size:42px;font-weight:700;
  line-height:1;color:{sc};text-shadow:0 0 30px {sc}44}}
.score-num{{font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--gr);margin-top:4px}}
.score-sub{{font-size:11px;color:var(--gr)}}
.count-row{{display:flex;gap:28px;padding-top:20px;
  border-top:1px solid rgba(255,255,255,0.06)}}
.count-item{{text-align:left}}
.count-n{{font-family:'JetBrains Mono',monospace;font-size:32px;font-weight:700;line-height:1}}
.count-l{{font-size:9px;letter-spacing:0.12em;color:var(--gr);margin-top:5px}}
.bull .count-n{{color:var(--g)}}
.neut .count-n{{color:var(--a)}}
.bear .count-n{{color:var(--r)}}

/* Signals */
.sig-grid{{display:grid;grid-template-columns:repeat(9,1fr);gap:8px}}
.sig-card{{background:#0d111a;border:1px solid rgba(255,255,255,0.07);
  border-radius:10px;padding:10px 12px;
  transition:border-color .2s,transform .15s;cursor:default}}
.sig-card:hover{{transform:translateY(-1px)}}
.sig-bullish{{border-left:3px solid var(--g)}}
.sig-bearish{{border-left:3px solid var(--r)}}
.sig-neutral{{border-left:3px solid var(--a)}}
.sig-label{{font-size:9px;color:var(--gr);letter-spacing:0.03em;margin-bottom:6px;
  text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sig-val{{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700;margin-bottom:6px}}
.sig-badge{{display:inline-block;font-size:8px;font-weight:700;
  letter-spacing:0.1em;padding:2px 6px;border-radius:4px}}
.badge-bullish{{background:rgba(57,255,20,0.12);color:var(--g)}}
.badge-bearish{{background:rgba(255,77,77,0.12);color:var(--r)}}
.badge-neutral{{background:rgba(255,201,60,0.12);color:var(--a)}}

/* Charts */
.chart-2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.chart-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}}
.chart-2-1{{display:grid;grid-template-columns:2fr 1fr;gap:14px}}
.c{{background:#0d111a;border:1px solid rgba(255,255,255,0.07);
  border-radius:var(--radius);overflow:hidden;
  transition:border-color .2s}}
.c:hover{{border-color:rgba(255,255,255,0.12)}}
.c.full{{grid-column:1/-1}}

/* Economic Calendar */
.cal-row{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:4px}}
.cal-card{{display:flex;align-items:center;gap:12px;
  background:#0d111a;border:1px solid rgba(255,255,255,0.07);
  border-radius:10px;padding:12px 16px;flex:1;min-width:180px}}
.cal-card.cal-soon{{border-color:rgba(57,255,20,0.35);box-shadow:0 0 12px rgba(57,255,20,.08)}}
.cal-card.cal-today{{border-color:#39ff14;box-shadow:0 0 20px rgba(57,255,20,.15)}}
.cal-icon{{font-size:1.4rem}}
.cal-body{{flex:1}}
.cal-name{{font-size:9px;font-weight:600;color:var(--gr);text-transform:uppercase;letter-spacing:.05em}}
.cal-date{{font-family:'JetBrains Mono',monospace;font-size:.9rem;font-weight:700;color:var(--w);margin-top:3px}}
.cal-badge{{font-family:'JetBrains Mono',monospace;font-size:.65rem;font-weight:700;
  padding:3px 8px;border-radius:4px;background:rgba(57,255,20,0.12);color:var(--g);white-space:nowrap}}
.cal-card.cal-later .cal-badge{{background:rgba(255,255,255,0.06);color:var(--gr)}}

/* Footer */
.ftr{{margin:48px 0 0;
  padding:20px 40px;border-top:1px solid rgba(255,255,255,0.06);
  display:flex;justify-content:space-between;align-items:center;
  font-size:10px;color:var(--gr);font-family:'JetBrains Mono',monospace}}

@media(max-width:1100px){{
  .macro-top{{flex-direction:column}}
  .gauge-col{{flex:none;width:100%}}
  .info-col{{flex:none;width:100%}}
  .divider{{flex:none;height:1px;width:100%}}
  .chart-2,.chart-2-1{{grid-template-columns:1fr}}
  .chart-3{{grid-template-columns:1fr 1fr}}
  .wrap{{padding:20px 16px 40px}}
}}
@media(max-width:700px){{
  .chart-3{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>

<header class="hdr">
  <div class="hdr-i">
    <a class="logo" href="#">
      <svg width="26" height="26" viewBox="0 0 60 60" fill="none">
        <path d="M30,4 L54,17 L54,43 L30,56 L6,43 L6,17 Z" fill="rgba(57,255,20,.08)" stroke="#39ff14" stroke-width="1.5"/>
        <polyline points="16,40 24,28 30,33 40,18" fill="none" stroke="#39ff14" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        <polyline points="40,25 40,18 34,21" fill="none" stroke="#39ff14" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <div>
        <div class="logo-txt"><span class="logo-lae">LAE</span><span class="logo-rest"> Market Services</span></div>
        <div class="logo-claim">Learn. Analyze. Execute.</div>
      </div>
    </a>
    <div class="hdr-right">
      <span>Macro Analysis</span>
      <span class="chip">{DATE_STR}</span>
      <span class="score-pill">{sl} &nbsp;·&nbsp; {score}/100</span>
    </div>
  </div>
</header>

<div class="wrap">

  <!-- ECONOMIC CALENDAR -->
  <div class="sec-hdr" style="margin-top:0">
    <div class="sec-dot"></div>
    <div class="sec-title">Economic Calendar &middot; Upcoming Dates</div>
  </div>
  <div class="cal-row">{cal_html}</div>

  <!-- MACRO SCORE -->
  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Macro Score · US Markets Overview</div>
  </div>
  <div class="macro-card">
    <div class="macro-top">
      <div class="gauge-col">{div(charts['gauge'], 'gauge')}</div>
      <div class="divider"></div>
      <div class="info-col">
        <div>
          <div class="score-headline">US Macro Overview</div>
          <div class="score-signal">{sl}</div>
          <div class="score-num">{score} / 100</div>
        </div>
        <div class="score-sub">{len(signals)} Indikatoren &nbsp;·&nbsp; {DATE_STR}</div>
        <div class="count-row">
          <div class="count-item bull"><div class="count-n">{bull}</div><div class="count-l">BULLISH</div></div>
          <div class="count-item neut"><div class="count-n">{neut}</div><div class="count-l">NEUTRAL</div></div>
          <div class="count-item bear"><div class="count-n">{bear}</div><div class="count-l">BEARISH</div></div>
        </div>
      </div>
    </div>
    <div class="text-col">
      <div class="text-col-label">Macro Assessment</div>
      <div class="interp">{interp_html}</div>
    </div>
  </div>

  <!-- KEY METRICS -->
  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Key Metrics</div>
  </div>
  <div class="sig-grid">{sig_html}</div>

  <!-- INFLATION & WACHSTUM -->
  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Inflation &amp; Growth</div>
  </div>
  <div class="chart-2">
    <div class="c">{div(charts['inflation'], 'infl')}</div>
    <div class="c">{div(charts['gdp'], 'gdp')}</div>
  </div>

  <!-- FED & ZINSEN -->
  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Fed &amp; Rates</div>
  </div>
  <div class="chart-2">
    <div class="c">{div(charts['yield_curve'], 'yc')}</div>
    <div class="c">{div(charts['yields'], 'yields')}</div>
  </div>

  <!-- ARBEITSMARKT -->
  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Labor Market</div>
  </div>
  <div class="chart-2">
    <div class="c">{div(charts['nfp'], 'nfp')}</div>
    <div class="c">{div(charts['unemp'], 'unemp')}</div>
  </div>

  <!-- MARKTSTRUKTUR -->
  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Market Structure &amp; Sentiment</div>
  </div>
  <div class="chart-2">
    <div class="c">{div(charts['sp'], 'sp')}</div>
    <div class="c">{div(charts['vix'], 'vix')}</div>
  </div>
  <div class="chart-2" style="margin-top:14px">
    <div class="c">{div(charts['dxy_gold'], 'dg')}</div>
    <div class="c">{div(charts['oil_copper'], 'oc')}</div>
  </div>

</div>

<footer class="ftr">
  <span>Sources: Yahoo Finance &middot; BLS (Bureau of Labor Statistics) &middot; FRED Federal Reserve (optional)</span>
  <span>LAE Market Services &middot; {TODAY.strftime("%Y-%m-%d")}</span>
</footer>

<script>
(function(){{
  function sendHeight(){{
    var ftr = document.querySelector('.ftr');
    var h = ftr
      ? Math.ceil(ftr.getBoundingClientRect().bottom + window.scrollY)
      : document.documentElement.scrollHeight;
    window.parent.postMessage({{frameHeight: h}}, '*');
  }}
  window.addEventListener('load', function(){{
    sendHeight();
    setTimeout(sendHeight, 500);
    setTimeout(sendHeight, 1500);
    setTimeout(sendHeight, 3000);
  }});
}})();
</script>
</body></html>"""

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key", default=os.environ.get("FRED_API_KEY", ""))
    args = ap.parse_args()

    print(f"LAE Macro Analysis - {DATE_STR}")
    print("Lade Daten...\n")

    # Yields (Yahoo Finance)
    print("  [Yahoo] Treasury Yields...")
    tnx = yahoo("^TNX", "2y")   # 10Y
    fvx = yahoo("^FVX", "2y")   # 5Y
    irx = yahoo("^IRX", "2y")   # 3M T-Bill

    # Inflation & Labor (BLS - kein Key, ein Batch-Request)
    print("  [BLS]   CPI / Unemployment / NFP...")
    bls_data = bls_batch(["CUUR0000SA0", "CUUR0000SA0L1E", "LNS14000000", "CES0000000001"])
    cpi      = bls_data["CUUR0000SA0"]
    core_cpi = bls_data["CUUR0000SA0L1E"]
    unemp    = bls_data["LNS14000000"]
    nfp      = bls_data["CES0000000001"]

    # GDP (FRED falls Key vorhanden, sonst Fallback-Daten)
    print("  [GDP]   Real GDP...")
    gdp = fetch_gdp(args.api_key)

    # Market Data (Yahoo Finance)
    print("  [Yahoo] Marktdaten...")
    vix    = yahoo("^VIX",    "2y")
    dxy    = yahoo("DX-Y.NYB","2y")
    gold   = yahoo("GC=F",    "2y")
    oil    = yahoo("CL=F",    "2y")
    copper = yahoo("HG=F",    "2y")
    sp     = yahoo("^GSPC",   "2y")

    # FRED optional
    if args.api_key:
        print("  [FRED]  Erweiterte Daten...")
        core_pce   = fred("PCEPILFE", args.api_key, START_3Y)
        claims     = fred("ICSA",     args.api_key, START_2Y)
        fedfunds   = fred("FEDFUNDS", args.api_key, START_2Y)
    else:
        print("  [Info]  Kein FRED-Key - Basis-Daten ausreichend.")
        core_pce = claims = fedfunds = pd.Series(dtype=float)

    print("\n  Berechne Signale...")
    signals = []

    # --- Inflation & Wachstum ---
    if not cpi.empty and len(cpi) >= 13:
        cpi_yoy = float(cpi.pct_change(12).dropna().iloc[-1]) * 100
        signals.append(sig("CPI YoY", cpi_yoy,
            lambda v: v <= 2.5, lambda v: v > 3.5))

    if not core_cpi.empty and len(core_cpi) >= 13:
        core_yoy = float(core_cpi.pct_change(12).dropna().iloc[-1]) * 100
        signals.append(sig("Core CPI YoY", core_yoy,
            lambda v: v <= 2.5, lambda v: v > 3.5))

    if not gdp.empty:
        signals.append(sig("Real GDP QoQ", float(gdp.dropna().iloc[-1]),
            lambda v: v >= 2.5, lambda v: v < 0))

    # --- Fed & Zinsen ---
    if not tnx.empty and not irx.empty:
        spread = float(tnx.dropna().iloc[-1]) - float(irx.dropna().iloc[-1])
        signals.append(sig("Yield Curve 10Y-3M", spread,
            lambda v: v > 0.05, lambda v: v < -0.15))

    if not tnx.empty:
        signals.append(sig("10Y Yield", float(tnx.dropna().iloc[-1]),
            lambda v: v < 4.0, lambda v: v > 4.8))

    # --- Arbeitsmarkt ---
    if not unemp.empty:
        signals.append(sig("Unemployment Rate", float(unemp.dropna().iloc[-1]),
            lambda v: v <= 4.2, lambda v: v > 5.0))

    if not nfp.empty:
        nfp_chg = float(nfp.diff().dropna().iloc[-1])
        signals.append(sig("NFP Monthly Change", nfp_chg,
            lambda v: v > 150, lambda v: v < 0))

    # --- Marktstruktur & Sentiment ---
    if not vix.empty:
        signals.append(sig("VIX", float(vix.dropna().iloc[-1]),
            lambda v: v <= 15, lambda v: v > 25))

    if not dxy.empty:
        signals.append(sig("DXY", float(dxy.dropna().iloc[-1]),
            lambda v: v <= 100, lambda v: v > 107))

    score = macro_score(signals)
    print(f"  Score: {score}/100 | {len(signals)} Indikatoren")

    print("\n  Generiere Charts...")
    charts = {
        "gauge":       chart_gauge(score),
        "yield_curve": chart_yield_curve(tnx, irx),
        "yields":      chart_yields(tnx, fvx, irx),
        "inflation":   chart_inflation(cpi, core_cpi),
        "gdp":         chart_gdp(gdp),
        "nfp":         chart_nfp(nfp),
        "unemp":       chart_unemployment(unemp),
        "vix":         chart_vix(vix),
        "dxy_gold":    chart_dxy_gold(dxy, gold),
        "oil_copper":  chart_oil_copper(oil, copper),
        "sp":          chart_sp500(sp),
    }

    print("  Baue HTML...")
    data = dict(tnx=tnx, irx=irx, cpi=cpi, core_cpi=core_cpi,
                unemp=unemp, vix=vix, dxy=dxy, gold=gold, sp=sp)
    html = build(charts, signals, score, data)

    out = OUTPUT_DIR / f"lae-macro-analysis-{DATE_STR}.html"
    out.write_text(html, encoding="utf-8")
    print(f"\nFertig: {out}\n")

if __name__ == "__main__":
    main()
