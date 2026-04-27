"""
LAE Earnings Preview – HTML Generator
Usage: python generate.py  (from the skills/earnings-preview folder)
Output: ../../outputs/earnings-preview/earnings-preview-V-Q2-FY2026.html
"""
from pathlib import Path

# ── HEADER ────────────────────────────────────────────────────────────────────
DATA = {
    "DATUM":        "April 27, 2026",
    "TICKER":       "V",
    "COMPANY_NAME": "Visa Inc.",
    "QUARTER":      "Q2 FY2026",
    "REPORT_DATE":  "April 28, 2026",
    "REPORT_TIME":  "After Close",
    "STOCK_DATE":   "Apr. 25",
    "STOCK_PRICE":  "$ 309.10",
    "IMPLIED_MOVE": "± 3.5%",
    "TV_IFRAME_SRC": (
        "https://www.tradingview.com/embed-widget/mini-symbol-overview/"
        "?symbol=NYSE%3AV&locale=en&dateRange=12M&colorTheme=dark"
        "&trendLineColor=%2339ff14&underLineColor=rgba(57%2C255%2C20%2C0.15)"
        "&underLineBottomColor=rgba(57%2C255%2C20%2C0)&isTransparent=true&autosize=true"
    ),
}

# ── CONSENSUS ESTIMATES ───────────────────────────────────────────────────────
# Format: (Metric, Consensus, Prior Year, YoY, yoy_class)
ESTIMATES = [
    ("Revenue (total)",           "$ 10.7B",  "$ 9.6B",   "▲ 11.5%",  "pos"),
    ("Service Revenue",           "$ 4.91B",  "$ 4.40B",  "▲ 11.6%",  "pos"),
    ("Data Processing Revenue",   "$ 5.30B",  "$ 4.70B",  "▲ 12.8%",  "pos"),
    ("EPS (adj.)",                "$ 3.09",   "$ 2.76",   "▲ 12.0%",  "pos"),
]

# ── KEY METRICS TO WATCH ──────────────────────────────────────────────────────
# Format: (Rank, Title, Description)
METRICS = [
    ("1", "Cross-Border Volume (ex. intra-Europe)",
     "Q2 FY2025: +13% YoY. Consensus expects ~+12%. This is Visa's highest-margin "
     "business line – driven by international travel and cross-border e-commerce."),
    ("2", "Total Payment Volume",
     "Q2 FY2025: ~+8% constant currency. Consensus expects ~+9% YoY. "
     "A beat signals US consumer resilience and global spending momentum."),
    ("3", "FY2026 Guidance Update",
     "Full-year EPS consensus: $12.84. Any guidance revision is the key re-rating catalyst. "
     "Management tone on consumer spending and macro outlook drives the post-print move."),
    ("4", "Net Revenue (Constant Currency)",
     "Q2 FY2025: +11% in constant currency. USD strength may create a headwind – "
     "constant-currency growth gives the cleanest read of underlying business momentum."),
]

# ── SCENARIOS ─────────────────────────────────────────────────────────────────
# Format: (class, tag, reaction, revenue, eps, driver, description)
SCENARIOS = [
    ("bull", "Bull", "+8–12%",
     "> $ 11.0B", "> $ 3.15",
     "Cross-Border Beat + Guidance Raise",
     "Cross-border volume grows above 15%, total payment volume exceeds $4.3T. "
     "Management raises FY2026 EPS guidance above $13.00. Strong international travel "
     "and consumer spending confirm demand resilience despite macro headwinds."),
    ("base", "Base", "± 2–4%",
     "~ $ 10.7B", "~ $ 3.09",
     "Consensus Met, Guidance Stable",
     "Results meet expectations. Payment volume grows ~9% YoY, cross-border at ~12%. "
     "FY2026 guidance maintained. Strong business fundamentals – "
     "stock moves sideways to slightly positive."),
    ("bear", "Bear", "− 7–12%",
     "< $ 10.3B", "< $ 2.90",
     "Volume Miss + Guidance Cut",
     "Payment volumes disappoint amid macro uncertainty and consumer slowdown. "
     "Cross-border decelerates below 10%. Management lowers Q3/FY2026 guidance – "
     "the recent recovery in the stock is fully reversed."),
]

# ── CATALYST CHECKLIST ────────────────────────────────────────────────────────
# Format: (Number, Title, Description)
CATALYSTS = [
    ("01", "Cross-Border Volume (ex. intra-Europe)",
     "Q2 FY2025: +13% YoY. Every 100 bps above consensus signals premium travel "
     "and international spending demand – Visa's highest-margin business line."),
    ("02", "Total Payment Volume",
     "Q2 FY2025: ~$3.93T (+8% constant currency). A beat above $4.3T (+10% YoY) "
     "confirms US consumer resilience despite tariff uncertainty."),
    ("03", "FY2026 EPS Guidance",
     "Full-year consensus at $12.84 (+11.9% YoY). Any revision higher triggers an "
     "immediate re-rating. A cut – even modest – drives sharp downside given current valuation."),
    ("04", "Processed Transactions",
     "Q2 FY2025: +9% YoY. An acceleration signals strong everyday spending "
     "and continued digital payment adoption across global markets."),
    ("05", "Capital Return Program",
     "Visa announced a $30B buyback in Q2 FY2025. Any new buyback authorization "
     "or dividend increase would be an additional positive surprise for shareholders."),
]

# ── TRADING SETUP ─────────────────────────────────────────────────────────────
# Format: (Label, Value, class)  class: "red" | "green" | ""
TRADING = [
    ("Price (Apr. 25)",             "$ 309.10",          ""),
    ("52-Week Range",               "$ 293 – 376",       ""),
    ("YTD Performance",             "▼ 8.5%",            "red"),
    ("Avg. Earnings Reaction",      "± 4.2%",            ""),
    ("Implied Move (Options)",      "± 3.5%",            "red"),
    ("Analyst Consensus",           "Buy / 31 analysts", ""),
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
