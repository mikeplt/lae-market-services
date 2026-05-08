"""
LAE Earnings Analysis – HTML Generator
Usage: python generate.py  (from the skills/earnings-analysis folder)
Output: ../../outputs/earnings-analysis/earnings-analysis-TICKER-QUARTER.html
"""
from pathlib import Path

# ── HEADER ────────────────────────────────────────────────────────────────────
DATA = {
    "DATUM":           "May 8, 2026",
    "TICKER":          "AMD",
    "COMPANY_NAME":    "Advanced Micro Devices, Inc.",
    "QUARTER":         "Q1 FY2026",
    "REPORT_DATE":     "May 5, 2026",
    "REPORT_TIME":     "After Close",
    "STOCK_PREV_DATE": "May 5",        # Schlusskurs am Tag der Earnings (vor AH)
    "STOCK_PREV":      "$ 363.00",     # Kurs vor Earnings
    "STOCK_POST_DATE": "May 6",        # Erster Handelstag nach Earnings
    "STOCK_AFTER":     "$ 421.39",     # Schlusskurs nach Earnings
    "STOCK_REACT":     "▲ +16.1%",    # Tatsächliche Kursreaktion
    "REACT_CLASS":     "green",        # "green" oder "red"
    "TV_IFRAME_SRC": (
        "https://www.tradingview.com/embed-widget/mini-symbol-overview/"
        "?symbol=NASDAQ%3AAMD&locale=en&dateRange=12M&colorTheme=dark"
        "&trendLineColor=%2339ff14&underLineColor=rgba(57%2C255%2C20%2C0.15)"
        "&underLineBottomColor=rgba(57%2C255%2C20%2C0)&isTransparent=true&autosize=true"
    ),
}

# ── ACTUAL RESULTS ─────────────────────────────────────────────────────────────
# Format: (Metric, Estimate aus Preview, Actual, vs_text, vs_class, status)
# vs_class: "pos" (grün) | "neg" (rot) | "neutral" (gelb)
# status:   "beat" | "missed" | "in-line"
RESULTS = [
    ("Revenue (total)",          "$ 9.84B",   "$ 10.25B",  "▲ +$0.41B",  "pos", "beat"),
    ("Data Center Revenue",      "~ $ 5.3B",  "$ 5.8B",    "▲ +$0.5B",   "pos", "beat"),
    ("EPS (non-GAAP adj.)",      "$ 1.25",    "$ 1.37",    "▲ +$0.12",   "pos", "beat"),
    ("Non-GAAP Gross Margin",    "~ 54.5%",   "55.0%",     "▲ +0.5 pp",  "pos", "beat"),
]

# ── SCENARIO RESULT ────────────────────────────────────────────────────────────
# played_out: "bull" | "base" | "bear"
SCENARIO_RESULT = {
    "played_out": "bull",
    "tag":        "Bull",
    "reaction":   "▲ +16.1%",
    "driver":     "Data Center Beat + Full EPS Beat + Strong Q2 Guidance",
    "revenue":    "$ 10.25B",
    "eps":        "$ 1.37",
    "summary":    (
        "AMD delivered its best post-earnings session in seven years – the stock surged +16.1% "
        "on May 6, 2026, closing at $421.39. Revenue of $10.25B crushed the $9.84B consensus by $0.41B, "
        "up 38% year-over-year. The Data Center segment led the way at $5.8B (+57% YoY), driven by "
        "explosive demand for EPYC server CPUs and Instinct AI GPUs. A blockbuster Meta partnership "
        "announcement – up to 6 GW of Instinct GPU deployments – supercharged the bull narrative. "
        "Q2 guidance of $11.2B topped the ~$10.9B estimate, cementing AMD's AI infrastructure momentum."
    ),
}

