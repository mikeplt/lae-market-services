"""
LAE Earnings Analysis – HTML Generator
Usage: python generate.py  (from the skills/earnings-analysis folder)
Output: ../../outputs/earnings-analysis/earnings-analysis-TICKER-QUARTER.html
"""
from pathlib import Path

# ── HEADER ────────────────────────────────────────────────────────────────────
DATA = {
    "DATUM":           "May 21, 2026",
    "TICKER":          "NVDA",
    "COMPANY_NAME":    "NVIDIA Corporation",
    "QUARTER":         "Q1 FY2027",
    "REPORT_DATE":     "May 20, 2026",
    "REPORT_TIME":     "After Close",
    "STOCK_PREV_DATE": "May 20",       # Schlusskurs am Tag der Earnings (vor AH)
    "STOCK_PREV":      "$ 220.60",     # Kurs vor Earnings
    "STOCK_POST_DATE": "May 21",       # Erster Handelstag nach Earnings
    "STOCK_AFTER":     "$ 220.66",     # Schlusskurs nach Earnings
    "STOCK_REACT":     "▲ +0.0%",     # Tatsächliche Kursreaktion (AH +1.4%, dann Fading)
    "REACT_CLASS":     "green",        # "green" oder "red"
    "TV_IFRAME_SRC": (
        "https://www.tradingview.com/embed-widget/mini-symbol-overview/"
        "?symbol=NASDAQ%3ANVDA&locale=en&dateRange=12M&colorTheme=dark"
        "&trendLineColor=%2339ff14&underLineColor=rgba(57%2C255%2C20%2C0.15)"
        "&underLineBottomColor=rgba(57%2C255%2C20%2C0)&isTransparent=true&autosize=true"
    ),
}

# ── ACTUAL RESULTS ─────────────────────────────────────────────────────────────
# Format: (Metric, Estimate aus Preview, Actual, vs_text, vs_class, status)
# vs_class: "pos" (grün) | "neg" (rot) | "neutral" (gelb)
# status:   "beat" | "missed" | "in-line"
RESULTS = [
    ("Revenue (total)",       "$ 78.8B",   "$ 81.6B",  "▲ +$2.8B",    "pos",     "beat"),
    ("Data Center Revenue",   "$ 72.9B",   "$ 75.2B",  "▲ +$2.3B",    "pos",     "beat"),
    ("Gaming Revenue",        "$ 3.6B",    "$ 3.7B",   "▲ +$0.1B",    "pos",     "beat"),
    ("EPS (non-GAAP adj.)",   "$ 1.77",    "$ 1.87",   "▲ +$0.10",    "pos",     "beat"),
    ("Gross Margin (adj.)",   "~ 75.0%",   "75.0%",    "—",           "neutral", "in-line"),
]

# ── SCENARIO RESULT ────────────────────────────────────────────────────────────
# played_out: "bull" | "base" | "bear"
SCENARIO_RESULT = {
    "played_out": "bull",
    "tag":        "Bull",
    "reaction":   "▲ +1.4% AH / flat",
    "driver":     "Data Center Beat + Q2 Guidance $91B vs. $80B Consensus",
    "revenue":    "$ 81.6B",
    "eps":        "$ 1.87",
    "summary":    (
        "NVIDIA delivered a textbook bull quarter – but the market barely moved. Revenue of $81.6B "
        "beat the $78.8B consensus by $2.8B, up 85% year-over-year. Data Center hit $75.2B (+92% YoY), "
        "driven entirely by Blackwell GPU shipments to hyperscalers. The true market-mover was Q2 "
        "guidance of $91B – a staggering $11B above the $80B Street consensus and well above even the "
        "bull-case threshold of $82B. Despite these blockbuster numbers, the stock rose just +1.4% in "
        "after-hours trading and closed flat the next day at $220.66 – suggesting the beat was already "
        "priced in and investors focused on the China headwind (zero H20 revenue in Q2 guidance)."
    ),
}

