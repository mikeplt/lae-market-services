"""
LAE Market Services – Daily Note Generator
Pre-market sentiment dashboard with interactive gauges.
Run: python skills/daily-note/generate.py
"""

import sys
import os
import math
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data_fetcher


BASE_DIR = Path(__file__).parent.parent.parent


# ── SVG Gauge Helper ──────────────────────────────────────────────────────────

def _arc_path(f_start: float, f_end: float, r: int = 72, cx: int = 100, cy: int = 96) -> str:
    """SVG path for a half-circle arc segment (fraction 0=left, 1=right)."""
    def frac_xy(f):
        angle = (f - 0.5) * math.pi
        return cx + r * math.sin(angle), cy - r * math.cos(angle)
    x1, y1 = frac_xy(f_start)
    x2, y2 = frac_xy(f_end)
    large = 1 if (f_end - f_start) > 0.5 else 0
    return f"M {x1:.1f},{y1:.1f} A {r},{r} 0 {large},1 {x2:.1f},{y2:.1f}"


def _needle_coords(fraction: float, r: int = 62, cx: int = 100, cy: int = 96):
    """Needle tip coordinates for given fraction [0,1]."""
    angle = (fraction - 0.5) * math.pi
    return cx + r * math.sin(angle), cy - r * math.cos(angle)


def make_gauge(value, max_val: float, zone_colors: list, label: str,
               sub_label: str = "", tooltip: str = "") -> str:
    """
    Renders an SVG half-circle gauge card.
    zone_colors: list of (threshold, hex_color) tuples up to max_val
    """
    cx, cy, r = 100, 96, 72
    sw = 14  # stroke width

    # Background track
    bg = f'<path d="{_arc_path(0, 1, r, cx, cy)}" fill="none" stroke="#111820" stroke-width="{sw}" stroke-linecap="round"/>'

    # Zone arcs
    zone_paths = []
    prev = 0.0
    for thresh, color in zone_colors:
        f_start = prev / max_val
        f_end   = min(thresh, max_val) / max_val
        if f_end > f_start:
            zone_paths.append(
                f'<path d="{_arc_path(f_start, f_end, r, cx, cy)}" fill="none" stroke="{color}" '
                f'stroke-width="{sw}" stroke-linecap="round" opacity="0.5"/>'
            )
        prev = thresh

    # Active fill up to current value
    frac = max(0.0, min(1.0, (value or 0) / max_val))
    active_color = next(
        (c for t, c in zone_colors if (value or 0) <= t),
        zone_colors[-1][1] if zone_colors else "#39ff14"
    )
    if frac > 0:
        zone_paths.append(
            f'<path d="{_arc_path(0, frac, r, cx, cy)}" fill="none" stroke="{active_color}" '
            f'stroke-width="{sw}" stroke-linecap="round"/>'
        )

    # Needle
    nx, ny = _needle_coords(frac, r - 4, cx, cy)
    needle = (
        f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" '
        f'stroke="#f0f4f8" stroke-width="2.5" stroke-linecap="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="#f0f4f8"/>'
    )

    val_str = f"{value:.1f}" if value is not None else "–"
    tooltip_attr = f'title="{tooltip}"' if tooltip else ""

    return f"""
    <div class="signal-card" {tooltip_attr}>
      <div class="signal-label">{label}</div>
      <svg viewBox="0 0 200 108" class="gauge-svg">
        {bg}
        {''.join(zone_paths)}
        {needle}
      </svg>
      <div class="signal-value">{val_str}</div>
      <div class="signal-zone">{sub_label}</div>
    </div>"""


# ── Expected Move Card ────────────────────────────────────────────────────────

def make_em_card(em: dict, spx: dict) -> str:
    if em.get("pts") is None:
        pts_str  = "–"
        pct_str  = "–"
        range_str = "–"
    else:
        pts_str   = f"± {em['pts']:,} pts"
        pct_str   = f"± {em['pct']}%"
        low_str   = f"{em['low']:,}"
        high_str  = f"{em['high']:,}"
        range_str = f"{low_str} – {high_str}"

    spx_str = f"{spx['value']:,.0f}" if spx.get("value") else "–"

    return f"""
    <div class="signal-card em-card" title="1-day Expected Move: SPX × (VIX / 100) / √252 · Based on previous close">
      <div class="signal-label">Expected Move</div>
      <div class="em-body">
        <div class="em-spx">SPX <span class="em-spx-val">{spx_str}</span></div>
        <div class="em-pts">{pts_str}</div>
        <div class="em-pct">{pct_str}</div>
        <div class="em-range-label">Today's Range</div>
        <div class="em-range">{range_str}</div>
      </div>
    </div>"""