# ── CATALYST REVIEW ────────────────────────────────────────────────────────────
# Format: (Nr, Title, status, Beschreibung was tatsächlich passiert ist)
# status: "triggered" | "missed" | "partial"
CATALYST_RESULTS = [
    ("01", "Data Center Revenue Surge", "triggered",
     "Data Center segment revenue hit $5.8B, up 57% year-over-year, crushing the ~$5.3B estimate. "
     "Both EPYC server CPUs and Instinct AI GPUs contributed to the outperformance. "
     "AMD's Data Center segment is now the clear growth engine of the company."),
    ("02", "Meta Partnership – Instinct GPU Deployment", "triggered",
     "AMD and Meta announced plans to deploy up to 6 GW of AMD Instinct GPUs, "
     "with the first 1-GW tranche powered by a custom MI450-based GPU. "
     "This is one of the largest single AI infrastructure commitments ever announced – a major demand signal."),
    ("03", "Q2 FY2026 Revenue Guidance Beat", "triggered",
     "AMD guided Q2 revenue to approximately $11.2B (±$300M), well above the ~$10.9B Street estimate. "
     "This represents ~46% year-over-year growth and confirms AI infrastructure demand acceleration "
     "heading into the second half of 2026."),
    ("04", "Non-GAAP EPS Beat", "triggered",
     "Non-GAAP diluted EPS of $1.37 beat the $1.25 consensus by $0.12, or +9.6%. "
     "On a year-over-year basis, EPS grew 43%, reflecting strong operating leverage as "
     "Data Center scale benefits flow through to the bottom line."),
    ("05", "Server CPU Market Share Momentum", "triggered",
     "Lisa Su confirmed server CPU market growth exceeding 35% and a CPU-to-GPU ratio target of 1:1. "
     "Server CPU revenue is expected to grow more than 70% year-over-year in Q2 FY2026, "
     "signaling sustained EPYC share gains versus Intel in the data center."),
]

# ── FORWARD GUIDANCE ───────────────────────────────────────────────────────────
# Format: (Metric, Alte Guidance, Neue Guidance, change_class)
# change_class: "pos" | "neg" | "neutral"
GUIDANCE = [
    ("Q2 FY2026 Revenue",              "~ $10.9B (consensus)",  "$11.2B (±$300M)",  "pos"),
    ("Q2 Non-GAAP Gross Margin",       "~ 54.5%",               "~ 56%",            "pos"),
    ("Q2 Non-GAAP Operating Expenses", "~ $3.2B",               "~ $3.3B",          "neg"),
    ("Server CPU Revenue Growth Q2",   "~ +50% YoY",            "> +70% YoY",       "pos"),
]

# ── OUTLOOK ────────────────────────────────────────────────────────────────────
# Format: (Nr, Title, Text) – 3–4 Ausblickspunkte
OUTLOOK = [
    ("01", "AI Infrastructure Demand Cycle",
     "The Meta partnership – up to 6 GW of Instinct GPU deployments – is a multi-year demand signal. "
     "As hyperscalers ramp AI workloads, AMD's Instinct GPU lineup directly competes with Nvidia's H-series. "
     "The key question for H2 2026: can AMD maintain supply to meet accelerating hyperscaler demand?"),
    ("02", "Server CPU Market Share vs. Intel",
     "AMD's EPYC is firmly in share-gain mode with server CPU revenue expected to grow >70% YoY in Q2. "
     "Lisa Su's 1:1 CPU-to-GPU ratio target signals how deeply AMD is embedding itself "
     "in AI data center infrastructure – a strategic moat that compounds over time."),
    ("03", "Embedded & Gaming Recovery Pace",
     "Embedded revenue of $873M (+6% YoY) is recovering but remains sluggish vs. the Data Center. "
     "Gaming ($720M, +11% YoY) showed resilience driven by Radeon GPU demand. "
     "Neither segment is a near-term growth catalyst – the Data Center dominates the story."),
    ("04", "Valuation & Price Target",
     "AMD closed at $421.39 post-earnings – up +16.1% on its best post-earnings day in seven years. "
     "At these levels, the premium reflects strong AI execution and hyperscaler partnerships. "
     "Key support at $390–400, resistance at $430–440. Continued Data Center outperformance "
     "is required to justify the elevated multiple."),
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