# ── CATALYST REVIEW ────────────────────────────────────────────────────────────
# Format: (Nr, Title, status, Beschreibung was tatsächlich passiert ist)
# status: "triggered" | "missed" | "partial"
CATALYST_RESULTS = [
    ("01", "Data Center Revenue vs. $72.9B", "triggered",
     "Data Center revenue hit a record $75.2B, up 92% year-over-year, beating the $72.9B consensus "
     "by $2.3B. Compute alone reached $60.4B (+77% YoY), with Networking adding $14.8B (+199% YoY). "
     "Blackwell GPU shipments to hyperscalers drove the entire outperformance – demand remains fully unbound."),
    ("02", "Q2 FY2027 Revenue Guidance", "triggered",
     "NVIDIA guided Q2 revenue to $91.0B (±2%) – a jaw-dropping $11B above the $80B Street consensus "
     "and far beyond the bull-case threshold of $82B. This is the most aggressive quarterly guidance "
     "beat in NVIDIA's history and confirms the Blackwell demand cycle is accelerating, not plateauing."),
    ("03", "China / Export Controls Update", "partial",
     "The Q2 guidance of $91B explicitly assumes zero data center compute revenue from China, as H20 "
     "exports remain banned. No policy relief, no alternative products for China announced. The headwind "
     "is fully baked in – no escalation, but no resolution either. This capped the stock's upside reaction."),
    ("04", "Q2 Gross Margin Guidance", "in-line",
     "Q2 non-GAAP gross margin guided at ~75.0% (±50 bps) – exactly in line with Q1 actuals and consensus. "
     "Blackwell manufacturing yields are stabilizing rather than rapidly improving. No margin expansion "
     "catalyst for the near term; the margin story remains a watch item for H2 FY2027."),
    ("05", "Blackwell Demand & Supply Commentary", "triggered",
     "Jensen Huang confirmed Blackwell demand is 'insane' with customer order backlogs extending well into "
     "H2 2026. Supply is ramping on schedule with new GB200 NVLink configurations driving higher ASPs. "
     "Professional Visualization surpassed $1B for the first time ($1.3B, +159% YoY), signaling Blackwell "
     "penetration beyond hyperscalers into enterprise AI workloads."),
]

# ── FORWARD GUIDANCE ───────────────────────────────────────────────────────────
# Format: (Metric, Alte Guidance, Neue Guidance, change_class)
# change_class: "pos" | "neg" | "neutral"
GUIDANCE = [
    ("Q2 FY2027 Revenue",              "~ $80.0B (consensus)",  "$91.0B (±2%)",    "pos"),
    ("Q2 Non-GAAP Gross Margin",       "~ 75.0%",               "~ 75.0% (±50 bps)", "neutral"),
    ("Q2 Non-GAAP Operating Expenses", "—",                     "~ $8.3B",         "neutral"),
    ("Q2 GAAP Operating Expenses",     "—",                     "~ $8.5B",         "neutral"),
]

# ── OUTLOOK ────────────────────────────────────────────────────────────────────
# Format: (Nr, Title, Text) – 3–4 Ausblickspunkte
OUTLOOK = [
    ("01", "Q2 Guidance Shock – $91B vs. $80B",
     "A guidance beat of $11B above consensus is nearly unprecedented at NVIDIA's scale. The Q2 guide "
     "implies sequential revenue growth of ~11% from Q1's $81.6B, driven entirely by continued Blackwell "
     "shipment acceleration. The key risk: this guidance explicitly excludes China. If export policy "
     "shifts even modestly, $91B could prove conservative – the upside optionality is significant."),
    ("02", "China Headwind – Priced In, Not Resolved",
     "Zero H20 revenue is already baked into Q2 guidance. The China market – historically ~20% of NVIDIA's "
     "data center business – remains closed for high-end compute. Management offered no timeline for "
     "resolution or alternative product launches. This single variable caps the bull narrative and "
     "explains the muted stock reaction despite a historic guidance beat."),
    ("03", "Shareholder Returns – Dividend 25x Raise",
     "NVIDIA raised its quarterly cash dividend from $0.01 to $0.25 per share – a 25x increase – and "
     "returned a record ~$20B to shareholders via buybacks and dividends in Q1. Free cash flow of $49B "
     "annualizes to ~$196B, one of the highest FCF yields of any company in history. Capital return "
     "capacity is no longer a question; the question is where to direct it."),
    ("04", "Market Reaction – 'Sell the News' Dynamics",
     "The stock rose just +1.4% AH and closed flat at $220.66 the next day – well below the implied "
     "move of ±8.0%. This pattern reflects 'buy the rumor, sell the news': NVDA's AI momentum was "
     "already embedded at $225.32 (preview price). Key support at $210–215, resistance at $230–235. "
     "A sustained move above $235 requires either China policy relief or another guidance acceleration in Q2."),
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
