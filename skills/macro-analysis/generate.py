#!/usr/bin/env python3
"""LAE Macro Analysis – Chart.js Generator
Ausgabe: outputs/macro-analysis/lae-macro-analysis-DATUM.html

Aufruf:
  python skills/macro-analysis/generate.py
  python skills/macro-analysis/generate.py --api-key DEIN_FRED_KEY
"""

import os, sys, json, argparse, math
from pathlib import Path

from data import (
    yahoo, bls_batch, fetch_gdp, fred,
    sig, macro_score, last_val,
    build_calendar_html, ai_interpretation,
    signal_card, kpi_card,
    TODAY, DATE_STR, OUTPUT_DIR,
)

import pandas as pd


# ── Series → JSON für Chart.js ────────────────────────────────────────────────

def _xy(s, fmt="%Y-%m-%d"):
    s = s.dropna()
    return [d.strftime(fmt) for d in s.index], [round(float(v), 4) for v in s.values]

def _snap(s, idx, r=4):
    return [round(float(v), r) if pd.notna(v) else None
            for v in s.reindex(idx, method="ffill")]

def d_inflation(cpi, core_cpi):
    yoy  = cpi.pct_change(12).mul(100).dropna()
    core = core_cpi.pct_change(12).mul(100)
    return {"labels": [d.strftime("%Y-%m") for d in yoy.index],
            "cpi":   [round(float(v), 2) for v in yoy],
            "core":  _snap(core, yoy.index, 2)}

def d_gdp(gdp):
    qmap = {1:"Q1", 4:"Q2", 7:"Q3", 10:"Q4"}
    vals = [round(float(v), 2) for v in gdp.values]
    return {"labels": [f"{qmap.get(ts.month,'?')}'{ts.strftime('%y')}" for ts in gdp.index],
            "values": vals,
            "colors": ["#4da6ff" if v >= 2 else ("#6b8fa8" if v >= 0 else "#ff4d4d") for v in vals]}

def d_yield_curve(tnx, irx):
    spread = (tnx - irx.reindex(tnx.index, method="ffill")).dropna()
    labels, vals = _xy(spread)
    return {"labels": labels, "spread": vals}

def d_yields(tnx, fvx, irx):
    idx = tnx.dropna().index
    return {"labels": [d.strftime("%Y-%m-%d") for d in idx],
            "tnx": _snap(tnx, idx), "fvx": _snap(fvx, idx), "irx": _snap(irx, idx)}

def d_nfp(nfp):
    m    = nfp.diff().dropna().iloc[-24:]
    vals = [round(float(v), 0) for v in m.values]
    return {"labels": [d.strftime("%m/%Y") for d in m.index],
            "values": vals,
            "colors": ["#4da6ff" if v >= 0 else "#ff4d4d" for v in vals],
            "avg":    round(float(m.mean()), 0)}

def d_unemployment(unemp):
    labels, vals = _xy(unemp, "%m/%Y")
    return {"labels": labels, "values": vals}

def d_vix(vix):
    labels, vals = _xy(vix)
    return {"labels": labels, "values": vals}

def d_dxy_gold(dxy, gold):
    idx = dxy.dropna().index
    return {"labels": [d.strftime("%Y-%m-%d") for d in idx],
            "dxy":  _snap(dxy, idx), "gold": _snap(gold, idx)}

def d_oil_copper(oil, copper):
    common = oil.index.intersection(copper.index)
    oil_a  = oil.reindex(common).dropna()
    if oil_a.empty:
        return {"labels": [], "oil": [], "copper": []}
    cop_a = copper.reindex(common)
    oil_n = (oil_a / oil_a.iloc[0] * 100).round(2)
    cop_n = (cop_a / cop_a.iloc[0] * 100).round(2)
    return {"labels": [d.strftime("%Y-%m-%d") for d in oil_n.index],
            "oil":    [float(v) for v in oil_n],
            "copper": _snap(cop_n, oil_n.index)}

def d_sp500(sp):
    if sp.empty:
        return {"labels": [], "sp": [], "ma": []}
    ma200 = sp.rolling(200).mean()
    sp_v  = sp.iloc[-200:]
    ma_v  = ma200.reindex(sp_v.index)
    return {"labels": [d.strftime("%Y-%m-%d") for d in sp_v.index],
            "sp":  [round(float(v), 2) for v in sp_v],
            "ma":  [round(float(v), 2) if pd.notna(v) else None for v in ma_v]}


# ── Gauge SVG ─────────────────────────────────────────────────────────────────

def gauge_html(score: int) -> str:
    col   = "#39ff14" if score >= 60 else ("#ffc93c" if score >= 40 else "#ff4d4d")
    label = "BULLISH"  if score >= 60 else ("NEUTRAL" if score >= 40 else "BEARISH")
    cx, cy, r = 100, 96, 68

    def arc(a0, a1, rv=None):
        rv = rv or r
        sx = cx + rv * math.cos(math.radians(a0))
        sy = cy - rv * math.sin(math.radians(a0))
        ex = cx + rv * math.cos(math.radians(a1))
        ey = cy - rv * math.sin(math.radians(a1))
        la = 1 if abs(a0 - a1) > 180 else 0
        return f"M {sx:.1f},{sy:.1f} A {rv},{rv} 0 {la},1 {ex:.1f},{ey:.1f}"

    sa = 180 - score * 1.8
    end_x = cx + r * math.cos(math.radians(sa))
    end_y = cy - r * math.sin(math.radians(sa))

    ticks = []
    for ts in [0, 25, 50, 75, 100]:
        ta  = 180 - ts * 1.8
        x1  = cx + (r - 6)  * math.cos(math.radians(ta))
        y1  = cy - (r - 6)  * math.sin(math.radians(ta))
        x2  = cx + (r + 4)  * math.cos(math.radians(ta))
        y2  = cy - (r + 4)  * math.sin(math.radians(ta))
        lx  = cx + (r + 17) * math.cos(math.radians(ta))
        ly  = cy - (r + 17) * math.sin(math.radians(ta))
        ticks += [
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="rgba(255,255,255,0.15)" stroke-width="1.5"/>',
            f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="middle" font-size="7" fill="#7a8899" font-family="JetBrains Mono">{ts}</text>',
        ]

    val_arc = (f'<path d="{arc(180, sa)}" stroke="{col}" stroke-width="10" fill="none"'
               f' stroke-linecap="round" style="filter:drop-shadow(0 0 8px {col}66)"/>') if score > 0 else ""
    end_dot = (f'<circle cx="{end_x:.0f}" cy="{end_y:.0f}" r="5" fill="{col}"'
               f' style="filter:drop-shadow(0 0 8px {col})"/>') if score > 0 else ""

    return f"""<div style="padding:20px 12px;text-align:center">
<svg viewBox="0 0 200 122" style="width:100%;max-width:300px;display:block;margin:0 auto">
  <path d="{arc(180,180-63)}"     stroke="rgba(255,77,77,0.22)"   stroke-width="14" fill="none" stroke-linecap="butt"/>
  <path d="{arc(180-63,180-117)}" stroke="rgba(255,201,60,0.18)"  stroke-width="14" fill="none" stroke-linecap="butt"/>
  <path d="{arc(180-117,0)}"      stroke="rgba(57,255,20,0.16)"   stroke-width="14" fill="none" stroke-linecap="butt"/>
  <path d="{arc(180,0)}"          stroke="rgba(255,255,255,0.06)" stroke-width="10" fill="none" stroke-linecap="round"/>
  {val_arc}
  {end_dot}
  {"".join(ticks)}
  <text x="100" y="80" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="32" font-weight="700" fill="{col}">{score}</text>
  <text x="100" y="95" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="7.5" fill="#7a8899" letter-spacing="2">/ 100</text>
</svg>
<div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#7a8899;letter-spacing:3px;text-transform:uppercase;margin-top:2px">MACRO SIGNAL</div>
<div style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:{col};letter-spacing:4px;margin-top:4px">{label}</div>
</div>"""


