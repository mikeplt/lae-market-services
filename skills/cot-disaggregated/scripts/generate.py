"""
LAE Market Services – COT Disaggregated Report Generator
Disaggregated Futures Only · Gold, Crude Oil, Natural Gas, Wheat
"""

import csv
import io
import json
import math
import sys
import zipfile
from datetime import datetime
from pathlib import Path
import urllib.request

# ── Konfiguration ─────────────────────────────────────────────────────────────
URL_FUT       = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
OUTPUT_DIR    = Path(__file__).parents[3] / "outputs" / "cot-disaggregated"
REFERENCE_DIR = Path(__file__).parents[3] / "reference"
WEEKS         = 52

MARKETS = [
    {"slug": "gold",      "label": "Gold",        "exchange": "COMEX", "cftc": "GOLD - COMMODITY EXCHANGE INC."},
    {"slug": "crude-oil", "label": "Crude Oil",    "exchange": "ICE",   "cftc": "CRUDE OIL, LIGHT SWEET-WTI - ICE FUTURES EUROPE"},
    {"slug": "nat-gas",   "label": "Natural Gas",  "exchange": "NYMEX", "cftc": "NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE"},
    {"slug": "wheat",     "label": "Wheat",        "exchange": "CBOT",  "cftc": "WHEAT-SRW - CHICAGO BOARD OF TRADE"},
]

# ── Download & Parse ──────────────────────────────────────────────────────────

def fetch(url):
    print(f"  Loading {url} ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LAE-COT/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except Exception as e:
        print(f"  Error: {e}")
        return None

def local_file(year):
    p = REFERENCE_DIR / f"fut_disagg_txt_{year}.zip"
    if p.exists():
        print(f"  Local file: {p}")
        return p.read_bytes()
    return None

def parse_all(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        fname = next(n for n in z.namelist() if n.lower().endswith((".txt", ".csv")))
        with z.open(fname) as f:
            content = f.read().decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(content)))

def load_all_rows():
    rows = []
    year = datetime.now().year
    for y in [year, year - 1]:
        data = local_file(y) or fetch(URL_FUT.format(year=y))
        if data:
            try:
                rows.extend(parse_all(data))
            except Exception as e:
                print(f"  Parse error {y}: {e}")
    if not rows:
        sys.exit("No data. Check internet connection or place ZIP manually in reference/.")
    return rows

# ── Datenaufbereitung ─────────────────────────────────────────────────────────

def pi(v):
    try:
        return int(str(v).replace(",", "").strip())
    except Exception:
        return 0

def build_market(all_rows, cftc_name):
    rows = [r for r in all_rows if cftc_name in r.get("Market_and_Exchange_Names", "")]
    series = []
    for r in rows:
        ds = r.get("Report_Date_as_YYYY-MM-DD", "").strip()
        try:
            d = datetime.strptime(ds, "%Y-%m-%d")
        except Exception:
            continue
        series.append({
            "date":       d,
            "date_str":   d.strftime("%d.%m.%Y"),
            "oi":         pi(r.get("Open_Interest_All",              "0")),
            "prod_long":  pi(r.get("Prod_Merc_Positions_Long_All",   "0")),
            "prod_short": pi(r.get("Prod_Merc_Positions_Short_All",  "0")),
            "mm_long":    pi(r.get("M_Money_Positions_Long_All",     "0")),
            "mm_short":   pi(r.get("M_Money_Positions_Short_All",    "0")),
        })
    series.sort(key=lambda x: x["date"])
    seen, out = set(), []
    for s in series:
        if s["date"] not in seen:
            seen.add(s["date"])
            s["prod_net"] = s["prod_long"] - s["prod_short"]
            s["mm_net"]   = s["mm_long"]   - s["mm_short"]
            out.append(s)
    return out[-WEEKS:]

def cot_idx(vals):
    mn, mx = min(vals), max(vals)
    return 50 if mx == mn else round((vals[-1] - mn) / (mx - mn) * 100)

def cot_idx_series(vals):
    out = []
    for i in range(len(vals)):
        w = vals[max(0, i - WEEKS + 1): i + 1]
        mn, mx = min(w), max(w)
        out.append(50 if mx == mn else round((vals[i] - mn) / (mx - mn) * 100))
    return out

