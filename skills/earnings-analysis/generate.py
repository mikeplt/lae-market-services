"""
LAE Earnings Analysis – HTML Generator
Usage: python generate.py  (from the skills/earnings-analysis folder)
Output: ../../outputs/earnings-analysis/earnings-analysis-TICKER-QUARTER.html
"""
from pathlib import Path

# ── HEADER ────────────────────────────────────────────────────────────────────
DATA = {
    "DATUM":           "April 29, 2026",
    "TICKER":          "KO",
    "COMPANY_NAME":    "The Coca-Cola Company",
    "QUARTER":         "Q1 FY2026",
    "REPORT_DATE":     "April 28, 2026",
    "REPORT_TIME":     "Before Open",
    "STOCK_PREV_DATE": "Apr. 25",       # Tag vor den Earnings (Kurs aus Preview)
    "STOCK_PREV":      "$ 76.31",       # Kurs vor Earnings
    "STOCK_POST_DATE": "Apr. 28",       # Tag nach den Earnings
    "STOCK_AFTER":     "$ 78.59",       # Schlusskurs nach Earnings
    "STOCK_REACT":     "▲ 3.0%",        # Tatsächliche Kursreaktion
    "REACT_CLASS":     "green",         # "green" oder "red"
    "TV_IFRAME_SRC": (
        "https://www.tradingview.com/embed-widget/mini-symbol-overview/"
        "?symbol=NYSE%3AKO&locale=en&dateRange=12M&colorTheme=dark"
        "&trendLineColor=%2339ff14&underLineColor=rgba(57%2C255%2C20%2C0.15)"
        "&underLineBottomColor=rgba(57%2C255%2C20%2C0)&isTransparent=true&autosize=true"
    ),
}

# ── ACTUAL RESULTS ─────────────────────────────────────────────────────────────
# Format: (Metric, Estimate aus Preview, Actual, vs_text, vs_class, status)
# vs_class: "pos" (grün) | "neg" (rot) | "neutral" (gelb)
# status:   "beat" | "missed" | "in-line"
RESULTS = [
    ("Revenue (total)",       "$ 12.2B",  "$ 12.5B",  "▲ +$0.3B",   "pos", "beat"),
    ("Organic Revenue Growth","~ +5.5%",  "+10%",     "▲ +4.5 pp",  "pos", "beat"),
    ("EPS (adj.)",            "$ 0.81",   "$ 0.86",   "▲ +$0.05",   "pos", "beat"),
    ("Unit Case Volume",      "~ +2%",    "+3%",      "▲ +1 pp",    "pos", "beat"),
]

# ── SCENARIO RESULT ────────────────────────────────────────────────────────────
# played_out: "bull" | "base" | "bear"
SCENARIO_RESULT = {
    "played_out": "bull",
    "tag":        "Bull",
    "reaction":   "▲ 3.0%",
    "driver":     "Organic Growth Surge + Full Beat + Guidance Raise",
    "revenue":    "$ 12.5B",
    "eps":        "$ 0.86",
    "summary":    (
        "Coca-Cola delivered its best organic revenue growth in five quarters at +10%, "
        "massively topping the ~+5.5% consensus estimate. Volume, price, and mix all contributed. "
        "Management raised full-year EPS guidance to 8–9% growth from the prior 7–8% outlook. "
        "The stock surged intraday (+4.49%) before closing up 3.0% at $78.59 – "
        "above the implied move of ±2.5%."
    ),
}

# ── CATALYST REVIEW ────────────────────────────────────────────────────────────
# Format: (Nr, Title, status, Beschreibung was tatsächlich passiert ist)
# status: "triggered" | "missed" | "partial"
CATALYST_RESULTS = [
    ("01", "Organic Revenue Growth", "triggered",
     "Organic revenue grew +10% – the best result in five quarters and far above the ~+5.5% consensus estimate. "
     "Driven by 8% concentrate sales growth and 2% price/mix improvement."),
    ("02", "Unit Case Volume", "triggered",
     "Unit case volume grew +3%, beating the ~+2% estimate. "
     "Growth was broad-based across all operating segments, supported by strong brand activation and innovation."),
    ("03", "FY2026 EPS Guidance", "triggered",
     "Full-year comparable EPS growth guidance raised to 8–9% (from 7–8% prior), "
     "driven by a lower effective tax rate of 19.9% and stronger underlying business momentum."),
    ("04", "New CEO Braun – Strategic Commentary", "triggered",
     "CEO James Quincey's successor provided constructive commentary on portfolio strategy and volume recovery. "
     "Market viewed the tone as confident and execution-focused – no major strategic pivots announced."),
    ("05", "Currency Headwinds", "triggered",
     "A 3% currency tailwind (positive surprise vs. prior headwind expectations) boosted comparable EPS. "
     "The FX environment shifted favorably, removing a key bear-case risk heading into H2 2026."),
]

# ── FORWARD GUIDANCE ───────────────────────────────────────────────────────────
# Format: (Metric, Alte Guidance, Neue Guidance, change_class)
# change_class: "pos" | "neg" | "neutral"
GUIDANCE = [
    ("Organic Revenue Growth FY2026", "mid-single digits",  "4–5%",         "neutral"),
    ("Comparable EPS Growth FY2026",  "+7–8% (vs. $3.00)",  "+8–9%",        "pos"),
    ("Effective Tax Rate FY2026",     "~ 20.5%",            "19.9%",        "pos"),
    ("Currency Impact",               "headwind",           "~3% tailwind", "pos"),
]

