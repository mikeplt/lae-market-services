"""
LAE Earnings Preview – HTML Generator
Usage: python generate.py  (from the skills/earnings-preview folder)
Output: ../../outputs/earnings-preview/earnings-preview-TSLA-Q1-FY2026.html
"""
from pathlib import Path

# ── HEADER ────────────────────────────────────────────────────────────────────
DATA = {
    "DATUM":        "April 19, 2026",
    "TICKER":       "TSLA",
    "COMPANY_NAME": "Tesla, Inc.",
    "QUARTER":      "Q1 FY2026",
    "REPORT_DATE":  "April 22, 2026",
    "REPORT_TIME":  "After Close",
    "STOCK_DATE":   "Apr. 18",
    "STOCK_PRICE":  "$ 400.62",
    "IMPLIED_MOVE": "± 6.92%",
    "TV_IFRAME_SRC": (
        "https://www.tradingview.com/embed-widget/mini-symbol-overview/"
        "?symbol=NASDAQ%3ATSLA&locale=en&dateRange=12M&colorTheme=dark"
        "&trendLineColor=%2339ff14&underLineColor=rgba(57%2C255%2C20%2C0.15)"
        "&underLineBottomColor=rgba(57%2C255%2C20%2C0)&isTransparent=true&autosize=true"
    ),
}

# ── CONSENSUS ESTIMATES ───────────────────────────────────────────────────────
# Format: (Metric, Consensus, Prior Year, YoY, yoy_class)
ESTIMATES = [
    ("Revenue (total)",           "$ 21.4B",   "$ 19.34B",  "▲ 10.7%",  "pos"),
    ("Automotive Revenue",        "$ 14.5B",   "$ 13.7B",   "▲ 5.8%",   "pos"),
    ("Energy & Storage Revenue",  "$ 3.5B",    "$ 2.73B",   "▲ 28.2%",  "pos"),
    ("Gross Margin",              "16.5%",     "16.3%",     "▲ 20 bps", "pos"),
    ("Automotive Gross Margin",   "16.0%",     "15.0%",     "▲ 100 bps","pos"),
    ("EPS (adj.)",                "$ 0.37",    "$ 0.27",    "▲ 37.0%",  "pos"),
]

# ── KEY METRICS TO WATCH ──────────────────────────────────────────────────────
# Format: (Rank, Title, Description)
METRICS = [
    ("1", "Automotive Gross Margin",
     "Consensus expects 16.0% (vs. 15.0% prior year). Tariff headwinds and price cuts make "
     "the margin outlook the key metric for H2 guidance."),
    ("2", "Energy & Storage Revenue",
     "The growth segment generates ~30% margin – more than twice the automotive business. "
     "A beat supports the AI/energy infrastructure narrative."),
    ("3", "FSD & Robotaxi Roadmap",
     "A concrete Cybercab timeline (H2 2026?) is the most important re-rating catalyst. "
     "The market is increasingly pricing in AI value – management must deliver with data."),
    ("4", "Deliveries & Q2 Outlook",
     "Q1 expected: 365,645 vehicles (▲ 8.6% YoY). The Q2 outlook shows whether demand "
     "recovery is sustainable or disappoints again."),
]

# ── SCENARIOS ─────────────────────────────────────────────────────────────────
# Format: (class, tag, reaction, revenue, eps, driver, description)
SCENARIOS = [
    ("bull", "Bull", "+15–20%",
     "> $ 22.0B", "> $ 0.43",
     "Energy Beat + Margin Surprise",
     "Energy revenue above $ 4.0B, Automotive Gross Margin at 17% or higher. "
     "A clear Robotaxi timeline triggers an AI re-rating. Management raises FY2026 guidance."),
    ("base", "Base", "± 3–7%",
     "~ $ 21.4B", "~ $ 0.37",
     "In-line, Positive Outlook",
     "Results meet consensus. Margin stable, Energy grows on plan. "
     "FSD update without major surprise – stock moves sideways to slightly positive."),
    ("bear", "Bear", "− 12–18%",
     "< $ 20.5B", "< $ 0.28",
     "Demand Miss + Margin Pressure",
     "Delivery numbers disappoint, tariff headwinds push Automotive Gross Margin below 14%. "
     "No concrete Robotaxi timeline – recent gains are given back."),
]

# ── CATALYST CHECKLIST ────────────────────────────────────────────────────────
# Format: (Number, Title, Description)
CATALYSTS = [
    ("01", "Automotive Gross Margin",
     "Consensus: 16.0%. Every positive basis point signals pricing power despite tariff headwinds. "
     "Management commentary on H2 2026 guidance is decisive."),
    ("02", "Energy & Storage Revenue",
     "If the segment beats the $ 3.5B estimate, the valuation as an energy infrastructure "
     "company rises significantly. The ~30% segment margin is the core re-rating argument."),
    ("03", "FSD Update & Cybercab Timeline",
     "Concrete data on the Cybercab launch (H2 2026?) is the most important catalyst. "
     "The AI narrative supports the current valuation – management must deliver here."),
    ("04", "Q2 Delivery Guidance",
     "Q1: 365,645 vehicles expected. Raising guidance above 400,000 for Q2 would be "
     "a strong buy signal and confirms sustainable demand recovery."),
    ("05", "Free Cash Flow",
     "After negative FCF in Q4 2025: a return to positive territory strengthens the "
     "balance sheet story and reduces structural downside risks."),
]

# ── TRADING SETUP ─────────────────────────────────────────────────────────────
# Format: (Label, Value, class)  class: "red" | "green" | ""
TRADING = [
    ("Price (Apr. 18)",             "$ 400.62",          ""),
    ("52-Week Range",               "$ 222 – 499",       ""),
    ("YTD Performance",             "▲ 14.5%",           "green"),
    ("Avg. Earnings Reaction",      "± 9.8%",            ""),
    ("Implied Move (Options)",      "± 6.92%",           "red"),
    ("Analyst Consensus",           "Buy / 32 analysts", ""),
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