# ── HTML Template ─────────────────────────────────────────────────────────────
# __PLACEHOLDER__ Syntax: Python-Werte via .replace(), JS {} bleiben unescaped

_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LAE Macro Analysis · __DATE__ · Chart.js</title>
<script>__CHARTJS__</script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#090c11;--bg2:#0d111a;--bg3:#111720;--g:#39ff14;--w:#f0f4f8;--gr:#7a8899;--r:#ff4d4d;--a:#ffc93c;--b:rgba(255,255,255,0.07);--radius:14px}
html{background:#090c11}
body{background:#090c11;color:var(--w);font-family:'Inter',sans-serif;font-size:14px}
.hdr{background:rgba(13,17,26,0.92);border-bottom:1px solid rgba(255,255,255,0.07);backdrop-filter:blur(20px);position:sticky;top:0;z-index:100}
.hdr-i{padding:0 40px;display:flex;align-items:center;justify-content:space-between;height:60px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none}
.logo-txt{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px}
.logo-lae{color:var(--g)}.logo-rest{color:var(--w)}
.logo-claim{font-size:10px;color:var(--gr);letter-spacing:0.05em;font-family:'JetBrains Mono',monospace;margin-top:2px}
.hdr-right{display:flex;align-items:center;gap:16px;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--gr)}
.chip{background:#111720;border:1px solid rgba(255,255,255,0.07);padding:5px 12px;border-radius:8px;color:var(--w)}
.score-pill{background:#111720;border:1px solid rgba(57,255,20,0.25);padding:5px 14px;border-radius:8px;font-weight:700;color:__SC__;box-shadow:0 0 14px rgba(57,255,20,0.08)}
.wrap{padding:28px 40px 32px}
.sec-hdr{display:flex;align-items:center;gap:10px;margin:36px 0 16px;padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,0.06)}
.sec-dot{width:6px;height:6px;border-radius:50%;background:var(--g);box-shadow:0 0 8px var(--g);flex-shrink:0}
.sec-title{font-size:10px;font-weight:700;letter-spacing:0.16em;color:var(--gr);text-transform:uppercase}
.macro-card{background:#0d111a;border:1px solid rgba(57,255,20,0.18);border-radius:var(--radius);box-shadow:0 0 50px rgba(57,255,20,0.05);overflow:hidden}
.macro-top{display:flex;align-items:stretch;border-bottom:1px solid rgba(255,255,255,0.06)}
.gauge-col{flex:0 0 320px;display:flex;align-items:center;justify-content:center}
.divider{flex:0 0 1px;background:rgba(255,255,255,0.06)}
.info-col{flex:1;min-width:0;padding:28px 32px;display:flex;flex-direction:column;justify-content:center;gap:20px}
.text-col{padding:24px 32px}
.text-col-label{font-size:9px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;color:var(--gr);margin-bottom:14px}
.interp{font-size:12px;line-height:1.75;color:var(--gr)}
.interp p{margin-bottom:10px}.interp p:last-child{margin-bottom:0}
.interp strong{color:var(--w);font-weight:600}
.score-headline{font-size:13px;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:var(--gr)}
.score-signal{font-family:'JetBrains Mono',monospace;font-size:42px;font-weight:700;line-height:1;color:__SC__}
.score-num{font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--gr);margin-top:4px}
.score-sub{font-size:11px;color:var(--gr)}
.count-row{display:flex;gap:28px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.06)}
.count-n{font-family:'JetBrains Mono',monospace;font-size:32px;font-weight:700;line-height:1}
.count-l{font-size:9px;letter-spacing:0.12em;color:var(--gr);margin-top:5px}
.bull .count-n{color:var(--g)}.neut .count-n{color:var(--a)}.bear .count-n{color:var(--r)}
.range-btns{display:flex;gap:5px;margin-bottom:10px}
.range-btn{background:#111720;border:1px solid rgba(255,255,255,0.07);border-radius:5px;color:#7a8899;font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:700;padding:3px 9px;cursor:pointer;letter-spacing:.05em;transition:color .15s,border-color .15s}
.range-btn:hover{color:#f0f4f8;border-color:rgba(255,255,255,0.15)}
.range-btn.active{color:#39ff14;border-color:rgba(57,255,20,0.3)}
.ctrl-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;gap:8px}
.ctrl-row .range-btns{margin-bottom:0;flex-shrink:0}
.leg{display:flex;gap:10px;flex-wrap:wrap;flex:1;min-width:0}
.leg-item{display:flex;align-items:center;gap:5px;cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:9px;color:#7a8899;user-select:none;transition:opacity .15s}
.leg-swatch{width:16px;height:2px;border-radius:1px;flex-shrink:0;display:inline-block}
.leg-item.hidden{opacity:0.3}
.sig-grid{display:grid;grid-template-columns:repeat(9,1fr);gap:8px}
.sig-card{background:#0d111a;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:10px 12px;transition:border-color .2s,transform .15s;cursor:default}
.sig-card:hover{transform:translateY(-1px)}
.sig-bullish{border-left:3px solid var(--g)}.sig-bearish{border-left:3px solid var(--r)}.sig-neutral{border-left:3px solid var(--a)}
.sig-label{font-size:9px;color:var(--gr);letter-spacing:0.03em;margin-bottom:6px;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sig-val{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700;margin-bottom:6px}
.sig-badge{display:inline-block;font-size:8px;font-weight:700;letter-spacing:0.1em;padding:2px 6px;border-radius:4px}
.badge-bullish{background:rgba(57,255,20,0.12);color:var(--g)}.badge-bearish{background:rgba(255,77,77,0.12);color:var(--r)}.badge-neutral{background:rgba(255,201,60,0.12);color:var(--a)}
.chart-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.c{background:#0d111a;border:1px solid rgba(255,255,255,0.07);border-radius:var(--radius);overflow:hidden;transition:border-color .2s;padding:20px 20px 16px}
.c:hover{border-color:rgba(255,255,255,0.12)}
.c-title{font-size:10px;font-weight:700;color:var(--w);letter-spacing:0.05em;margin-bottom:16px;text-transform:uppercase}
.cal-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:4px}
.cal-card{display:flex;align-items:center;gap:12px;background:#0d111a;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:12px 16px;flex:1;min-width:180px}
.cal-icon{font-size:1.4rem}.cal-body{flex:1}
.cal-name{font-size:9px;font-weight:600;color:var(--gr);text-transform:uppercase;letter-spacing:.05em}
.cal-date{font-family:'JetBrains Mono',monospace;font-size:.9rem;font-weight:700;color:var(--w);margin-top:3px}
.cal-badge{font-family:'JetBrains Mono',monospace;font-size:.65rem;font-weight:700;padding:3px 8px;border-radius:4px;background:rgba(57,255,20,0.12);color:var(--g);white-space:nowrap}
.cal-card.cal-later .cal-badge{background:rgba(255,255,255,0.06);color:var(--gr)}
.ftr{margin:24px 0 0;padding:20px 40px;border-top:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between;align-items:center;font-size:10px;color:var(--gr);font-family:'JetBrains Mono',monospace}
@media(max-width:1100px){
  .macro-top{flex-direction:column}.gauge-col{flex:none;width:100%}.divider{flex:none;height:1px;width:100%}
  .chart-2{grid-template-columns:1fr}.sig-grid{grid-template-columns:repeat(3,1fr)}
  .wrap{padding:20px 16px 40px}.hdr-i{padding:0 16px}
}
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
      <span class="chip">__DATE__</span>
      <span class="score-pill">__SL__ &nbsp;·&nbsp; __SCORE__/100</span>
    </div>
  </div>
</header>

<div class="wrap">

  <div class="sec-hdr" style="margin-top:0">
    <div class="sec-dot"></div>
    <div class="sec-title">Economic Calendar &middot; Upcoming Dates</div>
  </div>
  <div class="cal-row">__CAL__</div>

  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Macro Score &middot; US Markets Overview</div>
  </div>
  <div class="macro-card">
    <div class="macro-top">
      <div class="gauge-col">__GAUGE__</div>
      <div class="divider"></div>
      <div class="info-col">
        <div>
          <div class="score-headline">US Macro Overview</div>
          <div class="score-signal">__SL__</div>
          <div class="score-num">__SCORE__ / 100</div>
        </div>
        <div class="score-sub">__N_SIG__ Indicators &nbsp;·&nbsp; __DATE__</div>
        <div class="count-row">
          <div class="count-item bull"><div class="count-n">__BULL__</div><div class="count-l">BULLISH</div></div>
          <div class="count-item neut"><div class="count-n">__NEUT__</div><div class="count-l">NEUTRAL</div></div>
          <div class="count-item bear"><div class="count-n">__BEAR__</div><div class="count-l">BEARISH</div></div>
        </div>
      </div>
    </div>
    <div class="text-col">
      <div class="text-col-label">Macro Assessment</div>
      <div class="interp">__INTERP__</div>
    </div>
  </div>

  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Key Metrics</div>
  </div>
  <div class="sig-grid">__SIGS__</div>

  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Inflation &amp; Growth</div>
  </div>
  <div class="chart-2">
    <div class="c"><div class="c-title">Inflation &middot; CPI &amp; Core CPI YoY</div><div class="ctrl-row"><div class="leg" id="lg_infl"></div><div class="range-btns" id="rb_infl"><button class="range-btn" data-m="6">6M</button><button class="range-btn" data-m="12">1Y</button><button class="range-btn active" data-m="0">All</button></div></div><div style="position:relative;height:260px"><canvas id="ch_infl"></canvas></div></div>
    <div class="c"><div class="c-title">Real GDP &middot; QoQ annualized (%)</div><div style="position:relative;height:260px"><canvas id="ch_gdp"></canvas></div></div>
  </div>

  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Fed &amp; Rates</div>
  </div>
  <div class="chart-2">
    <div class="c"><div class="c-title">Yield Curve &middot; 10Y - 3M</div><div class="range-btns" id="rb_yc"><button class="range-btn" data-m="6">6M</button><button class="range-btn" data-m="12">1Y</button><button class="range-btn active" data-m="0">All</button></div><div style="position:relative;height:260px"><canvas id="ch_yc"></canvas></div></div>
    <div class="c"><div class="c-title">Treasury Yields</div><div class="ctrl-row"><div class="leg" id="lg_yields"></div><div class="range-btns" id="rb_yields"><button class="range-btn" data-m="6">6M</button><button class="range-btn" data-m="12">1Y</button><button class="range-btn active" data-m="0">All</button></div></div><div style="position:relative;height:260px"><canvas id="ch_yields"></canvas></div></div>
  </div>

  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Labor Market</div>
  </div>
  <div class="chart-2">
    <div class="c"><div class="c-title">Non-Farm Payrolls &middot; Monthly Change</div><div style="position:relative;height:260px"><canvas id="ch_nfp"></canvas></div></div>
    <div class="c"><div class="c-title">Unemployment Rate</div><div style="position:relative;height:260px"><canvas id="ch_unemp"></canvas></div></div>
  </div>

  <div class="sec-hdr">
    <div class="sec-dot"></div>
    <div class="sec-title">Market Structure &amp; Sentiment</div>
  </div>
  <div class="chart-2">
    <div class="c"><div class="c-title">S&amp;P 500 &middot; 200-Day MA</div><div class="ctrl-row"><div class="leg" id="lg_sp"></div><div class="range-btns" id="rb_sp"><button class="range-btn" data-m="6">6M</button><button class="range-btn" data-m="12">1Y</button><button class="range-btn active" data-m="0">All</button></div></div><div style="position:relative;height:260px"><canvas id="ch_sp"></canvas></div></div>
    <div class="c"><div class="c-title">VIX &middot; Volatility Index</div><div class="range-btns" id="rb_vix"><button class="range-btn" data-m="6">6M</button><button class="range-btn" data-m="12">1Y</button><button class="range-btn active" data-m="0">All</button></div><div style="position:relative;height:260px"><canvas id="ch_vix"></canvas></div></div>
  </div>
  <div class="chart-2" style="margin-top:14px">
    <div class="c"><div class="c-title">DXY &middot; Gold</div><div class="ctrl-row"><div class="leg" id="lg_dg"></div><div class="range-btns" id="rb_dg"><button class="range-btn" data-m="6">6M</button><button class="range-btn" data-m="12">1Y</button><button class="range-btn active" data-m="0">All</button></div></div><div style="position:relative;height:260px"><canvas id="ch_dg"></canvas></div></div>
    <div class="c"><div class="c-title">WTI Crude &middot; Copper &middot; Indexed (Base 100)</div><div class="ctrl-row"><div class="leg" id="lg_oc"></div><div class="range-btns" id="rb_oc"><button class="range-btn" data-m="6">6M</button><button class="range-btn" data-m="12">1Y</button><button class="range-btn active" data-m="0">All</button></div></div><div style="position:relative;height:260px"><canvas id="ch_oc"></canvas></div></div>
  </div>

</div>

<footer class="ftr">
  <span>Sources: Yahoo Finance &middot; BLS &middot; FRED (optional)</span>
  <span>LAE Market Services &middot; __DATE__</span>
</footer>

<script>
// ── Chart data ────────────────────────────────────────────────────────────────
__JS_DATA__

// ── Shared config ─────────────────────────────────────────────────────────────
const MONO = "'JetBrains Mono', monospace";
const tt = {
  backgroundColor: '#0d111a',
  borderColor: 'rgba(57,255,20,.25)',
  borderWidth: 1,
  titleColor: '#39ff14',
  bodyColor: '#f0f4f8',
  padding: 10,
  displayColors: true,
  boxWidth: 20, boxHeight: 2,
  titleFont: {family: MONO, size: 11},
  bodyFont:  {family: MONO, size: 10},
  filter: function(item) { return !item.dataset.refLine; }
};
const tFont  = {family: MONO, size: 9, color: '#7a8899'};
const gColor = 'rgba(255,255,255,0.03)';
const bColor = 'rgba(255,255,255,0.08)';

function ref(n, val, color, dash) {
  return {type: 'line', label: n, refLine: true, data: Array(10000).fill(val),
    borderColor: color || 'rgba(255,255,255,0.15)',
    borderDash: dash || [5,4], borderWidth: 1,
    pointRadius: 0, fill: false, tension: 0};
}

// ── Current-value annotation plugin ──────────────────────────────────────────
function cvPlugin(entries) {
  return {
    afterDraw(chart) {
      const {ctx, chartArea:{right,top,bottom}} = chart;
      function lastVal(arr) {
        for (let i = arr.length-1; i >= 0; i--) {
          if (arr[i] !== null && arr[i] !== undefined && !isNaN(arr[i])) return arr[i];
        }
        return null;
      }
      entries.forEach(({getData, col, fmt, axisId}) => {
        const v = lastVal(getData(chart));
        if (v === null) return;
        const scale = chart.scales[axisId||'y'];
        if (!scale) return;
        const yp = scale.getPixelForValue(v);
        if (yp < top || yp > bottom) return;
        ctx.save();
        ctx.fillStyle = col;
        ctx.font = "700 9px 'JetBrains Mono', monospace";
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(fmt(v), right + 6, yp);
        ctx.restore();
      });
    }
  };
}

// ── Range selector ────────────────────────────────────────────────────────────
const _rd = {};
function setRange(chartId, months) {
  const s = _rd[chartId]; if (!s) return;
  const labelLen = s.full.labels[0].length;
  let si = 0;
  if (months > 0) {
    const c = new Date(); c.setMonth(c.getMonth() - months);
    const cs = c.toISOString().slice(0, labelLen);
    si = s.full.labels.findIndex(l => l >= cs); if (si < 0) si = 0;
  }
  s.chart.data.labels = s.full.labels.slice(si);
  s.chart.data.datasets.forEach((ds, i) => {
    if (ds.refLine) return;
    const key = s.keys[i];
    if (key !== undefined && s.full[key]) ds.data = s.full[key].slice(si);
  });
  s.chart.update('none');
}
document.addEventListener('click', e => {
  const btn = e.target.closest('.range-btn'); if (!btn) return;
  const container = btn.closest('.range-btns'); if (!container) return;
  const chartId = container.id.replace('rb_', 'ch_');
  container.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  setRange(chartId, parseInt(btn.dataset.m));
});
function xCfg(max) {
  return {grid: {display:false}, border: {color: bColor},
          ticks: {font: tFont, maxTicksLimit: max||8, maxRotation: 0}};
}
function xCfgDate(max) {
  const _mn = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return {grid:{display:false}, border:{color:bColor},
          ticks:{font:tFont, maxRotation:0, maxTicksLimit:max||6,
                 callback:function(val){
                   const s=this.getLabelForValue(val); if(!s) return '';
                   const p=s.split('-'); if(p.length<2) return s;
                   return _mn[+p[1]-1]+" '"+p[0].slice(2);
                 }}};
}
function yCfg(suf, extra) {
  return {grid: {color: gColor}, border: {color: bColor},
          ticks: {font: tFont, callback: v => v+(suf||''), maxTicksLimit:6}, ...(extra||{})};
}
function buildLeg(chartId, chart) {
  const el = document.getElementById(chartId.replace('ch_','lg_'));
  if (!el) return;
  el.innerHTML = '';
  chart.data.datasets.forEach((ds, i) => {
    if (ds.refLine) return;
    const hidden = !chart.isDatasetVisible(i);
    const it = document.createElement('div');
    it.className = 'leg-item' + (hidden ? ' hidden' : '');
    it.dataset.chart = chartId; it.dataset.idx = i;
    const sw = document.createElement('span');
    sw.className = 'leg-swatch';
    sw.style.background = typeof ds.borderColor === 'string' ? ds.borderColor : '#7a8899';
    const lb = document.createElement('span');
    lb.textContent = ds.label;
    it.append(sw, lb); el.append(it);
  });
}
document.addEventListener('click', e => {
  const it = e.target.closest('.leg-item'); if (!it) return;
  const chartId = it.dataset.chart;
  const s = _rd[chartId]; if (!s) return;
  const meta = s.chart.getDatasetMeta(parseInt(it.dataset.idx));
  meta.hidden = !meta.hidden;
  s.chart.update();
  buildLeg(chartId, s.chart);
});

// ── Inflation ─────────────────────────────────────────────────────────────────
const ch_infl = new Chart(document.getElementById('ch_infl'), {
  type: 'line',
  data: {
    labels: CD_INFL.labels,
    datasets: [
      {label:'CPI YoY',  data:CD_INFL.cpi,  borderColor:'#f0f4f8', borderWidth:2, tension:0.38, fill:false, pointRadius:0, pointHoverRadius:5},
      {label:'Core CPI', data:CD_INFL.core, borderColor:'#ffc93c', borderDash:[6,3], borderWidth:2, tension:0.38, fill:false, pointRadius:0, pointHoverRadius:5},
      ref('Fed Target 2%', 2, 'rgba(57,255,20,0.5)')
    ]
  },
  options: {
    responsive:true, interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false}, tooltip:{...tt, callbacks:{label:ctx => !ctx.dataset.refLine ? ' '+ctx.dataset.label+': '+ctx.parsed.y.toFixed(1)+'%' : null}}},
    scales:{x:xCfg(8), y:yCfg('%')},
    layout:{padding:{right:52, left:10}}
  },
  plugins:[
    cvPlugin([
      {getData:c=>c.data.datasets[0].data, col:'#f0f4f8', fmt:v=>v.toFixed(1)+'%'},
      {getData:c=>c.data.datasets[1].data, col:'#ffc93c', fmt:v=>v.toFixed(1)+'%'}
    ]),
    {afterDraw(chart) {
      const {ctx, chartArea:{right,top,bottom}, scales:{y}} = chart;
      const yp = y.getPixelForValue(2);
      if (yp < top || yp > bottom) return;
      ctx.save();
      ctx.fillStyle = 'rgba(57,255,20,0.65)';
      ctx.font = "700 9px 'JetBrains Mono', monospace";
      ctx.textAlign = 'right'; ctx.textBaseline = 'bottom';
      ctx.fillText('Fed Target 2%', right - 4, yp - 3);
      ctx.restore();
    }}
  ]
});
_rd['ch_infl'] = {chart:ch_infl, full:CD_INFL, keys:{0:'cpi',1:'core'}};
buildLeg('ch_infl', ch_infl);

// ── GDP ───────────────────────────────────────────────────────────────────────
new Chart(document.getElementById('ch_gdp'), {
  type: 'bar',
  data: {
    labels: CD_GDP.labels,
    datasets: [
      {label:'Real GDP QoQ', data:CD_GDP.values,
       backgroundColor: CD_GDP.colors.map(c=>c+'bb'),
       borderColor: CD_GDP.colors, borderWidth:1, borderRadius:3},
      {type:'line', label:'Ø-Trend 2%', refLine:true, data:Array(CD_GDP.labels.length).fill(2),
       borderColor:'rgba(77,166,255,0.55)', borderDash:[5,4], borderWidth:1.2,
       pointRadius:0, fill:false, tension:0}
    ]
  },
  options: {
    responsive:true, interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},
      tooltip:{...tt, callbacks:{label:ctx=>ctx.dataset.refLine?null:' GDP: '+(ctx.parsed.y>=0?'+':'')+ctx.parsed.y.toFixed(1)+'%'}}},
    scales:{x:xCfg(12), y:yCfg('%')}
  },
  plugins:[{
    afterDraw(chart) {
      const {ctx, chartArea:{left,top}, scales:{y}} = chart;
      const yp = y.getPixelForValue(2);
      ctx.save();
      ctx.fillStyle = 'rgba(77,166,255,0.7)';
      ctx.font = "9px 'JetBrains Mono', monospace";
      ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
      ctx.fillText('Ø-Trend 2%', left + 4, yp - 3);
      ctx.restore();
    }
  }]
});

// ── Yield Curve ───────────────────────────────────────────────────────────────
const ch_yc = new Chart(document.getElementById('ch_yc'), {
  type: 'line',
  data: {
    labels: CD_YC.labels,
    datasets: [{label:'10Y - 3M', data:CD_YC.spread,
      borderColor:'#39ff14', borderWidth:2, tension:0.38, pointRadius:0, pointHoverRadius:5,
      fill:{target:'origin', above:'rgba(57,255,20,0.07)', below:'rgba(255,77,77,0.10)'}}]
  },
  options: {
    responsive:true, interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},
      tooltip:{...tt, callbacks:{label:ctx=>' Spread: '+(ctx.parsed.y>=0?'+':'')+ctx.parsed.y.toFixed(2)+'%'}}},
    scales:{x:xCfgDate(6), y:yCfg('%')},
    layout:{padding:{right:52, left:10}}
  },
  plugins:[cvPlugin([
    {getData:c=>c.data.datasets[0].data, col:'#39ff14', fmt:v=>(v>=0?'+':'')+v.toFixed(2)+'%'}
  ])]
});
_rd['ch_yc'] = {chart:ch_yc, full:CD_YC, keys:{0:'spread'}};

// ── Treasury Yields ───────────────────────────────────────────────────────────
const ch_yields = new Chart(document.getElementById('ch_yields'), {
  type: 'line',
  data: {
    labels: CD_YIELDS.labels,
    datasets: [
      {label:'3M T-Bill', data:CD_YIELDS.irx, borderColor:'#7a8899', borderWidth:1.5, tension:0.3, fill:false, pointRadius:0, pointHoverRadius:4},
      {label:'5Y',        data:CD_YIELDS.fvx, borderColor:'#38bdf8', borderWidth:1.8, tension:0.3, fill:false, pointRadius:0, pointHoverRadius:4},
      {label:'10Y',       data:CD_YIELDS.tnx, borderColor:'#c084fc', borderWidth:1.8, tension:0.3, fill:false, pointRadius:0, pointHoverRadius:4}
    ]
  },
  options: {
    responsive:true, interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},
      tooltip:{...tt, callbacks:{label:ctx=>' '+ctx.dataset.label+': '+ctx.parsed.y.toFixed(2)+'%'}}},
    scales:{x:xCfgDate(6), y:yCfg('%')},
    layout:{padding:{right:52, left:10}}
  },
  plugins:[cvPlugin([
    {getData:c=>c.data.datasets[0].data, col:'#7a8899', fmt:v=>v.toFixed(2)+'%'},
    {getData:c=>c.data.datasets[1].data, col:'#38bdf8', fmt:v=>v.toFixed(2)+'%'},
    {getData:c=>c.data.datasets[2].data, col:'#c084fc', fmt:v=>v.toFixed(2)+'%'}
  ])]
});
_rd['ch_yields'] = {chart:ch_yields, full:CD_YIELDS, keys:{0:'irx',1:'fvx',2:'tnx'}};
buildLeg('ch_yields', ch_yields);

