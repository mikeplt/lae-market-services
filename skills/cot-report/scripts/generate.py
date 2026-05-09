"""
LAE Market Services – COT Report Generator
TFF Futures Only · S&P 500 E-Mini · Visueller Report für Daytrader
"""

import csv
import io
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path
import urllib.request

# ── Konfiguration ─────────────────────────────────────────────────────────────
MARKET_NAME   = "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"
URL_FUT       = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
OUTPUT_DIR    = Path(__file__).parents[3] / "outputs" / "cot-report"
REFERENCE_DIR = Path(__file__).parents[3] / "reference"
WEEKS         = 52

# ── Download & Parse ──────────────────────────────────────────────────────────

def fetch(url: str) -> bytes | None:
    print(f"  Loading {url} ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LAE-COT/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except Exception as e:
        print(f"  Error: {e}")
        return None

def local(year: int) -> bytes | None:
    for name in [f"fut_fin_txt_{year}.zip"]:
        p = REFERENCE_DIR / name
        if p.exists():
            print(f"  Local file: {p}")
            return p.read_bytes()
    return None

def parse(data: bytes) -> list[dict]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        fname = next(n for n in z.namelist() if n.lower().endswith((".txt", ".csv")))
        with z.open(fname) as f:
            content = f.read().decode("utf-8", errors="replace")
    return [r for r in csv.DictReader(io.StringIO(content))
            if MARKET_NAME in r.get("Market_and_Exchange_Names", "")]

def load() -> list[dict]:
    rows, year = [], datetime.now().year
    for y in [year, year - 1]:
        data = local(y) or fetch(URL_FUT.format(year=y))
        if data:
            rows.extend(parse(data))
    if not rows:
        sys.exit("No data. Check internet connection or place ZIP manually in reference/.")
    return rows

# ── Datenaufbereitung ─────────────────────────────────────────────────────────

def pi(v: str) -> int:
    try:
        return int(v.replace(",", "").strip())
    except:
        return 0

def build(rows: list[dict]) -> list[dict]:
    series = []
    for r in rows:
        ds = r.get("Report_Date_as_YYYY-MM-DD", "").strip()
        try:
            d = datetime.strptime(ds, "%Y-%m-%d")
        except:
            continue
        series.append({
            "date":     d,
            "date_str": d.strftime("%d.%m.%Y"),
            "oi":       pi(r.get("Open_Interest_All", "0")),
            "am_long":  pi(r.get("Asset_Mgr_Positions_Long_All", "0")),
            "am_short": pi(r.get("Asset_Mgr_Positions_Short_All", "0")),
            "lf_long":  pi(r.get("Lev_Money_Positions_Long_All", "0")),
            "lf_short": pi(r.get("Lev_Money_Positions_Short_All", "0")),
        })
    series.sort(key=lambda x: x["date"])
    seen, out = set(), []
    for s in series:
        if s["date"] not in seen:
            seen.add(s["date"])
            s["am_net"] = s["am_long"] - s["am_short"]
            s["lf_net"] = s["lf_long"] - s["lf_short"]
            out.append(s)
    return out[-WEEKS:]

def cot_idx(vals: list[int]) -> int:
    mn, mx = min(vals), max(vals)
    return 50 if mx == mn else round((vals[-1] - mn) / (mx - mn) * 100)

def cot_idx_series(vals: list[int]) -> list[int]:
    out = []
    for i in range(len(vals)):
        w = vals[max(0, i - WEEKS + 1): i + 1]
        mn, mx = min(w), max(w)
        out.append(50 if mx == mn else round((vals[i] - mn) / (mx - mn) * 100))
    return out

def wow(vals: list[int]) -> int:
    return vals[-1] - vals[-2] if len(vals) >= 2 else 0

# ── Formatierung ──────────────────────────────────────────────────────────────

def fmt(n: int) -> str:
    s = "+" if n > 0 else ""
    if abs(n) >= 1_000_000: return f"{s}{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:     return f"{s}{n/1_000:.1f}K"
    return f"{s}{n:,}"

def fmt_abs(n: int) -> str:
    if abs(n) >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:     return f"{n/1_000:.0f}K"
    return str(n)

def sc(n):  return "positive" if n > 0 else ("negative" if n < 0 else "neutral")
def ar(n):  return "&#9650;" if n > 0 else ("&#9660;" if n < 0 else "&ndash;")

def idx_clr(v):
    if v >= 70: return "#39ff14"
    if v >= 40: return "#f0c040"
    return "#ff4d4d"

def idx_lbl(v):
    if v >= 70: return "Bullish"
    if v >= 40: return "Neutral"
    return "Bearish"

# ── Schnellübersicht-Logik ────────────────────────────────────────────────────

def sentiment_signal(ci: int) -> tuple[str, str, str]:
    """COT Index > 80 = Extrem Bullish, < 20 = Extrem Bearish, sonst Neutral."""
    if ci > 80:
        return "#39ff14", "Extremely Bullish", f"COT Index at {ci}/100 – Asset Managers near historical high. Strong institutional long interest."
    if ci < 20:
        return "#ff4d4d", "Extremely Bearish", f"COT Index at {ci}/100 – Asset Managers near historical low. Strong institutional short interest."
    return "#f0c040", "Neutral", f"COT Index at {ci}/100 – Asset Managers in the middle range. No extreme positioning detected."

def divergence_signal(am_wow: int, lf_wow: int, am_net: int, lf_net: int) -> tuple[str, str, str]:
    """Hoch wenn AM Long aufbaut während LF Short aufbaut (Smart Money vs. Hedgefonds)."""
    am_building_long  = am_wow > 0 and am_net > 0
    lf_building_short = lf_wow < 0 and lf_net < 0
    am_building_short = am_wow < 0 and am_net < 0
    lf_building_long  = lf_wow > 0 and lf_net > 0

    if am_building_long and lf_building_short:
        return "#39ff14", "High", "Asset Managers building long, Leveraged Funds building short. Classic Smart Money vs. Hedge Fund signal – bullish bias."
    if am_building_short and lf_building_long:
        return "#ff4d4d", "High", "Asset Managers building short, Leveraged Funds building long. Institutional hedging against hedge fund optimism – bearish bias."
    if (am_wow > 0) != (lf_wow > 0):
        return "#f0c040", "Moderate", "AM and LF moving in opposite directions. Slight divergence visible, but no extreme signal."
    return "#7a8899", "Low", "AM and LF moving in the same direction. No significant divergence this week."

# ── HTML ──────────────────────────────────────────────────────────────────────

def build_html(series: list[dict]) -> str:
    L      = series[-1]
    am_v   = [s["am_net"] for s in series]
    lf_v   = [s["lf_net"] for s in series]
    oi_v   = [s["oi"]     for s in series]
    lbls   = [s["date_str"] for s in series]

    am_net = L["am_net"];  lf_net = L["lf_net"]
    am_wow = wow(am_v);    lf_wow = wow(lf_v)
    oi_now = L["oi"];      oi_wow = wow(oi_v)
    ci     = cot_idx(am_v)
    ci_s   = cot_idx_series(am_v)

    kw     = L["date"].isocalendar()[1]
    yr     = L["date"].year

    sent_clr, sent_lbl, sent_desc = sentiment_signal(ci)
    div_clr,  div_lbl,  div_desc  = divergence_signal(am_wow, lf_wow, am_net, lf_net)

    def rgba(hex6: str, a: float) -> str:
        r, g, b = int(hex6[1:3],16), int(hex6[3:5],16), int(hex6[5:7],16)
        return f"rgba({r},{g},{b},{a})"

    cj = json.dumps

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>COT Report &ndash; S&amp;P 500 E-Mini &middot; CW {kw} {yr}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#090c11;--bg2:#0d111a;--bg3:#111720;
  --green:#39ff14;--green-glow:rgba(57,255,20,.08);--green-dim:rgba(57,255,20,.15);
  --white:#f0f4f8;--gray:#7a8899;
  --border:rgba(255,255,255,.07);--border-g:rgba(57,255,20,.2);
  --red:#ff4d4d;--yellow:#f0c040;
}}
body{{background:var(--bg);color:var(--white);font-family:'Inter',sans-serif;font-size:14px;padding:32px 32px 8px;max-width:1280px;margin:0 auto}}