def wow(vals):
    return vals[-1] - vals[-2] if len(vals) >= 2 else 0

# ── Formatierung ──────────────────────────────────────────────────────────────

def fmt(n):
    s = "+" if n > 0 else ""
    if abs(n) >= 1_000_000: return f"{s}{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:     return f"{s}{n/1_000:.1f}K"
    return f"{s}{n:,}"

def fmt_abs(n):
    if abs(n) >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:     return f"{n/1_000:.0f}K"
    return str(n)

def sc(n):  return "positive" if n > 0 else ("negative" if n < 0 else "neutral")
def ar(n):  return "&#9650;" if n > 0 else ("&#9660;" if n < 0 else "&ndash;")

def idx_clr(v):
    if v >= 70: return "#39ff14"
    if v >= 30: return "#f0c040"
    return "#ff4d4d"

def idx_lbl(v):
    if v >= 70: return "Bullish"
    if v >= 30: return "Neutral"
    return "Bearish"

def nice_step(mn, mx, n_ticks=5):
    r = max(abs(mx - mn), 1)
    raw = r / n_ticks
    mag = 10 ** math.floor(math.log10(raw))
    for s in [1, 2, 2.5, 5, 10]:
        if raw <= s * mag:
            return int(s * mag)
    return int(10 * mag)

# ── Schnellübersicht-Logik ────────────────────────────────────────────────────

def sentiment_signal(ci, label):
    if ci >= 70:
        return "#39ff14", "Bullish", f"COT Index at {ci}/100 – Producer/Merchant near historical low short exposure. Reduced hedging suggests less supply pressure – bullish for {label} prices."
    if ci <= 30:
        return "#ff4d4d", "Bearish", f"COT Index at {ci}/100 – Producer/Merchant near historical high short exposure. Heavy hedging signals supply-side pressure – bearish for {label} prices."
    return "#f0c040", "Neutral", f"COT Index at {ci}/100 – Producer/Merchant in the middle range. No extreme positioning detected."

def divergence_signal(prod_wow, mm_wow):
    prod_improving = prod_wow > 0
    mm_building    = mm_wow > 0
    if prod_improving and mm_building:
        return "#39ff14", "Bullish Setup", "Producer/Merchant covering shorts while Managed Money adds longs. Both groups aligned to the upside – a strong bullish signal."
    if not prod_improving and not mm_building:
        return "#ff4d4d", "Bearish Setup", "Producer/Merchant adding shorts while Managed Money reduces longs. Both groups aligned to the downside – a strong bearish signal."
    if prod_improving and not mm_building:
        return "#f0c040", "Mixed", "Producer/Merchant reducing short exposure but Managed Money trimming longs. Conflicting signals – monitor for resolution."
    return "#7a8899", "Mixed", "Producer/Merchant adding shorts while Managed Money adds longs. Structural divergence between hedgers and speculators."

# ── HTML ──────────────────────────────────────────────────────────────────────

