"""
LAE Earnings Preview – HTML Generator
Usage: python generate.py  (from the skills/earnings-preview folder)
Output: ../../outputs/earnings-preview/earnings-preview-MSFT-Q3-FY2026.html
"""
from pathlib import Path

# ── HEADER ────────────────────────────────────────────────────────────────────
DATA = {
    "DATUM":        "May 18, 2026",
    "TICKER":       "NVDA",
    "COMPANY_NAME": "Nvidia Corporation",
    "QUARTER":      "Q1 FY2027",
    "REPORT_DATE":  "May 20, 2026",
    "REPORT_TIME":  "After Close",
    "STOCK_DATE":   "May 18",
    "STOCK_PRICE":  "$ 225.32",
    "IMPLIED_MOVE": "± 8.0%",
    "TV_IFRAME_SRC": (
        "https://www.tradingview.com/embed-widget/mini-symbol-overview/"
        "?symbol=NASDAQ%3ANVDA&locale=en&dateRange=12M&colorTheme=dark"
        "&trendLineColor=%2339ff14&underLineColor=rgba(57%2C255%2C20%2C0.15)"
        "&underLineBottomColor=rgba(57%2C255%2C20%2C0)&isTransparent=true&autosize=true"
    ),
}

# ── CONSENSUS ESTIMATES ───────────────────────────────────────────────────────
# Format: (Metric, Consensus, Prior Year, YoY, yoy_class)
ESTIMATES = [
    ("Revenue (total)",      "$ 78.8B",  "$ 44.1B",   "▲ 78.7%",    "pos"),
    ("Data Center",          "$ 72.9B",  "$ 39.3B",   "▲ 85.4%",    "pos"),
    ("Gaming",               "$ 3.6B",   "$ 2.6B",    "▲ 38.5%",    "pos"),
    ("EPS (adj.)",           "$ 1.77",   "$ 0.78",    "▲ 126.9%",   "pos"),
    ("Gross Margin (adj.)",  "~ 75.0%",  "~ 78.4%",   "▼ 340 bps",  "neg"),
]

# ── KEY METRICS TO WATCH ──────────────────────────────────────────────────────
# Format: (Rank, Title, Description)
METRICS = [
    ("1", "Data Center Revenue vs. $72.9B",
     "The single most important number — driven entirely by Blackwell GPU shipments to hyperscalers. "
     "A beat above $75B signals demand remains unbroken and supply constraints are easing. "
     "A miss below $70B would call the entire AI capex cycle into question."),
    ("2", "Q2 FY2027 Revenue Guidance",
     "Consensus expects ~$80B for Q2. This number moves the stock more than the Q1 print itself — "
     "NVDA trades on trajectory. Guidance above $82B triggers a re-rating; anything below $78B "
     "overshadows even a strong Q1 beat."),
    ("3", "China / Export Control Commentary",
     "NVIDIA guided zero H20 revenue following US export restrictions. Any update on alternative "
     "products for China, policy relief, or demand redirection is the highest-variance wildcard — "
     "it can move the stock ±5% independent of any other number."),
    ("4", "Gross Margin Trajectory",
     "Q1 consensus is ~75.0% non-GAAP, down from 78.4% in Q1 FY2026 due to Blackwell ramp costs. "
     "Q2 gross margin guidance above 75.5% signals manufacturing yields are improving ahead of schedule "
     "and unlocks the margin expansion story for the rest of FY2027."),
]

# ── SCENARIOS ─────────────────────────────────────────────────────────────────
# Format: (class, tag, reaction, revenue, eps, driver, description)
SCENARIOS = [
    ("bull", "Bull", "+8–15%",
     "> $ 80B", "> $ 1.90",
     "Data Center Beat + Q2 Guidance Raise",
     "Data Center revenues exceed $75B on stronger-than-expected Blackwell shipments. Q2 guidance "
     "comes in above $82B, confirming continued acceleration. China commentary turns neutral-to-positive. "
     "Gross margin guidance for Q2 above 76% signals Blackwell cost normalization. "
     "Stock clears $235 resistance and targets the $260–280 zone."),
    ("base", "Base", "± 2–5%",
     "~ $ 78.8B", "~ $ 1.77",
     "Consensus Met, Guidance In-Line",
     "Revenue and EPS land at or slightly above consensus. Q2 guidance comes in around $80B, "
     "in line with expectations. China remains a headwind but no escalation. "
     "Gross margins stabilize near 75%. Stock moves within the implied range — "
     "mildly positive reaction or consolidation near current levels."),
    ("bear", "Bear", "− 8–15%",
     "< $ 77B", "< $ 1.65",
     "Data Center Miss + Weak Q2 Guidance",
     "Data Center falls short of $70B due to supply issues or demand softness from hyperscalers. "
     "Q2 guidance below $76B signals a deceleration in the Blackwell ramp. "
     "Negative China commentary or further export restrictions announced. "
     "Gross margins compress below 74%. Stock risks retesting the $196–200 support cluster."),
]

# ── CATALYST CHECKLIST ────────────────────────────────────────────────────────
# Format: (Number, Title, Description)
CATALYSTS = [
    ("01", "Data Center Revenue vs. $72.9B",
     "The headline number — any beat above $75B signals Blackwell demand is fully unbound. "
     "A miss below $70B would trigger a sharp selloff as it questions the hyperscaler AI capex narrative."),
    ("02", "Q2 FY2027 Revenue Guidance",
     "Consensus: ~$80B. This is the most market-moving number — NVDA trades on the trajectory, "
     "not the rearview mirror. Guidance above $82B triggers a re-rating; below $78B triggers selling."),
    ("03", "China / Export Controls Update",
     "NVIDIA guided zero H20 revenue. Any commentary on H20 replacements, licensing workarounds, "
     "or a shift in US policy toward Nvidia is the highest-surprise factor in either direction."),
    ("04", "Q2 Gross Margin Guidance",
     "Q1 consensus is ~75.0%. A Q2 gross margin guide above 75.5% signals Blackwell manufacturing "
     "yields are improving — a structural positive for the margin story beyond FY2027."),
    ("05", "Blackwell Demand & Supply Commentary",
     "CEO Jensen Huang's tone on order backlog, lead times, and customer demand visibility. "
     "Any signal that supply is beginning to exceed demand — or new capacity expansion plans — "
     "drives long-term sentiment and can reshape the valuation narrative."),
]

# ── TRADING SETUP ─────────────────────────────────────────────────────────────
# Format: (Label, Value, class)  class: "red" | "green" | ""
TRADING = [
    ("Price (May 18)",               "$ 225.32",                  ""),
    ("52-Week Range",                "$ 112 – $ 225",             ""),
    ("YTD Performance",              "▲ 15.4%",                   "green"),
    ("Avg. Earnings Reaction",       "± 6.3%",                    ""),
    ("Implied Move (Options)",       "± 8.0%",                    "red"),
    ("Analyst Consensus",            "Strong Buy / 70 Analysten", ""),
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