/* HEADER */
.header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:36px;padding-bottom:24px;border-bottom:1px solid var(--border);gap:16px;flex-wrap:wrap}}
.logo{{display:flex;align-items:center;gap:10px}}
.logo-text{{font-family:'JetBrains Mono',monospace;font-size:17px;font-weight:700}}
.logo-text .lae{{color:var(--green)}}
.header-meta{{text-align:right}}
.header-title{{font-size:22px;font-weight:800;letter-spacing:-.3px}}
.header-sub{{font-size:12px;color:var(--gray);margin-top:5px;font-family:'JetBrains Mono',monospace}}
.kw-badge{{display:inline-block;background:var(--green-glow);border:1px solid var(--border-g);color:var(--green);font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;padding:3px 10px;border-radius:4px;margin-top:8px}}

/* SECTION LABEL */
.sec{{font-size:10px;font-weight:700;color:var(--green);letter-spacing:2.5px;text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:10px}}
.sec::after{{content:'';flex:1;height:1px;background:var(--border)}}

/* KPI GRID */
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:36px}}
@media(max-width:1000px){{.kpi-grid{{grid-template-columns:repeat(2,1fr)}}}}
.kpi{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:20px;transition:border-color .2s,box-shadow .2s;cursor:default}}
.kpi:hover{{border-color:var(--border-g);box-shadow:0 0 24px var(--green-glow)}}
.kpi.hl{{border-color:var(--border-g);background:linear-gradient(140deg,var(--bg2) 60%,rgba(57,255,20,.05) 100%)}}
.kpi-lbl{{font-size:10px;font-weight:600;color:var(--gray);text-transform:uppercase;letter-spacing:1.2px;margin-bottom:2px}}
.kpi-grp{{font-size:10px;color:var(--green);font-weight:700;letter-spacing:.8px;margin-bottom:12px;font-family:'JetBrains Mono',monospace}}
.kpi-val{{font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:700;line-height:1;margin-bottom:10px}}
.kpi-val.positive{{color:var(--green)}}.kpi-val.negative{{color:var(--red)}}.kpi-val.neutral{{color:var(--white)}}
.kpi-wow{{display:flex;align-items:center;gap:6px;font-size:11px;font-family:'JetBrains Mono',monospace;font-weight:600}}
.wow.positive{{color:var(--green)}}.wow.negative{{color:var(--red)}}.wow.neutral{{color:var(--gray)}}
.wow-lbl{{color:var(--gray);font-weight:400}}