def build_html(series, market):
    L        = series[-1]
    prod_v   = [s["prod_net"] for s in series]
    mm_v     = [s["mm_net"]   for s in series]
    oi_v     = [s["oi"]       for s in series]
    lbls     = [s["date_str"] for s in series]

    prod_net = L["prod_net"];  mm_net  = L["mm_net"]
    prod_wow_ = wow(prod_v);   mm_wow_ = wow(mm_v)
    oi_now   = L["oi"];        oi_wow_ = wow(oi_v)
    ci       = cot_idx(prod_v)
    ci_s     = cot_idx_series(prod_v)

    _ps      = nice_step(min(prod_v), max(prod_v))
    prod_ymin = math.floor(min(prod_v) / _ps) * _ps
    prod_ymax = math.ceil(max(prod_v)  / _ps) * _ps
    _ms      = nice_step(min(mm_v), max(mm_v))
    mm_ymin  = math.floor(min(mm_v) / _ms) * _ms
    mm_ymax  = math.ceil(max(mm_v)  / _ms) * _ms
    prod_avg = round(sum(prod_v) / len(prod_v))
    mm_avg   = round(sum(mm_v)   / len(mm_v))
    _os      = nice_step(min(oi_v), max(oi_v))
    oi_ymin  = math.floor(min(oi_v) / _os) * _os
    oi_ymax  = math.ceil(max(oi_v)  / _os) * _os

    kw   = L["date"].isocalendar()[1]
    yr   = L["date"].year
    lbl  = market["label"]
    exch = market["exchange"]

    sent_clr, sent_lbl, sent_desc = sentiment_signal(ci, lbl)
    div_clr,  div_lbl,  div_desc  = divergence_signal(prod_wow_, mm_wow_)

    def rgba(hex6, a):
        r_, g_, b_ = int(hex6[1:3], 16), int(hex6[3:5], 16), int(hex6[5:7], 16)
        return f"rgba({r_},{g_},{b_},{a})"

    oi_trend_clr  = "#39ff14" if oi_wow_ > 0 else ("#ff4d4d" if oi_wow_ < 0 else "#7a8899")
    oi_trend_lbl  = "Rising"   if oi_wow_ > 0 else ("Falling"  if oi_wow_ < 0 else "Unchanged")
    oi_trend_desc = (
        f"OI rose by {fmt_abs(abs(oi_wow_))} contracts – new capital entering the market."
        if oi_wow_ > 0 else
        f"OI fell by {fmt_abs(abs(oi_wow_))} contracts – positions being closed."
        if oi_wow_ < 0 else
        "OI remains unchanged this week."
    )

    cj = json.dumps

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{lbl} &ndash; COT Positioning &middot; CW {kw} {yr}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#090c11;--bg2:#0d111a;--bg3:#111720;
  --green:#39ff14;--green-glow:rgba(57,255,20,.08);
  --white:#f0f4f8;--gray:#7a8899;
  --border:rgba(255,255,255,.07);--border-g:rgba(57,255,20,.2);
  --red:#ff4d4d;--yellow:#f0c040;
}}
body{{background:var(--bg);color:var(--white);font-family:'Inter',sans-serif;font-size:14px;padding:32px 32px 8px;max-width:1280px;margin:0 auto}}
.header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:36px;padding-bottom:24px;border-bottom:1px solid var(--border);gap:16px;flex-wrap:wrap}}
.logo{{display:flex;align-items:center;gap:10px}}
.logo-text{{font-family:'JetBrains Mono',monospace;font-size:17px;font-weight:700}}
.logo-text .lae{{color:var(--green)}}
.header-meta{{text-align:right}}
.header-title{{font-size:22px;font-weight:800;letter-spacing:-.3px}}
.header-sub{{font-size:12px;color:var(--gray);margin-top:5px;font-family:'JetBrains Mono',monospace}}
.kw-badge{{display:inline-block;background:var(--green-glow);border:1px solid var(--border-g);color:var(--green);font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;padding:3px 10px;border-radius:4px;margin-top:8px}}
.sec{{font-size:10px;font-weight:700;color:var(--green);letter-spacing:2.5px;text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:10px}}
.sec::after{{content:'';flex:1;height:1px;background:var(--border)}}
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
.idx-wrap{{margin:10px 0 4px;background:var(--bg3);border-radius:6px;height:7px;overflow:hidden}}
.idx-bar{{height:100%;border-radius:6px}}
.idx-zones{{display:flex;justify-content:space-between;font-size:9px;color:var(--gray);margin-top:4px;font-family:'JetBrains Mono',monospace}}
.chart-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:36px}}
@media(max-width:1000px){{.chart-grid{{grid-template-columns:1fr}}}}
.card{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:22px 20px}}
.card.full{{grid-column:1/-1}}
.card-title{{font-size:13px;font-weight:700;margin-bottom:3px}}
.card-sub{{font-size:11px;color:var(--gray);margin-bottom:14px}}
.chart-wrap{{position:relative}}
.h220{{height:220px}}
.legend{{display:flex;gap:18px;margin-bottom:12px;flex-wrap:wrap}}
.leg-item{{display:flex;align-items:center;gap:7px;font-size:11px;color:var(--gray)}}
.leg-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.insight-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:36px}}
@media(max-width:1000px){{.insight-grid{{grid-template-columns:1fr}}}}
.insight{{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:20px}}
.ins-lbl{{font-size:10px;font-weight:700;color:var(--green);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-family:'JetBrains Mono',monospace}}
.ins-val{{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;margin-bottom:6px}}
.ins-desc{{font-size:11px;color:var(--gray);line-height:1.6}}
.footer{{margin-top:24px;padding-top:16px;border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.footer-left{{font-size:11px;color:var(--gray);line-height:1.7}}
.footer-brand{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:12px}}
.footer-brand .lae{{color:var(--green)}}
.footer-claim{{font-size:10px;color:var(--gray);margin-top:2px;font-family:'JetBrains Mono',monospace}}
</style>
</head>
<body>

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
    <div class="header-title">{lbl} &ndash; COT Positioning</div>
    <div class="header-sub">Data: {L["date_str"]} &nbsp;&middot;&nbsp; CFTC Disaggregated &nbsp;&middot;&nbsp; Futures Only &nbsp;&middot;&nbsp; {exch}</div>
    <div class="kw-badge">CW {kw} &middot; {yr}</div>
  </div>
</header>

<div class="sec">Positioning Overview</div>
<div class="kpi-grid">

  <div class="kpi hl">
    <div class="kpi-lbl">Net Position</div>
    <div class="kpi-grp">PRODUCER/MERCHANT</div>
    <div class="kpi-val {sc(prod_net)}">{fmt(prod_net)}</div>
    <div class="kpi-wow">
      <span class="wow {sc(prod_wow_)}">{ar(prod_wow_)}&nbsp;{fmt(prod_wow_)}</span>
      <span class="wow-lbl">&nbsp;WoW</span>
    </div>
  </div>

  <div class="kpi hl">
    <div class="kpi-lbl">Net Position</div>
    <div class="kpi-grp">MANAGED MONEY</div>
    <div class="kpi-val {sc(mm_net)}">{fmt(mm_net)}</div>
    <div class="kpi-wow">
      <span class="wow {sc(mm_wow_)}">{ar(mm_wow_)}&nbsp;{fmt(mm_wow_)}</span>
      <span class="wow-lbl">&nbsp;WoW</span>
    </div>
  </div>

  <div class="kpi hl">
    <div class="kpi-lbl">COT Index (52W)</div>
    <div class="kpi-grp">PRODUCER/MERCHANT</div>
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

  <div class="kpi hl">
    <div class="kpi-lbl">Open Interest</div>
    <div class="kpi-grp">TOTAL</div>
    <div class="kpi-val neutral">{fmt_abs(oi_now)}</div>
    <div class="kpi-wow">
      <span class="wow {sc(oi_wow_)}">{ar(oi_wow_)}&nbsp;{fmt_abs(abs(oi_wow_))}</span>
      <span class="wow-lbl">&nbsp;WoW</span>
    </div>
  </div>

</div>

<div class="sec">Historical Positioning (52 Weeks)</div>
<div style="margin-bottom:14px;display:grid;gap:14px">
  <div class="card full">
    <div class="card-title">Net Positioning &ndash; Producer/Merchant</div>
    <div class="card-sub">Contracts (Long minus Short) &middot; weekly &middot; last 52 weeks</div>
    <div class="legend">
      <div class="leg-item"><div class="leg-dot" style="background:#39ff14;box-shadow:0 0 5px #39ff14aa"></div>Producer/Merchant</div>
      <div class="leg-item"><span style="display:inline-block;width:18px;height:2px;background:repeating-linear-gradient(90deg,rgba(57,255,20,.45) 0 3px,transparent 3px 6px)"></span>&nbsp;Producer/Merchant Ø 52W</div>
    </div>
    <div class="chart-wrap h220"><canvas id="prodChart"></canvas></div>
  </div>
  <div class="card full">
    <div class="card-title">Net Positioning &ndash; Managed Money</div>
    <div class="card-sub">Contracts (Long minus Short) &middot; weekly &middot; last 52 weeks</div>
    <div class="legend">
      <div class="leg-item"><span style="display:inline-block;width:18px;height:2px;background:repeating-linear-gradient(90deg,#7a8899 0 5px,transparent 5px 8px)"></span>&nbsp;Managed Money</div>
      <div class="leg-item"><span style="display:inline-block;width:18px;height:2px;background:repeating-linear-gradient(90deg,rgba(122,136,153,.45) 0 3px,transparent 3px 6px)"></span>&nbsp;Managed Money Ø 52W</div>
    </div>
    <div class="chart-wrap h220"><canvas id="mmChart"></canvas></div>
  </div>
</div>

<div class="chart-grid">
  <div class="card">
    <div class="card-title">COT Index &ndash; Producer/Merchant (52W)</div>
    <div class="card-sub">Normalized 0&ndash;100 &middot; &gt;70 = Bullish &middot; &lt;30 = Bearish</div>
    <div class="chart-wrap h220"><canvas id="idxChart"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Open Interest</div>
    <div class="card-sub">Total open contracts &middot; weekly &middot; last 52 weeks</div>
    <div class="chart-wrap h220"><canvas id="oiChart"></canvas></div>
  </div>
</div>

<div class="sec">Quick Overview</div>
<div class="insight-grid">

  <div class="insight">
    <div class="ins-lbl">Sentiment</div>
    <div class="ins-val" style="color:{sent_clr}">{sent_lbl}</div>
    <div class="ins-desc">{sent_desc}</div>
  </div>

  <div class="insight">
    <div class="ins-lbl">Producer/Merchant vs. MM</div>
    <div class="ins-val" style="color:{div_clr}">{div_lbl}</div>
    <div class="ins-desc">{div_desc}</div>
  </div>

  <div class="insight">
    <div class="ins-lbl">Open Interest</div>
    <div class="ins-val" style="color:{oi_trend_clr}">{oi_trend_lbl}</div>
    <div class="ins-desc">{oi_trend_desc}</div>
  </div>

</div>

<footer class="footer">
  <div class="footer-left">
    <strong style="color:var(--white)">Data Source:</strong> CFTC &ndash; Commitments of Traders (Disaggregated Report, Futures Only)<br>
    {lbl} &middot; {exch} &middot; As of: {L["date_str"]}
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
const prodData={cj(prod_v)};
const mmData={cj(mm_v)};
const oiData={cj(oi_v)};
const idxData={cj(ci_s)};
const prodAvg={prod_avg};
const mmAvg={mm_avg};

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

const netTip={{...tt,callbacks:{{
  label:ctx=>ctx.dataset.pointHoverRadius===0
    ?` ${{ctx.dataset.label}}: ${{(ctx.parsed.y/1000).toFixed(0)}}K (avg)`
    :` ${{ctx.dataset.label}}: ${{ctx.parsed.y.toLocaleString('en-US')}} Contracts`
}}}};

const axTick=v=>Math.abs(v)>=1e6?(v/1e6).toFixed(1)+'M':Math.abs(v)>=1e3?(v/1e3).toFixed(0)+'K':v;

new Chart(document.getElementById('prodChart'),{{
  type:'line',plugins:[zeroLine],
  data:{{labels,datasets:[
    {{
      label:'Producer/Merchant',data:prodData,
      borderColor:'#39ff14',
      backgroundColor:(ctx)=>{{const g=ctx.chart.ctx.createLinearGradient(0,0,0,220);g.addColorStop(0,'rgba(57,255,20,.12)');g.addColorStop(1,'rgba(57,255,20,.01)');return g;}},
      borderWidth:2,pointRadius:0,pointHoverRadius:5,
      pointHoverBackgroundColor:'#39ff14',pointHoverBorderColor:'#090c11',pointHoverBorderWidth:2,
      tension:.38,fill:true
    }},
    {{
      label:'Producer/Merchant Ø 52W',data:Array(labels.length).fill(prodAvg),
      borderColor:'rgba(57,255,20,.35)',backgroundColor:'transparent',
      borderWidth:1,borderDash:[3,5],pointRadius:0,pointHoverRadius:0,tension:0,fill:false
    }}
  ]}},
  options:{{
    responsive:true,maintainAspectRatio:false,
    interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{display:false}},tooltip:{{...netTip}}}},
    scales:{{
      x:{{grid:{{display:false}},ticks:{{maxTicksLimit:10,maxRotation:0}}}},
      y:{{min:{prod_ymin},max:{prod_ymax},grid:{{color:'rgba(255,255,255,.04)'}},ticks:{{callback:axTick}}}}
    }}
  }}
}});