// ── NFP ───────────────────────────────────────────────────────────────────────
(function(){
  const avg = CD_NFP.avg;
  new Chart(document.getElementById('ch_nfp'), {
    type: 'bar',
    data: {
      labels: CD_NFP.labels,
      datasets: [
        {label:'NFP', data:CD_NFP.values,
         backgroundColor:CD_NFP.colors.map(c=>c+'aa'),
         borderColor:CD_NFP.colors, borderWidth:1, borderRadius:2},
        ref('Ø '+avg.toLocaleString()+'k', avg, 'rgba(255,201,60,0.7)')
      ]
    },
    options: {
      responsive:true, interaction:{mode:'index',intersect:false},
      plugins:{legend:{display:false},
        tooltip:{...tt, callbacks:{label:ctx=>!ctx.dataset.refLine?' NFP: '+(ctx.parsed.y>=0?'+':'')+ctx.parsed.y.toLocaleString()+'k':null}}},
      scales:{x:xCfg(8), y:yCfg('k')},
      layout:{padding:{right:80, left:10}}
    },
    plugins:[{afterDraw(chart) {
      const {ctx, chartArea:{right,top,bottom}, scales:{y}} = chart;
      const yp = y.getPixelForValue(avg);
      if (yp < top || yp > bottom) return;
      ctx.save();
      ctx.fillStyle = 'rgba(255,201,60,0.8)';
      ctx.font = "700 9px 'JetBrains Mono', monospace";
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillText('Ø '+(avg>=0?'+':'')+Math.round(avg).toLocaleString()+'k', right+4, yp);
      ctx.restore();
    }}]
  });
})();