# ── OUTLOOK ────────────────────────────────────────────────────────────────────
# Format: (Nr, Title, Text) – 3–4 Ausblickspunkte
OUTLOOK = [
    ("01", "Organic Growth Sustainability",
     "The +10% organic growth print was the best in five quarters, but the bar is now reset higher. "
     "Q2 2026 consensus sits around +5–6% – any deceleration would be scrutinized. "
     "Management's 4–5% full-year guidance implies a moderation, keeping expectations in check."),
    ("02", "Volume Recovery Trajectory",
     "+3% unit case volume marks a meaningful re-acceleration from prior sluggishness. "
     "The key question for H2 2026 is whether volume can hold at 2–3% as pricing tailwinds fade. "
     "Emerging market performance and North America execution will be the key indicators to watch."),
    ("03", "Currency Tailwind Duration",
     "The unexpected 3% FX tailwind was a key upside driver for comparable EPS. "
     "This is unlikely to persist at this magnitude – if the dollar strengthens in H2, "
     "the FX benefit reverses and creates a headwind vs. raised expectations."),
    ("04", "Valuation & Price Target",
     "KO closed at $78.59 after the print – a fair reward for a strong beat. "
     "At these levels the stock trades at a slight premium to historical averages. "
     "Key support at $76, resistance at $80–82. Defensive profile remains intact for risk-off environments."),
]

# ── HTML BUILD ────────────────────────────────────────────────────────────────
_STATUS_LABELS = {
    "beat":    "Beat",
    "missed":  "Missed",
    "in-line": "In-Line",
}

_CATALYST_LABELS = {
    "triggered": "Triggered",
    "missed":    "Missed",
    "partial":   "Partial",
}

_GUIDANCE_ARROWS = {
    "pos":     "▲",
    "neg":     "▼",
    "neutral": "—",
}

def build_results():
    rows = []
    for metric, estimate, actual, vs_text, vs_class, status in RESULTS:
        label = _STATUS_LABELS.get(status, status)
        rows.append(
            f'<tr>'
            f'<td class="td-label">{metric}</td>'
            f'<td class="td-num">{estimate}</td>'
            f'<td class="td-actual">{actual}</td>'
            f'<td class="td-vs {vs_class}"><span class="vs-pill">{vs_text}</span></td>'
            f'<td class="td-status"><span class="status-badge {status}">{label}</span></td>'
            f'</tr>'
        )
    return "\n".join(rows)

def build_catalyst_review():
    items = []
    for nr, title, status, text in CATALYST_RESULTS:
        label = _CATALYST_LABELS.get(status, status)
        items.append(
            f'<div class="catalyst-review-item">'
            f'<div class="catalyst-badge {status}">{nr} {label}</div>'
            f'<div class="catalyst-review-text"><strong>{title}</strong><span>{text}</span></div>'
            f'</div>'
        )
    return "\n".join(items)

def build_guidance():
    rows = []
    for metric, old_g, new_g, change_class in GUIDANCE:
        arrow = _GUIDANCE_ARROWS.get(change_class, "—")
        rows.append(
            f'<tr>'
            f'<td class="td-guidance-label">{metric}</td>'
            f'<td class="td-guidance-old">{old_g}</td>'
            f'<td class="td-guidance-new">{new_g}</td>'
            f'<td class="td-guidance-change {change_class}"><span class="change-pill">{arrow}</span></td>'
            f'</tr>'
        )
    return "\n".join(rows)

def build_outlook():
    items = []
    for nr, title, text in OUTLOOK:
        items.append(
            f'<div class="outlook-item">'
            f'<div class="outlook-num">{nr}</div>'
            f'<div class="outlook-text"><strong>{title}</strong><span>{text}</span></div>'
            f'</div>'
        )
    return "\n".join(items)

def render_template():
    tpl = Path("template.html").read_text(encoding="utf-8")
    s   = SCENARIO_RESULT
    data = dict(DATA)
    data["SCENARIO_CLASS"]        = s["played_out"]
    data["SCENARIO_TAG"]          = s["tag"]
    data["SCENARIO_REACTION"]     = s["reaction"]
    data["SCENARIO_DRIVER"]       = s["driver"]
    data["SCENARIO_REVENUE"]      = s["revenue"]
    data["SCENARIO_EPS"]          = s["eps"]
    data["SCENARIO_SUMMARY"]      = s["summary"]
    data["RESULT_ROWS"]           = build_results()
    data["CATALYST_REVIEW_ITEMS"] = build_catalyst_review()
    data["GUIDANCE_ROWS"]         = build_guidance()
    data["OUTLOOK_ITEMS"]         = build_outlook()
    for key, val in data.items():
        tpl = tpl.replace("{{" + key + "}}", val)
    return tpl

if __name__ == "__main__":
    ticker  = DATA["TICKER"]
    quarter = DATA["QUARTER"].replace(" ", "-")
    out = Path(f"../../outputs/earnings-analysis/earnings-analysis-{ticker}-{quarter}.html")
    out.parent.mkdir(exist_ok=True)
    html = render_template()
    out.write_text(html, encoding="utf-8")
    print(f"HTML created: {out.resolve()}")
