"""
LAE Earnings Preview – HTML Generator
Usage: python generate.py  (from the skills/earnings-preview folder)
Output: ../../outputs/earnings-preview/earnings-preview-KO-Q1-FY2026.html
"""
from pathlib import Path

# ── HEADER ────────────────────────────────────────────────────────────────────
DATA = {
    "DATUM":        "April 27, 2026",
    "TICKER":       "KO",
    "COMPANY_NAME": "The Coca-Cola Company",
    "QUARTER":      "Q1 FY2026",
    "REPORT_DATE":  "April 28, 2026",
    "REPORT_TIME":  "Before Open",
    "STOCK_DATE":   "Apr. 25",
    "STOCK_PRICE":  "$ 76.31",
    "IMPLIED_MOVE": "± 2.5%",
    "TV_IFRAME_SRC": (
        "https://www.tradingview.com/embed-widget/mini-symbol-overview/"
        "?symbol=NYSE%3AKO&locale=en&dateRange=12M&colorTheme=dark"
        "&trendLineColor=%2339ff14&underLineColor=rgba(57%2C255%2C20%2C0.15)"
        "&underLineBottomColor=rgba(57%2C255%2C20%2C0)&isTransparent=true&autosize=true"
    ),
}

# ── CONSENSUS ESTIMATES ───────────────────────────────────────────────────────
# Format: (Metric, Consensus, Prior Year, YoY, yoy_class)
ESTIMATES = [
    ("Revenue (total)",       "$ 12.2B",  "$ 11.1B",  "▲ 9.9%",   "pos"),
    ("Organic Revenue Growth","~ +5.5%",  "6.0%",     "▼ 50 bps", "neg"),
    ("EPS (adj.)",            "$ 0.81",   "$ 0.73",   "▲ 11.0%",  "pos"),
    ("Unit Case Volume",      "~ +2%",    "+2%",      "→ stable",  ""),
]

# ── KEY METRICS TO WATCH ──────────────────────────────────────────────────────
# Format: (Rank, Title, Description)
METRICS = [
    ("1", "Organic Revenue Growth",
     "Q1 2025: +6% (5% price/mix + 1% volume). Consensus expects ~+5.5% for Q1 2026. "
     "This is the cleanest measure of business momentum – FX-neutral and divestiture-adjusted."),
    ("2", "Unit Case Volume",
     "Q1 2025: +2% globally (driven by India, China, Brazil). "
     "A beat above +3% confirms sustainable demand recovery across emerging markets."),
    ("3", "FY2026 Guidance",
     "Management guided 4–5% organic revenue growth and 7–8% EPS growth for FY2026. "
     "Any upward revision is the primary re-rating catalyst – especially on EPS."),
    ("4", "New CEO Henrique Braun – First Earnings",
     "First report under new CEO. Market watching for strategic direction: "
     "AI integration in marketing/pricing, brand portfolio focus, and capital allocation priorities."),
]

# ── SCENARIOS ─────────────────────────────────────────────────────────────────
# Format: (class, tag, reaction, revenue, eps, driver, description)
SCENARIOS = [
    ("bull", "Bull", "+5–8%",
     "> $ 12.5B", "> $ 0.85",
     "Organic Acceleration + Guidance Raise",
     "Organic revenue growth above 7%, unit case volume above +3%. "
     "New CEO Braun raises FY2026 EPS guidance to top end or above the 7–8% range. "
     "Pricing power confirmed despite tariff environment – Buffett-stock premium re-rates."),
    ("base", "Base", "± 1–3%",
     "~ $ 12.2B", "~ $ 0.81",
     "Consensus Met, Guidance Maintained",
     "Results in line with expectations. Organic growth ~+5.5%, volumes steady at +2%. "
     "FY2026 guidance unchanged. KO remains the defensive safe-haven – "
     "stock drifts sideways to slightly positive."),
    ("bear", "Bear", "− 5–8%",
     "< $ 11.8B", "< $ 0.76",
     "Volume Miss + Guidance Cut",
     "Unit case volumes disappoint, organic growth decelerates below 4%. "
     "Tariff headwinds pressure margins. Management lowers full-year EPS guidance – "
     "the 2026 YTD gains are partially reversed."),
]