// ── Unemployment ──────────────────────────────────────────────────────────────
(function(){
  const ctx = document.getElementById('ch_unemp');
  const c   = ctx.getContext('2d');
  const g   = c.createLinearGradient(0,0,0,260);
  g.addColorStop(0,'rgba(255,201,60,0.14)');
  g.addColorStop(1,'rgba(255,201,60,0.01)');
  const mn = Math.min(...CD_UNEMP.values.filter(v=>v!==null));
  new Chart(ctx, {
    type:'line',
    data:{labels:CD_UNEMP.labels, datasets:[
      {label:'Unemployment Rate', data:CD_UNEMP.values,
       borderColor:'#ffc93c', borderWidth:2, tension:0.38, fill:true, backgroundColor:g,
       pointRadius:0, pointHoverRadius:5}
    ]},
    options:{
      responsive:true, interaction:{mode:'index',intersect:false},
      plugins:{legend:{display:false},
        tooltip:{...tt, callbacks:{label:ctx=>' Unemployment: '+ctx.parsed.y.toFixed(1)+'%'}}},
      scales:{x:xCfg(8), y:yCfg('%',{min:Math.max(0,mn-0.5)})},
      layout:{padding:{right:52, left:10}}
    },
    plugins:[cvPlugin([
      {getData:c=>c.data.datasets[0].data, col:'#ffc93c', fmt:v=>v.toFixed(1)+'%'}
    ])]
  });
})();