# ── Narrative Section ─────────────────────────────────────────────────────────

def make_narrative(narrative: dict) -> str:
    sections = [
        ("Yesterday",        narrative.get("yesterday", "–")),
        ("Current Sentiment", narrative.get("sentiment", "–")),
        ("Today's Outlook",   narrative.get("outlook", "–")),
    ]
    rows = ""
    for title, text in sections:
        rows += f"""
      <div class="narrative-section">
        <div class="narrative-title">▸ {title}</div>
        <div class="narrative-text">{text}</div>
      </div>"""
    return rows


# ── Full HTML ─────────────────────────────────────────────────────────────────

def build_html(d: dict) -> str:
    vix = d["vix"]
    fng = d["fng"]
    em  = d["em"]
    spx = d["spx"]

    # VIX gauge: 0–40, zones green/yellow/red
    vix_gauge = make_gauge(
        value=vix.get("value"),
        max_val=40,
        zone_colors=[(15, "#39ff14"), (25, "#f59e0b"), (40, "#ef4444")],
        label="VIX",
        sub_label=f"{vix.get('zone', '–')} &nbsp;·&nbsp; {vix.get('delta_str', '–')}",
        tooltip="CBOE Volatility Index · <15 Low  15–25 Elevated  >25 High",
    )

    # F&G gauge: 0–100, zones red/orange/yellow/lightgreen/green
    fng_gauge = make_gauge(
        value=fng.get("value"),
        max_val=100,
        zone_colors=[
            (25,  "#ef4444"),
            (45,  "#f97316"),
            (55,  "#eab308"),
            (75,  "#84cc16"),
            (100, "#39ff14"),
        ],
        label="Fear & Greed",
        sub_label=fng.get("label", "–"),
        tooltip="CNN Fear & Greed Index · 0–25 Extreme Fear  26–45 Fear  46–55 Neutral  56–75 Greed  76–100 Extreme Greed",
    )

    em_card = make_em_card(em, spx)
    narrative_html = make_narrative(d["narrative"])

    vix_delta_color = "#39ff14" if not vix.get("up") else "#ef4444"
    fng_trend = "↑" if fng.get("trend_up") else "↓"
    fng_trend_color = "#39ff14" if fng.get("trend_up") else "#ef4444"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Daily Note – {d['datum']} – LAE Market Services</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #090c11;
      color: #f0f4f8;
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      padding: 28px 24px 48px;
    }}

    /* ── Header ── */
    .header {{
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 28px;
      padding-bottom: 18px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
    }}
    .header-logo {{ display: flex; align-items: center; gap: 10px; }}
    .header-title {{ font-size: 0.65rem; font-weight: 700; color: #7a8899; text-transform: uppercase; letter-spacing: 0.1em; }}
    .header-date  {{ font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; font-weight: 700; color: #f0f4f8; }}
    .header-spacer {{ flex: 1; }}
    .header-tag {{
      font-size: 0.65rem; font-weight: 700; letter-spacing: 0.06em;
      color: #39ff14; background: rgba(57,255,20,0.1); border: 1px solid rgba(57,255,20,0.25);
      padding: 4px 10px; border-radius: 4px; text-transform: uppercase;
    }}

    /* ── Signal cards row ── */
    .signals {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 16px;
      margin-bottom: 20px;
    }}
    .signal-card {{
      background: #0d111a;
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 14px;
      padding: 18px 16px 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: border-color 0.2s, box-shadow 0.2s;
      cursor: default;
    }}
    .signal-card:hover {{
      border-color: rgba(57,255,20,0.2);
      box-shadow: 0 0 20px rgba(57,255,20,0.07);
    }}
    .signal-label {{
      font-size: 0.65rem; font-weight: 700; color: #7a8899;
      text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px;
    }}
    .gauge-svg {{ width: 160px; height: 90px; }}
    .signal-value {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.7rem; font-weight: 700; color: #f0f4f8;
      margin-top: 4px; line-height: 1;
    }}
    .signal-zone {{
      font-size: 0.72rem; font-weight: 600; color: #7a8899;
      margin-top: 6px; letter-spacing: 0.03em;
    }}

    /* ── Expected Move card ── */
    .em-card {{ justify-content: flex-start; align-items: flex-start; padding: 20px 22px; }}
    .em-body {{ width: 100%; margin-top: 10px; display: flex; flex-direction: column; gap: 8px; }}
    .em-spx {{ font-size: 0.72rem; color: #7a8899; }}
    .em-spx-val {{ font-family: 'JetBrains Mono', monospace; color: #f0f4f8; font-weight: 700; }}
    .em-pts {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.7rem; font-weight: 700; color: #39ff14; line-height: 1;
    }}
    .em-pct {{ font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; color: #7a8899; }}
    .em-range-label {{ font-size: 0.62rem; font-weight: 700; color: #7a8899; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 6px; }}
    .em-range {{ font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; color: #f0f4f8; font-weight: 700; }}

    /* ── Narrative ── */
    .narrative {{
      background: #0d111a;
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 14px;
      padding: 24px 26px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .narrative-header {{
      font-size: 0.65rem; font-weight: 700; color: #7a8899;
      text-transform: uppercase; letter-spacing: 0.1em;
      margin-bottom: 4px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255,255,255,0.05);
    }}
    .narrative-section {{ display: flex; flex-direction: column; gap: 5px; }}
    .narrative-title {{
      font-size: 0.72rem; font-weight: 700; color: #39ff14;
      text-transform: uppercase; letter-spacing: 0.06em;
    }}
    .narrative-text {{
      font-size: 0.92rem; color: #c8d0db; line-height: 1.65;
    }}

    /* ── Footer ── */
    .footer {{
      margin-top: 28px;
      padding-top: 16px;
      border-top: 1px solid rgba(255,255,255,0.05);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .footer-brand {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem; color: #7a8899;
    }}
    .footer-brand span {{ color: #39ff14; font-weight: 700; }}
    .footer-note {{ font-size: 0.65rem; color: rgba(122,136,153,0.5); }}
  </style>
</head>
<body>

  <!-- Header -->
  <div class="header">
    <div class="header-logo">
      <svg width="26" height="26" viewBox="0 0 60 60" fill="none">
        <path d="M30,4 L54,17 L54,43 L30,56 L6,43 L6,17 Z" fill="rgba(57,255,20,.08)" stroke="#39ff14" stroke-width="1.5"/>
        <polyline points="16,40 24,28 30,33 40,18" fill="none" stroke="#39ff14" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        <polyline points="40,25 40,18 34,21" fill="none" stroke="#39ff14" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <div>
        <div class="header-title">LAE Market Services</div>
        <div class="header-date">{d['datum']}</div>
      </div>
    </div>
    <div class="header-spacer"></div>
    <div class="header-tag">Pre-Market · Daily Note</div>
  </div>

  <!-- Signal Indicators -->
  <div class="signals">
    {vix_gauge}
    {fng_gauge}
    {em_card}
  </div>

  <!-- AI Narrative -->
  <div class="narrative">
    <div class="narrative-header">Market Narrative</div>
    {narrative_html}
  </div>

  <!-- Footer -->
  <div class="footer">
    <div class="footer-brand"><span>LAE</span> Market Services · Learn. Analyze. Execute.</div>
    <div class="footer-note">Based on previous close · Generated {d['date_iso']}</div>
  </div>

</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\nLAE Daily Note – generating ...\n")
    d = data_fetcher.fetch_all()

    html = build_html(d)

    output_dir = BASE_DIR / "outputs" / "daily-note"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Timestamped archive copy
    archive_path = output_dir / f"Daily_Note_{d['date_iso']}.html"
    archive_path.write_text(html, encoding="utf-8")

    # Fixed "current" file – always overwritten, portal viewer points here
    current_path = output_dir / "Daily_Note_current.html"
    current_path.write_text(html, encoding="utf-8")

    print(f"\n  Report:  {archive_path}")
    print(f"  Current: {current_path}")

    # Dashboard-data JSON update
    dash_json = BASE_DIR / "outputs" / "portal" / "dashboard-data.json"
    new_entry = {
        "type":   "Daily Note",
        "title":  f"Daily Note · {d['datum']}",
        "teaser": f"Pre-market briefing: VIX {d['vix'].get('value', '–')} · F&G {d['fng'].get('value', '–')} ({d['fng'].get('label', '–')})",
        "link":   "./products/daily-note.html",
        "date":   d["date_iso"],
    }
    dash = {}
    if dash_json.exists():
        try:
            dash = json.loads(dash_json.read_text(encoding="utf-8"))
        except Exception:
            pass
    dash["updates"] = [new_entry] + [u for u in dash.get("updates", []) if u.get("type") != "Daily Note"]
    dash_json.write_text(json.dumps(dash, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Dashboard: updated")


if __name__ == "__main__":
    main()