/* COT INDEX BAR */
.idx-wrap{{margin:10px 0 4px;background:var(--bg3);border-radius:6px;height:7px;overflow:hidden}}
.idx-bar{{height:100%;border-radius:6px}}
.idx-zones{{display:flex;justify-content:space-between;font-size:9px;color:var(--gray);margin-top:4px;font-family:'JetBrains Mono',monospace}}

/* CHARTS */
.chart-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:36px}}
@media(max-width:1000px){{.chart-grid{{grid-template-columns:1fr}}}}
.card{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:22px 20px}}
.card.full{{grid-column:1/-1}}
.card-title{{font-size:13px;font-weight:700;margin-bottom:3px}}
.card-sub{{font-size:11px;color:var(--gray);margin-bottom:14px}}
.chart-wrap{{position:relative}}
.h280{{height:280px}}.h220{{height:220px}}
.legend{{display:flex;gap:18px;margin-bottom:12px;flex-wrap:wrap}}
.leg-item{{display:flex;align-items:center;gap:7px;font-size:11px;color:var(--gray)}}
.leg-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.leg-dash{{width:18px;height:2px;flex-shrink:0;background:repeating-linear-gradient(90deg,#7a8899 0 4px,transparent 4px 7px)}}

/* SCHNELLÜBERSICHT */
.insight-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:36px}}
@media(max-width:1000px){{.insight-grid{{grid-template-columns:1fr}}}}
.insight{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:20px}}
.ins-lbl{{font-size:10px;font-weight:700;color:var(--green);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-family:'JetBrains Mono',monospace}}
.ins-val{{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;margin-bottom:6px}}
.ins-desc{{font-size:11px;color:var(--gray);line-height:1.6}}