// ── S&P 500 vs 200-Day MA ─────────────────────────────────────────────────────
const ch_sp = new Chart(document.getElementById('ch_sp'), {
  type:'line',
  data:{labels:CD_SP.labels, datasets:[
    {label:'200-Day MA', data:CD_SP.ma,
     borderColor:'#7a8899', borderDash:[5,4], borderWidth:1.2,
     tension:0.3, fill:false, pointRadius:0},
    {label:'S&P 500', data:CD_SP.sp,
     borderColor:'#39ff14', borderWidth:1.8, tension:0.3, pointRadius:0, pointHoverRadius:5,
     fill:{target:'-1', above:'rgba(57,255,20,0.10)', below:'rgba(255,77,77,0.10)'}}
  ]},
  options:{
    responsive:true, interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},
      tooltip:{...tt, callbacks:{label:ctx=>' '+ctx.dataset.label+': $'+ctx.parsed.y.toLocaleString()}}},
    scales:{
      x:xCfgDate(6),
      y:{grid:{color:gColor}, border:{color:bColor},
         ticks:{font:tFont, callback:v=>'$'+v.toLocaleString(), maxTicksLimit:6}}
    },
    layout:{padding:{right:65, left:10}}
  },
  plugins:[cvPlugin([
    {getData:c=>c.data.datasets[1].data, col:'#39ff14', fmt:v=>'$'+Math.round(v).toLocaleString()}
  ])]
});
_rd['ch_sp'] = {chart:ch_sp, full:CD_SP, keys:{0:'ma',1:'sp'}};
buildLeg('ch_sp', ch_sp);