# ── CATALYST CHECKLIST ────────────────────────────────────────────────────────
# Format: (Number, Title, Description)
CATALYSTS = [
    ("01", "Organic Revenue Growth",
     "Q1 2025: +6%. Every 50 bps above consensus signals pricing power – "
     "the most important currency-neutral indicator of Coca-Cola's business health."),
    ("02", "Unit Case Volume",
     "Q1 2025: +2% globally. Growth in emerging markets (India, China, Brazil) "
     "is the structural long-term thesis – any acceleration strengthens the bull case."),
    ("03", "FY2026 EPS Guidance",
     "Guidance range: 7–8% EPS growth. A raise to the top end or above signals "
     "confidence in pricing power despite tariffs and FX headwinds."),
    ("04", "New CEO Braun – Strategic Commentary",
     "First earnings call as CEO. Investors watching for updates on AI integration, "
     "brand portfolio strategy, and how Braun plans to sustain Coca-Cola's pricing moat."),
    ("05", "Currency Headwinds",
     "Q1 2025: 5-point FX headwind on comparable EPS. USD strength in Q1 2026 "
     "may repeat – constant-currency commentary is crucial for interpretation."),
]

# ── TRADING SETUP ─────────────────────────────────────────────────────────────
# Format: (Label, Value, class)  class: "red" | "green" | ""
TRADING = [
    ("Price (Apr. 25)",             "$ 76.31",           ""),
    ("52-Week Range",               "$ 65 – 82",         ""),
    ("YTD Performance",             "▲ 9.9%",            "green"),
    ("Avg. Earnings Reaction",      "± 2.8%",            ""),
    ("Implied Move (Options)",      "± 2.5%",            "red"),
    ("Analyst Consensus",           "Buy / 26 analysts", ""),
]

# ── HTML BUILD ────────────────────────────────────────────────────────────────
def build_estimates():
    rows = []
    for metric, consensus, prior, yoy, cls in ESTIMATES:
        rows.append(
            f'<tr>'
            f'<td class="td-label">{metric}</td>'
            f'<td class="td-num">{consensus}</td>'
            f'<td class="td-num td-prev">{prior}</td>'
            f'<td class="td-yoy {cls}"><span class="yoy-pill">{yoy}</span></td>'
            f'</tr>'
        )
    return "\n".join(rows)

def build_metrics():
    items = []
    for _, title, text in METRICS:
        items.append(
            f'<div class="metric-item">'
            f'<div class="metric-icon">'
            f'<svg width="14" height="14" viewBox="0 0 14 14" fill="none">'
            f'<path d="M2 7h10M8 3l4 4-4 4" stroke="#39ff14" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
            f'</svg>'
            f'</div>'
            f'<div class="metric-text"><strong>{title}</strong><span>{text}</span></div>'
            f'</div>'
        )
    return "\n".join(items)

def build_scenarios():
    cards = []
    for cls, tag, reaction, revenue, eps, driver, body in SCENARIOS:
        cards.append(
            f'<div class="scenario-card {cls}">'
            f'<div class="scenario-header">'
            f'<span class="scenario-tag">{tag}</span>'
            f'</div>'
            f'<div class="scenario-reaction">{reaction}</div>'
            f'<div class="scenario-driver">{driver}</div>'
            f'<div class="scenario-nums">'
            f'<div class="scenario-num"><div class="lbl">Revenue</div><div class="val">{revenue}</div></div>'
            f'<div class="scenario-num"><div class="lbl">EPS (adj.)</div><div class="val">{eps}</div></div>'
            f'</div>'
            f'<div class="scenario-body">{body}</div>'
            f'</div>'
        )
    return "\n".join(cards)

def build_catalysts():
    items = []
    for nr, title, text in CATALYSTS:
        items.append(
            f'<div class="catalyst-item">'
            f'<div class="catalyst-num">{nr}</div>'
            f'<div class="catalyst-text"><strong>{title}</strong><span>{text}</span></div>'
            f'</div>'
        )
    return "\n".join(items)

def build_trading():
    cards = []
    for label, val, cls in TRADING:
        cards.append(
            f'<div class="trading-card">'
            f'<div class="lbl">{label}</div>'
            f'<div class="val {cls}">{val}</div>'
            f'</div>'
        )
    return "\n".join(cards)

def render_template():
    tpl = Path("template.html").read_text(encoding="utf-8")
    data = dict(DATA)
    data["ESTIMATE_ROWS"]  = build_estimates()
    data["METRIC_ITEMS"]   = build_metrics()
    data["SCENARIO_CARDS"] = build_scenarios()
    data["CATALYST_ITEMS"] = build_catalysts()
    data["TRADING_CARDS"]  = build_trading()
    for key, val in data.items():
        tpl = tpl.replace("{{" + key + "}}", val)
    return tpl

if __name__ == "__main__":
    ticker  = DATA["TICKER"]
    quarter = DATA["QUARTER"].replace(" ", "-")
    out = Path(f"../../outputs/earnings-preview/earnings-preview-{ticker}-{quarter}.html")
    out.parent.mkdir(exist_ok=True)
    html = render_template()
    out.write_text(html, encoding="utf-8")
    print(f"HTML created: {out.resolve()}")
