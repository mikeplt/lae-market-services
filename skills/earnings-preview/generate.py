"""
LAE Earnings Preview – HTML Generator
Usage: python generate.py  (from the skills/earnings-preview folder)
Output: ../../outputs/earnings-preview/earnings-preview-MSFT-Q3-FY2026.html
"""
from pathlib import Path

# ── HEADER ────────────────────────────────────────────────────────────────────
DATA = {
    "DATUM":        "April 28, 2026",
    "TICKER":       "MSFT",
    "COMPANY_NAME": "Microsoft Corporation",
    "QUARTER":      "Q3 FY2026",
    "REPORT_DATE":  "April 29, 2026",
    "REPORT_TIME":  "After Close",
    "STOCK_DATE":   "Apr. 28",
    "STOCK_PRICE":  "$ 424.82",
    "IMPLIED_MOVE": "± 6.8%",
    "TV_IFRAME_SRC": (
        "https://www.tradingview.com/embed-widget/mini-symbol-overview/"
        "?symbol=NASDAQ%3AMSFT&locale=en&dateRange=12M&colorTheme=dark"
        "&trendLineColor=%2339ff14&underLineColor=rgba(57%2C255%2C20%2C0.15)"
        "&underLineBottomColor=rgba(57%2C255%2C20%2C0)&isTransparent=true&autosize=true"
    ),
}

# ── CONSENSUS ESTIMATES ───────────────────────────────────────────────────────
# Format: (Metric, Consensus, Prior Year, YoY, yoy_class)
ESTIMATES = [
    ("Revenue (total)",      "$ 81.3B",  "$ 70.1B",  "▲ 16.0%",  "pos"),
    ("Intelligent Cloud",    "~ $ 30.0B","$ 26.7B",  "▲ 12.4%",  "pos"),
    ("Azure Growth (CC)",    "~ 38%",    "~ 33%",    "▲ 5 pp",   "pos"),
    ("EPS (adj.)",           "$ 4.06",   "$ 3.46",   "▲ 17.3%",  "pos"),
]

# ── KEY METRICS TO WATCH ──────────────────────────────────────────────────────
# Format: (Rank, Title, Description)
METRICS = [
    ("1", "Azure Growth Rate (CC)",
     "Q3 FY2025: 33% CC. Guidance Q3 FY2026: 37–38%. The #1 market focus – "
     "can Azure re-accelerate after decelerating to 31% in Q2? Every point above or below guidance drives outsized stock reaction."),
    ("2", "AI & Copilot Revenue",
     "Concrete Copilot ARR data is what the market craves. Seat count growth, "
     "enterprise adoption rates, and any mention of a $15B+ ARR milestone will be key signals for the AI investment thesis."),
    ("3", "Capital Expenditure Discipline",
     "CapEx is expected near $21–22B for Q3. The market wants to see AI infrastructure spending "
     "translate into Azure acceleration – not just cost escalation without visible returns."),
    ("4", "FY2026 Full-Year Guidance",
     "Any revision to revenue or EPS guidance is the key re-rating catalyst. "
     "Strong Azure + guidance raise = bull case. Cautious or no-raise outlook = renewed pressure on the stock."),
]

# ── SCENARIOS ─────────────────────────────────────────────────────────────────
# Format: (class, tag, reaction, revenue, eps, driver, description)
SCENARIOS = [
    ("bull", "Bull", "+8–12%",
     "> $ 83B", "> $ 4.20",
     "Azure Re-Acceleration + Guidance Raise",
     "Azure grows 40%+ CC, significantly beating guidance. Copilot adoption shows material ARR milestones. "
     "Management raises FY2026 revenue and EPS guidance. CapEx narrative shifts from 'cost' to 'return on investment'. "
     "Stock reclaims $460+ and targets the $480–500 resistance zone."),
    ("base", "Base", "± 2–4%",
     "~ $ 81.3B", "~ $ 4.06",
     "Consensus Met, Outlook Stable",
     "Azure delivers 37–38% growth, in line with guidance. EPS and revenue meet consensus. "
     "Full-year guidance maintained. Market reads the print as solid but without a big surprise – "
     "stock reacts mildly positive or flat, within the implied move range."),
    ("bear", "Bear", "− 7–10%",
     "< $ 79B", "< $ 3.90",
     "Azure Miss + Guidance Cut",
     "Azure falls below 36% CC, missing guidance for the second consecutive quarter. "
     "CapEx pressures margins further. Management lowers or removes FY2026 guidance. "
     "Post-earnings sentiment turns structurally negative – stock risks retesting the $380–390 lows."),
]

# ── CATALYST CHECKLIST ────────────────────────────────────────────────────────
# Format: (Number, Title, Description)
CATALYSTS = [
    ("01", "Azure Growth Rate (CC)",
     "Q3 FY2025: 33% CC. Guidance Q3 FY2026: 37–38%. The #1 market focus – "
     "every percentage point above or below guidance drives outsized stock reaction."),
    ("02", "AI & Copilot Revenue",
     "Seat count growth and ARR milestones for Copilot. "
     "A concrete $15B+ ARR figure or strong enterprise adoption data would validate the AI investment thesis."),
    ("03", "CapEx Efficiency Commentary",
     "Expected CapEx: ~$21–22B. CFO commentary on when AI infrastructure spending "
     "will translate into margin expansion is the key swing factor for long-term investors."),
    ("04", "OpenAI Partnership Update",
     "Microsoft restructured its OpenAI revenue share agreement in April 2026. "
     "Any earnings commentary on the financial impact or strategic implications will move the stock."),
    ("05", "FY2026 Full-Year Guidance",
     "Consensus expects ~14–15% revenue growth for FY2026. A raise confirms Azure re-acceleration. "
     "A hold is neutral. Any cut or removal of guidance triggers severe selling pressure."),
]

# ── TRADING SETUP ─────────────────────────────────────────────────────────────
# Format: (Label, Value, class)  class: "red" | "green" | ""
TRADING = [
    ("Price (Apr. 28)",              "$ 424.82",                  ""),
    ("52-Week Range",                "$ 356 – 555",               ""),
    ("YTD Performance",              "▼ 10.3%",                   "red"),
    ("Avg. Earnings Reaction",       "± 3.8%",                    ""),
    ("Implied Move (Options)",       "± 6.8%",                    "red"),
    ("Analyst Consensus",            "Strong Buy / 53 Analysten", ""),
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