// ── VIX ───────────────────────────────────────────────────────────────────────
(function(){
  const ctx = document.getElementById('ch_vix');
  const c   = ctx.getContext('2d');
  const g   = c.createLinearGradient(0,0,0,260);
  g.addColorStop(0,'rgba(255,255,255,0.07)');
  g.addColorStop(1,'rgba(255,255,255,0.01)');
  const ch_vix = new Chart(ctx, {
    type:'line',
    data:{labels:CD_VIX.labels, datasets:[
      {label:'VIX', data:CD_VIX.values,
       borderColor:'#f0f4f8', borderWidth:1.8, tension:0.3, fill:true, backgroundColor:g,
       pointRadius:0, pointHoverRadius:4},
      ref('15 – Low Vol', 15, 'rgba(57,255,20,0.45)'),
      ref('25 – Fear',    25, 'rgba(255,77,77,0.45)')
    ]},
    options:{
      responsive:true, interaction:{mode:'index',intersect:false},
      plugins:{legend:{display:false},
        tooltip:{...tt, callbacks:{label:ctx=>!ctx.dataset.refLine?' VIX: '+ctx.parsed.y.toFixed(1):null}}},
      scales:{x:xCfgDate(6), y:yCfg('',{min:0,max:60})},
      layout:{padding:{right:48, left:10}}
    },
    plugins:[
      {
        beforeDraw(chart) {
          const {ctx:c2, chartArea:{left,right,top,bottom}, scales:{y}} = chart;
          const zones = [
            {lo:0,  hi:15,  col:'rgba(57,255,20,0.04)'},
            {lo:15, hi:25,  col:'rgba(255,201,60,0.04)'},
            {lo:25, hi:60,  col:'rgba(255,77,77,0.05)'}
          ];
          zones.forEach(({lo,hi,col}) => {
            const y1 = Math.min(y.getPixelForValue(hi), bottom);
            const y2 = Math.max(y.getPixelForValue(lo), top);
            c2.save(); c2.fillStyle = col;
            c2.fillRect(left, y1, right-left, y2-y1);
            c2.restore();
          });
        }
      },
      cvPlugin([{getData:c=>c.data.datasets[0].data, col:'#f0f4f8', fmt:v=>v.toFixed(1)}])
    ]
  });
  _rd['ch_vix'] = {chart:ch_vix, full:CD_VIX, keys:{0:'values'}};
})();