/* FOOTER */
.footer{{margin-top:24px;padding-top:16px;border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.footer-left{{font-size:11px;color:var(--gray);line-height:1.7}}
.footer-brand{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:12px}}
.footer-brand .lae{{color:var(--green)}}
.footer-claim{{font-size:10px;color:var(--gray);margin-top:2px;font-family:'JetBrains Mono',monospace}}
</style>
</head>
<body>

<!-- HEADER -->
<header class="header">
  <div class="logo">
    <svg width="30" height="30" viewBox="0 0 60 60" fill="none">
      <path d="M30,4 L54,17 L54,43 L30,56 L6,43 L6,17 Z" fill="rgba(57,255,20,.08)" stroke="#39ff14" stroke-width="1.5"/>
      <polyline points="16,40 24,28 30,33 40,18" fill="none" stroke="#39ff14" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      <polyline points="40,25 40,18 34,21" fill="none" stroke="#39ff14" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div class="logo-text"><span class="lae">LAE</span> Market Services</div>
  </div>
  <div class="header-meta">
    <div class="header-title">COT Report &ndash; S&amp;P 500 E-Mini</div>
    <div class="header-sub">Data: {L["date_str"]} &nbsp;&middot;&nbsp; CFTC TFF Report &nbsp;&middot;&nbsp; Futures Only</div>
    <div class="kw-badge">CW {kw} &middot; {yr}</div>
  </div>
</header>

<!-- KPI CARDS -->
<div class="sec">Positioning Overview</div>
<div class="kpi-grid">

  <div class="kpi hl">
    <div class="kpi-lbl">Net Position</div>
    <div class="kpi-grp">ASSET MANAGER</div>
    <div class="kpi-val {sc(am_net)}">{fmt(am_net)}</div>
    <div class="kpi-wow">
      <span class="wow {sc(am_wow)}">{ar(am_wow)}&nbsp;{fmt(am_wow)}</span>
      <span class="wow-lbl">&nbsp;WoW</span>
    </div>
  </div>

  <div class="kpi">
    <div class="kpi-lbl">Net Position</div>
    <div class="kpi-grp">LEVERAGED FUNDS</div>
    <div class="kpi-val {sc(lf_net)}">{fmt(lf_net)}</div>
    <div class="kpi-wow">
      <span class="wow {sc(lf_wow)}">{ar(lf_wow)}&nbsp;{fmt(lf_wow)}</span>
      <span class="wow-lbl">&nbsp;WoW</span>
    </div>
  </div>

  <div class="kpi">
    <div class="kpi-lbl">COT Index (52W)</div>
    <div class="kpi-grp">ASSET MANAGER</div>
    <div class="kpi-val" style="color:{idx_clr(ci)}">{ci}</div>
    <div class="idx-wrap">
      <div class="idx-bar" style="width:{ci}%;background:{idx_clr(ci)};box-shadow:0 0 10px {rgba(idx_clr(ci),.4)};"></div>
    </div>
    <div class="idx-zones">
      <span>0 Bearish</span>
      <span style="color:{idx_clr(ci)};font-weight:700">{idx_lbl(ci)}</span>
      <span>Bullish 100</span>
    </div>
  </div>

  <div class="kpi">
    <div class="kpi-lbl">Open Interest</div>
    <div class="kpi-grp">TOTAL</div>
    <div class="kpi-val neutral">{fmt_abs(oi_now)}</div>
    <div class="kpi-wow">
      <span class="wow {sc(oi_wow)}">{ar(oi_wow)}&nbsp;{fmt_abs(abs(oi_wow))}</span>
      <span class="wow-lbl">&nbsp;WoW</span>
    </div>
  </div>

</div>

<!-- CHARTS -->
<div class="sec">Historical Positioning (52 Weeks)</div>
<div style="margin-bottom:14px">
  <div class="card full">
    <div class="card-title">Net Positioning &ndash; Asset Manager &amp; Leveraged Funds</div>
    <div class="card-sub">Contracts (Long minus Short) &middot; weekly &middot; last 52 weeks</div>
    <div class="legend">
      <div class="leg-item"><div class="leg-dot" style="background:#39ff14;box-shadow:0 0 5px #39ff14aa"></div>Asset Manager</div>
      <div class="leg-item"><div class="leg-dash"></div>Leveraged Funds</div>
    </div>
    <div class="chart-wrap h280"><canvas id="netChart"></canvas></div>
  </div>
</div>

<div class="chart-grid">
  <div class="card">
    <div class="card-title">COT Index &ndash; Asset Manager (52W)</div>
    <div class="card-sub">Normalized 0&ndash;100 &middot; &gt;80 = Extremely Bullish &middot; &lt;20 = Extremely Bearish</div>
    <div class="chart-wrap h220"><canvas id="idxChart"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Open Interest</div>
    <div class="card-sub">Total open contracts &middot; current value highlighted</div>
    <div class="chart-wrap h220"><canvas id="oiChart"></canvas></div>
  </div>
</div>

<!-- SCHNELLÜBERSICHT -->
<div class="sec">Quick Overview</div>
<div class="insight-grid">

  <div class="insight">
    <div class="ins-lbl">Sentiment</div>
    <div class="ins-val" style="color:{sent_clr}">{sent_lbl}</div>
    <div class="ins-desc">{sent_desc}</div>
  </div>

  <div class="insight">
    <div class="ins-lbl">AM vs. LF Divergence</div>
    <div class="ins-val" style="color:{div_clr}">{div_lbl}</div>
    <div class="ins-desc">{div_desc}</div>
  </div>

  <div class="insight">
    <div class="ins-lbl">Open Interest</div>
    <div class="ins-val" style="color:{'#39ff14' if oi_wow > 0 else '#ff4d4d' if oi_wow < 0 else '#7a8899'}">{'Rising' if oi_wow > 0 else ('Falling' if oi_wow < 0 else 'Unchanged')}</div>
    <div class="ins-desc">OI {('rose by ' + fmt_abs(abs(oi_wow)) + ' contracts – new capital flowing into the market.') if oi_wow > 0 else ('fell by ' + fmt_abs(abs(oi_wow)) + ' contracts – positions being reduced.') if oi_wow < 0 else 'remains unchanged.'}</div>
  </div>

</div>

<!-- FOOTER -->
<footer class="footer">
  <div class="footer-left">
    <strong style="color:var(--white)">Data Source:</strong> CFTC &ndash; Commitments of Traders (TFF Report, Futures Only)<br>
    E-Mini S&amp;P 500 &middot; Chicago Mercantile Exchange &middot; As of: {L["date_str"]}
  </div>
  <div>
    <div class="footer-brand"><span class="lae">LAE</span> Market Services</div>
    <div class="footer-claim">Learn. Analyze. Execute.</div>
  </div>
</footer>

<script>
Chart.defaults.color='#7a8899';
Chart.defaults.borderColor='rgba(255,255,255,.05)';
Chart.defaults.font.family="'JetBrains Mono',monospace";
Chart.defaults.font.size=10;

const labels={cj(lbls)};
const amData={cj(am_v)};
const lfData={cj(lf_v)};
const oiData={cj(oi_v)};
const idxData={cj(ci_s)};

const tt={{backgroundColor:'#0d111a',borderColor:'rgba(57,255,20,.25)',borderWidth:1,titleColor:'#39ff14',bodyColor:'#f0f4f8',padding:10}};

const zeroLine={{
  id:'zeroLine',
  afterDraw(c){{
    const{{ctx,scales,chartArea}}=c;
    if(!scales.y)return;
    const y0=scales.y.getPixelForValue(0);
    if(y0<chartArea.top||y0>chartArea.bottom)return;
    ctx.save();ctx.beginPath();
    ctx.moveTo(chartArea.left,y0);ctx.lineTo(chartArea.right,y0);
    ctx.strokeStyle='rgba(255,255,255,.18)';ctx.lineWidth=1;ctx.setLineDash([5,4]);
    ctx.stroke();ctx.restore();
  }}
}};

// NET POSITIONING
new Chart(document.getElementById('netChart'),{{
  type:'line',plugins:[zeroLine],
  data:{{labels,datasets:[
    {{
      label:'Asset Manager',data:amData,
      borderColor:'#39ff14',
      backgroundColor:(ctx)=>{{const g=ctx.chart.ctx.createLinearGradient(0,0,0,280);g.addColorStop(0,'rgba(57,255,20,.12)');g.addColorStop(1,'rgba(57,255,20,.01)');return g;}},
      borderWidth:2,pointRadius:0,pointHoverRadius:5,
      pointHoverBackgroundColor:'#39ff14',pointHoverBorderColor:'#090c11',pointHoverBorderWidth:2,
      tension:.38,fill:true
    }},
    {{
      label:'Leveraged Funds',data:lfData,
      borderColor:'#7a8899',backgroundColor:'transparent',
      borderWidth:1.5,borderDash:[5,4],pointRadius:0,pointHoverRadius:4,
      pointHoverBackgroundColor:'#7a8899',tension:.38,fill:false
    }}
  ]}},
  options:{{
    responsive:true,maintainAspectRatio:false,
    interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{display:false}},tooltip:{{...tt,callbacks:{{
      label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.parsed.y.toLocaleString('de-DE')}} Kontrakte`
    }}}}}},
    scales:{{
      x:{{grid:{{display:false}},ticks:{{maxTicksLimit:10,maxRotation:0}}}},
      y:{{grid:{{color:'rgba(255,255,255,.04)'}},ticks:{{callback:v=>Math.abs(v)>=1000?(v/1000).toFixed(0)+'K':v}}}}
    }}
  }}
}});

// COT INDEX
new Chart(document.getElementById('idxChart'),{{
  type:'line',
  data:{{labels,datasets:[{{
    data:idxData,borderColor:'#39ff14',
    backgroundColor:(ctx)=>{{const g=ctx.chart.ctx.createLinearGradient(0,0,0,220);g.addColorStop(0,'rgba(57,255,20,.2)');g.addColorStop(1,'rgba(57,255,20,0)');return g;}},
    borderWidth:2,pointRadius:0,pointHoverRadius:4,
    pointHoverBackgroundColor:'#39ff14',tension:.42,fill:true
  }}]}},
  options:{{
    responsive:true,maintainAspectRatio:false,
    interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{display:false}},tooltip:{{...tt,callbacks:{{label:ctx=>` COT Index: ${{ctx.parsed.y}}`}}}}}},
    scales:{{
      x:{{grid:{{display:false}},ticks:{{maxTicksLimit:6,maxRotation:0}}}},
      y:{{min:0,max:100,grid:{{color:'rgba(255,255,255,.04)'}},ticks:{{stepSize:25}},
        afterDraw(c){{
          const{{ctx,chartArea}}=c.chart;
          [[80,'rgba(57,255,20,.12)'],[20,'rgba(255,77,77,.12)']].forEach(([v,col])=>{{
            const y=c.getPixelForValue(v);
            ctx.save();ctx.fillStyle=col;
            ctx.fillRect(chartArea.left,v>=50?chartArea.top:y,chartArea.right-chartArea.left,v>=50?y-chartArea.top:chartArea.bottom-y);
            ctx.restore();
          }});
        }}
      }}
    }}
  }}
}});

// OPEN INTEREST
new Chart(document.getElementById('oiChart'),{{
  type:'bar',
  data:{{labels,datasets:[{{
    data:oiData,
    backgroundColor:oiData.map((_,i)=>i===oiData.length-1?'rgba(57,255,20,.55)':'rgba(122,136,153,.2)'),
    borderColor:oiData.map((_,i)=>i===oiData.length-1?'#39ff14':'transparent'),
    borderWidth:1,borderRadius:2,
    hoverBackgroundColor:oiData.map((_,i)=>i===oiData.length-1?'rgba(57,255,20,.7)':'rgba(122,136,153,.35)')
  }}]}},
  options:{{
    responsive:true,maintainAspectRatio:false,
    interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{display:false}},tooltip:{{...tt,callbacks:{{label:ctx=>` OI: ${{(ctx.parsed.y/1000).toFixed(0)}}K`}}}}}},
    scales:{{
      x:{{grid:{{display:false}},ticks:{{maxTicksLimit:6,maxRotation:0}}}},
      y:{{grid:{{color:'rgba(255,255,255,.04)'}},ticks:{{callback:v=>(v/1000).toFixed(0)+'K'}}}}
    }}
  }}
}});

function sendHeight(){{
  var ftr = document.querySelector('.footer');
  var h = ftr
    ? Math.ceil(ftr.getBoundingClientRect().bottom + window.scrollY)
    : (document.documentElement.scrollHeight || document.body.scrollHeight);
  window.parent.postMessage({{ frameHeight: h }}, '*');
}}
window.addEventListener('load', function(){{
  sendHeight();
  setTimeout(sendHeight, 500);
  setTimeout(sendHeight, 1500);
}});
</script>
</body>
</html>"""

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("LAE COT Report Generator")
    print("-" * 40)
    print("\nLade CFTC TFF Futures Only ...")
    rows   = load()
    series = build(rows)
    if not series:
        sys.exit("Fehler: Keine verwertbaren Daten.")

    L = series[-1]
    fname  = f"lae-cot-report-{L['date'].strftime('%Y-%m-%d')}.html"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / fname
    out.write_text(build_html(series), encoding="utf-8")

    ci = cot_idx([s["am_net"] for s in series])
    print(f"\n  Report:        {out}")
    print(f"  Datum:         {L['date_str']}")
    print(f"  Wochen:        {len(series)}")
    print(f"  AM Net:        {L['am_net']:,}")
    print(f"  LF Net:        {L['lf_net']:,}")
    print(f"  COT Index:     {ci}")
    print(f"  Open Interest: {L['oi']:,}")

    # ── Portal-Archiv aktualisieren ───────────────────────────────────────────
    portal_path = Path(__file__).parents[3] / "outputs" / "portal" / "products" / "cot-report.html"
    if portal_path.exists():
        portal_html = portal_path.read_text(encoding="utf-8")
        rel_src  = f"../../cot-report/{fname}"
        kw       = L["date"].isocalendar()[1]
        yr       = L["date"].year
        label    = f"CW {kw} · {yr}"
        new_item = f'              <option value="{rel_src}">{label}</option>'
        marker   = "              <!-- ARCHIV-START -->"
        if rel_src not in portal_html:
            portal_html = portal_html.replace(marker, marker + "\n" + new_item)
            portal_path.write_text(portal_html, encoding="utf-8")
            print(f"  Portal:        aktualisiert ({label})")
        else:
            print(f"  Portal:        Eintrag bereits vorhanden")

    # ── Dashboard-Data JSON aktualisieren ─────────────────────────────────────
    dash_json = Path(__file__).parents[3] / "outputs" / "portal" / "dashboard-data.json"
    pub_date  = datetime.today().strftime("%Y-%m-%d")
    kw        = L["date"].isocalendar()[1]
    yr        = L["date"].year
    new_entry = {
        "type": "COT Report",
        "title": f"COT Report · CW {kw} · {yr}",
        "teaser": "Latest Commitments of Traders data for S&P 500 E-Mini futures. Net positioning, commercial vs. non-commercial flows.",
        "link": "./products/cot-report.html",
        "date": pub_date,
    }
    dash = {}
    if dash_json.exists():
        try: dash = json.loads(dash_json.read_text(encoding="utf-8"))
        except Exception: pass
    dash["updates"] = [new_entry] + [u for u in dash.get("updates", []) if u.get("type") != "COT Report"]
    dash_json.write_text(json.dumps(dash, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Dashboard:     aktualisiert (CW {kw} · {yr})")

if __name__ == "__main__":
    main()