new Chart(document.getElementById('mmChart'),{{
  type:'line',plugins:[zeroLine],
  data:{{labels,datasets:[
    {{
      label:'Managed Money',data:mmData,
      borderColor:'#7a8899',backgroundColor:'transparent',
      borderWidth:1.5,borderDash:[5,4],pointRadius:0,pointHoverRadius:4,
      pointHoverBackgroundColor:'#7a8899',tension:.38,fill:false
    }},
    {{
      label:'Managed Money Ø 52W',data:Array(labels.length).fill(mmAvg),
      borderColor:'rgba(122,136,153,.35)',backgroundColor:'transparent',
      borderWidth:1,borderDash:[3,5],pointRadius:0,pointHoverRadius:0,tension:0,fill:false
    }}
  ]}},
  options:{{
    responsive:true,maintainAspectRatio:false,
    interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{display:false}},tooltip:{{...netTip}}}},
    scales:{{
      x:{{grid:{{display:false}},ticks:{{maxTicksLimit:10,maxRotation:0}}}},
      y:{{min:{mm_ymin},max:{mm_ymax},grid:{{color:'rgba(255,255,255,.04)'}},ticks:{{callback:axTick}}}}
    }}
  }}
}});

new Chart(document.getElementById('idxChart'),{{
  type:'line',
  data:{{labels,datasets:[{{
    data:idxData,borderColor:'#39ff14',
    backgroundColor:(ctx)=>{{const g=ctx.chart.ctx.createLinearGradient(0,0,0,220);g.addColorStop(0,'rgba(57,255,20,.2)');g.addColorStop(1,'rgba(57,255,20,0)');return g;}},
    borderWidth:2,pointRadius:0,pointHoverRadius:4,
    pointHoverBackgroundColor:'#39ff14',tension:.42,fill:true,clip:false
  }}]}},
  options:{{
    responsive:true,maintainAspectRatio:false,
    interaction:{{mode:'index',intersect:false}},
    layout:{{padding:{{top:8,left:4,right:4}}}},
    plugins:{{legend:{{display:false}},tooltip:{{...tt,callbacks:{{label:ctx=>` COT Index: ${{ctx.parsed.y}}`}}}}}},
    scales:{{
      x:{{grid:{{display:false}},ticks:{{maxTicksLimit:6,maxRotation:0}}}},
      y:{{min:0,max:100,grid:{{color:'rgba(255,255,255,.04)'}},ticks:{{stepSize:25}},
        afterDraw(c){{
          const{{ctx,chartArea}}=c.chart;
          [[70,'rgba(57,255,20,.12)'],[30,'rgba(255,77,77,.12)']].forEach(([v,col])=>{{
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

const oiMin=Math.min(...oiData),oiMax=Math.max(...oiData);
const oiMinIdx=oiData.lastIndexOf(oiMin),oiMaxIdx=oiData.lastIndexOf(oiMax),oiLastIdx=oiData.length-1;
function oiBg(i){{
  if(i===oiLastIdx)return'rgba(57,255,20,.55)';
  if(i===oiMaxIdx) return'rgba(240,192,64,.45)';
  if(i===oiMinIdx) return'rgba(255,77,77,.45)';
  return'rgba(122,136,153,.2)';
}}
function oiBorder(i){{
  if(i===oiLastIdx)return'#39ff14';
  if(i===oiMaxIdx) return'#f0c040';
  if(i===oiMinIdx) return'#ff4d4d';
  return'transparent';
}}
new Chart(document.getElementById('oiChart'),{{
  type:'bar',
  data:{{labels,datasets:[{{
    data:oiData,
    backgroundColor:oiData.map((_,i)=>oiBg(i)),
    borderColor:oiData.map((_,i)=>oiBorder(i)),
    borderWidth:1,borderRadius:2,
    hoverBackgroundColor:oiData.map((_,i)=>oiBg(i))
  }}]}},
  options:{{
    responsive:true,maintainAspectRatio:false,
    interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{display:false}},tooltip:{{...tt,callbacks:{{label:ctx=>` OI: ${{ctx.parsed.y.toLocaleString('en-US')}}`}}}}}},
    scales:{{
      x:{{grid:{{display:false}},ticks:{{maxTicksLimit:6,maxRotation:0}}}},
      y:{{min:{oi_ymin},max:{oi_ymax},grid:{{color:'rgba(255,255,255,.04)'}},ticks:{{callback:axTick}}}}
    }}
  }}
}});

function sendHeight(){{
  var ftr=document.querySelector('.footer');
  var h=ftr?Math.ceil(ftr.getBoundingClientRect().bottom+window.scrollY)
           :(document.documentElement.scrollHeight||document.body.scrollHeight);
  window.parent.postMessage({{frameHeight:h}},'*');
}}
window.addEventListener('load',function(){{sendHeight();setTimeout(sendHeight,500);setTimeout(sendHeight,1500);}});
</script>
</body>
</html>"""

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("LAE COT Disaggregated Report Generator")
    print("-" * 40)
    print("\nLade CFTC Disaggregated Futures Only ...")
    all_rows = load_all_rows()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    portal_path = Path(__file__).parents[3] / "outputs" / "portal" / "products" / "cot-disaggregated.html"
    portal_html = portal_path.read_text(encoding="utf-8") if portal_path.exists() else ""

    latest_date = None

    for market in MARKETS:
        slug  = market["slug"]
        label = market["label"]

        print(f"\n[{label}]")
        series = build_market(all_rows, market["cftc"])
        if not series:
            print(f"  Keine Daten gefunden.")
            continue

        L = series[-1]
        latest_date = latest_date or L["date"]

        fname = f"lae-cot-disaggregated-{slug}-{L['date'].strftime('%Y-%m-%d')}.html"
        out   = OUTPUT_DIR / fname
        out.write_text(build_html(series, market), encoding="utf-8")

        ci = cot_idx([s["prod_net"] for s in series])
        print(f"  Report:        {out}")
        print(f"  Datum:         {L['date_str']}")
        print(f"  Prod Net:      {L['prod_net']:,}")
        print(f"  MM Net:        {L['mm_net']:,}")
        print(f"  COT Index:     {ci}")
        print(f"  Open Interest: {L['oi']:,}")

        # Portal-Archiv aktualisieren
        if portal_html:
            kw         = L["date"].isocalendar()[1]
            yr         = L["date"].year
            lbl_opt    = f"CW {kw} · {yr}"
            rel_src    = f"../../cot-disaggregated/{fname}"
            marker_key = slug.upper()          # gold→GOLD, crude-oil→CRUDE-OIL, etc.
            start_mark = f"              <!-- ARCHIV-{marker_key}-START -->"
            new_item   = f'              <option value="{rel_src}">{lbl_opt}</option>'
            if rel_src not in portal_html:
                portal_html = portal_html.replace(start_mark, start_mark + "\n" + new_item)
                print(f"  Portal:        aktualisiert ({lbl_opt})")
            else:
                print(f"  Portal:        Eintrag bereits vorhanden")

    # Portal-HTML zurückschreiben (einmalig nach allen Märkten)
    if portal_html and portal_path.exists():
        portal_path.write_text(portal_html, encoding="utf-8")

    # ── Dashboard-Data JSON aktualisieren ─────────────────────────────────────
    if latest_date:
        dash_json = Path(__file__).parents[3] / "outputs" / "portal" / "dashboard-data.json"
        kw        = latest_date.isocalendar()[1]
        yr        = latest_date.year
        pub_date  = datetime.today().strftime("%Y-%m-%d")
        new_entry = {
            "type":   "COT Report",
            "title":  f"COT Disaggregated · CW {kw} · {yr}",
            "teaser": "Commodity positioning: Gold, Crude Oil, Natural Gas & Wheat. Producers vs. Managed Money flows.",
            "link":   "./products/cot-disaggregated.html",
            "date":   pub_date,
        }
        dash = {}
        if dash_json.exists():
            try:
                dash = json.loads(dash_json.read_text(encoding="utf-8"))
            except Exception:
                pass
        dash["updates"] = [new_entry] + [
            u for u in dash.get("updates", [])
            if not (u.get("type") == "COT Report" and "Disaggregated" in u.get("title", ""))
        ]
        dash_json.write_text(json.dumps(dash, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n  Dashboard:     aktualisiert (CW {kw} · {yr})")

if __name__ == "__main__":
    main()