// ── DXY & Gold ────────────────────────────────────────────────────────────────
const ch_dg = new Chart(document.getElementById('ch_dg'), {
  type:'line',
  data:{labels:CD_DG.labels, datasets:[
    {label:'DXY',  data:CD_DG.dxy,  borderColor:'#818cf8', borderWidth:1.8, tension:0.3, fill:false, pointRadius:0, pointHoverRadius:4, yAxisID:'y'},
    {label:'Gold', data:CD_DG.gold, borderColor:'#fbbf24', borderWidth:1.8, tension:0.3, fill:false, pointRadius:0, pointHoverRadius:4, yAxisID:'y2'}
  ]},
  options:{
    responsive:true, interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},
      tooltip:{...tt, callbacks:{label:ctx=>ctx.dataset.label==='Gold'?' Gold: $'+ctx.parsed.y.toLocaleString():' DXY: '+ctx.parsed.y.toFixed(1)}}},
    scales:{
      x: xCfgDate(6),
      y:  {grid:{color:gColor}, border:{color:bColor}, position:'left',  ticks:{font:tFont, maxTicksLimit:6}},
      y2: {grid:{drawOnChartArea:false}, border:{color:bColor}, position:'right', ticks:{font:tFont, callback:v=>'$'+v.toLocaleString(), maxTicksLimit:6}}
    },
    layout:{padding:{left:10}}
  }
});
_rd['ch_dg'] = {chart:ch_dg, full:CD_DG, keys:{0:'dxy',1:'gold'}};
buildLeg('ch_dg', ch_dg);

// ── Oil & Copper (Indexed) ────────────────────────────────────────────────────
const ch_oc = new Chart(document.getElementById('ch_oc'), {
  type:'line',
  data:{labels:CD_OC.labels, datasets:[
    {label:'WTI Crude', data:CD_OC.oil,    borderColor:'#ff8c42', borderWidth:1.8, tension:0.3, fill:false, pointRadius:0, pointHoverRadius:4},
    {label:'Copper',    data:CD_OC.copper, borderColor:'#00c4b4', borderWidth:1.8, tension:0.3, fill:false, pointRadius:0, pointHoverRadius:4},
    ref('Base 100', 100, 'rgba(255,255,255,0.18)')
  ]},
  options:{
    responsive:true, interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},
      tooltip:{...tt, callbacks:{label:ctx=>{
        if(ctx.dataset.refLine) return null;
        const pct=(ctx.parsed.y-100).toFixed(1);
        return ' '+ctx.dataset.label+': '+ctx.parsed.y.toFixed(1)+' pts ('+(pct>=0?'+':'')+pct+'%)';
      }}}},
    scales:{x:xCfgDate(6), y:yCfg(' pts')},
    layout:{padding:{left:10}}
  }
});
_rd['ch_oc'] = {chart:ch_oc, full:CD_OC, keys:{0:'oil',1:'copper'}};
buildLeg('ch_oc', ch_oc);

window.addEventListener('load', function(){
  var h = document.documentElement.scrollHeight || document.body.scrollHeight;
  window.parent && window.parent.postMessage({frameHeight: h}, '*');
});
</script>
</body></html>"""


def build_chartjs(score, signals, data_dict, cdata):
    sc   = "#39ff14" if score >= 60 else ("#ffc93c" if score >= 40 else "#ff4d4d")
    sl   = "BULLISH" if score >= 60 else ("NEUTRAL" if score >= 40 else "BEARISH")
    bull = sum(1 for s in signals if s["signal"] == "bullish")
    neut = sum(1 for s in signals if s["signal"] == "neutral")
    bear = sum(1 for s in signals if s["signal"] == "bearish")

    interp = ai_interpretation(signals, score)
    sigs   = "".join(signal_card(s) for s in signals)
    cal    = build_calendar_html()
    gauge  = gauge_html(score)

    js_data = "\n".join([
        f"const CD_INFL   = {json.dumps(cdata['inflation'])};",
        f"const CD_GDP    = {json.dumps(cdata['gdp'])};",
        f"const CD_YC     = {json.dumps(cdata['yield_curve'])};",
        f"const CD_YIELDS = {json.dumps(cdata['yields'])};",
        f"const CD_NFP    = {json.dumps(cdata['nfp'])};",
        f"const CD_UNEMP  = {json.dumps(cdata['unemployment'])};",
        f"const CD_SP     = {json.dumps(cdata['sp500'])};",
        f"const CD_VIX    = {json.dumps(cdata['vix'])};",
        f"const CD_DG     = {json.dumps(cdata['dxy_gold'])};",
        f"const CD_OC     = {json.dumps(cdata['oil_copper'])};",
    ])

    chartjs_file = Path(__file__).parent / "_chartjs.min.js"
    chartjs_code = chartjs_file.read_text(encoding="utf-8") if chartjs_file.exists() else "/* Chart.js missing */"

    return (_HTML
        .replace("__CHARTJS__",  chartjs_code)
        .replace("__DATE__",    DATE_STR)
        .replace("__SC__",      sc)
        .replace("__SL__",      sl)
        .replace("__SCORE__",   str(score))
        .replace("__N_SIG__",   str(len(signals)))
        .replace("__BULL__",    str(bull))
        .replace("__NEUT__",    str(neut))
        .replace("__BEAR__",    str(bear))
        .replace("__CAL__",     cal)
        .replace("__GAUGE__",   gauge)
        .replace("__INTERP__",  interp)
        .replace("__SIGS__",    sigs)
        .replace("__JS_DATA__", js_data)
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key", default=os.environ.get("FRED_API_KEY", ""))
    args = ap.parse_args()

    print(f"LAE Macro Analysis (Chart.js) – {DATE_STR}")
    print("Lade Daten...\n")

    print("  [Yahoo] Treasury Yields...")
    tnx = yahoo("^TNX", "2y")
    fvx = yahoo("^FVX", "2y")
    irx = yahoo("^IRX", "2y")

    print("  [BLS]   CPI / Unemployment / NFP...")
    bls_data = bls_batch(["CUUR0000SA0", "CUUR0000SA0L1E", "LNS14000000", "CES0000000001"])
    cpi      = bls_data["CUUR0000SA0"]
    core_cpi = bls_data["CUUR0000SA0L1E"]
    unemp    = bls_data["LNS14000000"]
    nfp      = bls_data["CES0000000001"]

    print("  [GDP]   Real GDP...")
    gdp = fetch_gdp(args.api_key)

    print("  [Yahoo] Marktdaten...")
    vix    = yahoo("^VIX",     "2y")
    dxy    = yahoo("DX-Y.NYB", "2y")
    gold   = yahoo("GC=F",     "2y")
    oil    = yahoo("CL=F",     "2y")
    copper = yahoo("HG=F",     "2y")
    sp     = yahoo("^GSPC",    "2y")

    print("\n  Berechne Signale...")
    signals = []

    if not cpi.empty and len(cpi) >= 13:
        signals.append(sig("CPI YoY", float(cpi.pct_change(12).dropna().iloc[-1]) * 100,
            lambda v: v <= 2.5, lambda v: v > 3.5))
    if not core_cpi.empty and len(core_cpi) >= 13:
        signals.append(sig("Core CPI YoY", float(core_cpi.pct_change(12).dropna().iloc[-1]) * 100,
            lambda v: v <= 2.5, lambda v: v > 3.5))
    if not gdp.empty:
        signals.append(sig("Real GDP QoQ", float(gdp.dropna().iloc[-1]),
            lambda v: v >= 2.5, lambda v: v < 0))
    if not tnx.empty and not irx.empty:
        spread = float(tnx.dropna().iloc[-1]) - float(irx.dropna().iloc[-1])
        signals.append(sig("Yield Curve 10Y-3M", spread,
            lambda v: v > 0.05, lambda v: v < -0.15))
    if not tnx.empty:
        signals.append(sig("10Y Yield", float(tnx.dropna().iloc[-1]),
            lambda v: v < 4.0, lambda v: v > 4.8))
    if not unemp.empty:
        signals.append(sig("Unemployment Rate", float(unemp.dropna().iloc[-1]),
            lambda v: v <= 4.2, lambda v: v > 5.0))
    if not nfp.empty:
        signals.append(sig("NFP Monthly Change", float(nfp.diff().dropna().iloc[-1]),
            lambda v: v > 150, lambda v: v < 0))
    if not vix.empty:
        signals.append(sig("VIX", float(vix.dropna().iloc[-1]),
            lambda v: v <= 15, lambda v: v > 25))
    if not dxy.empty:
        signals.append(sig("DXY", float(dxy.dropna().iloc[-1]),
            lambda v: v <= 100, lambda v: v > 107))

    score = macro_score(signals)
    print(f"  Score: {score}/100 | {len(signals)} Indikatoren")

    print("\n  Bereite Chart-Daten vor...")
    cdata = {
        "inflation":    d_inflation(cpi, core_cpi),
        "gdp":          d_gdp(gdp),
        "yield_curve":  d_yield_curve(tnx, irx),
        "yields":       d_yields(tnx, fvx, irx),
        "nfp":          d_nfp(nfp),
        "unemployment": d_unemployment(unemp),
        "sp500":        d_sp500(sp),
        "vix":          d_vix(vix),
        "dxy_gold":     d_dxy_gold(dxy, gold),
        "oil_copper":   d_oil_copper(oil, copper),
    }
    data_dict = dict(tnx=tnx, irx=irx, cpi=cpi, core_cpi=core_cpi,
                     unemp=unemp, vix=vix, dxy=dxy, gold=gold, sp=sp)

    print("  Baue HTML...")
    html = build_chartjs(score, signals, data_dict, cdata)

    filename = f"lae-macro-analysis-{DATE_STR}.html"
    out = OUTPUT_DIR / filename
    out.write_text(html, encoding="utf-8")
    print(f"\nFertig: {out}")

    # ── Portal-Archiv aktualisieren ───────────────────────────────────────────
    from pathlib import Path as _Path
    base_dir    = _Path(__file__).parents[2]
    portal_path = base_dir / "outputs" / "portal" / "products" / "macro-analysis.html"
    if portal_path.exists():
        portal_html = portal_path.read_text(encoding="utf-8")
        rel_src  = f"../../macro-analysis/{filename}"
        label    = TODAY.strftime("%b %d, %Y")
        new_item = f'              <option value="{rel_src}">{label}</option>'
        marker   = "              <!-- ARCHIV-START -->"
        if rel_src not in portal_html:
            portal_html = portal_html.replace(marker, marker + "\n" + new_item)
            portal_path.write_text(portal_html, encoding="utf-8")
            print(f"  Portal:  aktualisiert ({label})")
        else:
            print(f"  Portal:  Eintrag bereits vorhanden")

    # ── Dashboard-Data aktualisieren ──────────────────────────────────────────
    dash_json = base_dir / "outputs" / "portal" / "dashboard-data.json"
    score_label = "BULLISH" if score >= 60 else ("NEUTRAL" if score >= 40 else "BEARISH")
    new_entry = {
        "type":   "Macro Analysis",
        "title":  f"Macro Analysis · {label}",
        "teaser": f"US macro score at {score}/100 – {score_label}. Full dashboard with interactive charts.",
        "link":   "./products/macro-analysis.html",
        "date":   DATE_STR,
    }
    dash = {}
    if dash_json.exists():
        try: dash = json.loads(dash_json.read_text(encoding="utf-8"))
        except Exception: pass
    dash["updates"] = [new_entry] + [u for u in dash.get("updates", []) if u.get("type") != "Macro Analysis"]
    dash_json.write_text(json.dumps(dash, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Dashboard: aktualisiert")


if __name__ == "__main__":
    main()
