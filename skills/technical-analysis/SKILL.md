---
name: technical-analysis
description: >
  Analyzes a TradingView chart screenshot and generates a structured HTML Technical Analysis
  report for the LAE portal. Use this skill whenever Mike provides a TradingView screenshot
  and wants a chart analysis — even if he just pastes an image path, says "TA für [Asset]",
  "Technical Analysis für [Asset]", "analysiere diesen Chart", "erstelle eine Chart-Analyse",
  "TA [Ticker]", or "schau dir den Chart an". Claude reads the image directly, identifies
  all indicators and zones using their fixed color conventions (SMA 200 = purple,
  BB = light blue/red/green, Long AVWAP = green, Short AVWAP = red, Support/Resistance = orange,
  Gaps = colored rectangles), then writes a professional English analysis with four sections —
  Overall Bias, Trend, Indicators, Key Levels & Zones — formatted as a two-column
  LAE Dark Theme HTML page ready for the portal. Always use this skill when a chart
  screenshot is provided alongside a request for analysis.
---

# Technical Analysis Skill

Generates a professional, portal-ready Technical Analysis report from a single TradingView
chart screenshot. Claude reads and interprets the chart visually — no external data needed.

## Input

| Input | Required | Notes |
|-------|----------|-------|
| Screenshot path | Yes | TradingView chart with active indicators and marked zones |
| Asset name | Optional | Provide if ticker is not clearly visible in chart |
| Timeframe | Optional | Provide if timeframe label is not visible in chart |

---

## Indicator Color Legend

Mike's fixed TradingView setup — every chart uses the same conventions:

| Element | Color in chart | Interpretation |
|---------|---------------|----------------|
| **SMA 200** | Purple | Long-term trend baseline. Price above = bullish, below = bearish. |
| **BB Mid Band** | Light blue | Bollinger Band mean (22-SMA) |
| **BB Upper Band** | Light red | Upper bound — expansion / overbought |
| **BB Lower Band** | Light green | Lower bound — expansion / oversold |
| **Long AVWAP** | Green line | Anchored VWAP from a low — buyer-anchored, dynamic support |
| **Short AVWAP** | Red line | Anchored VWAP from a high — seller-anchored, dynamic resistance |
| **Support / Resistance** | Orange line (Line-on-Close) | Horizontal key level |
| **GAP Up** | Light green rectangle | Open upward price gap |
| **GAP Down** | Light red rectangle | Open downward price gap |

**AVWAP clusters:** Multiple green AVWAPs close together = strong support cluster.
Multiple red AVWAPs close together = strong resistance cluster.

**Reading AVWAP prices:** AVWAP values are labeled directly on the price axis (right side of chart)
in the same color as the line (green for Long, red for Short). Always read from the axis label,
not from the indicator header at the top-left (which shows BB and SMA values, not AVWAPs).

---

## Workflow

### Step 1 — Read the Screenshot

Use the `Read` tool to load the image from the provided path. Study it carefully.

Identify:
- **Asset & exchange**: e.g. CME:ES1!, NASDAQ:NVDA
- **Timeframe**: Daily, 4H, 1H, 15m, etc.
- **Current price**: Read from the price axis on the right side (symbol info label)

### Step 2 — Analyze the Chart

Work through each block in order:

**Overall Bias:**
Weigh all visible signals and commit to one: **Bullish**, **Neutral**, or **Bearish**.
Let it reflect the full picture — not just one indicator.

**Trend (SMA 200 — purple line):**
- Is price above or below the SMA 200?
- Is the SMA sloping up (bullish), flat (neutral), or down (bearish)?
- Estimate the rough % distance between current price and the SMA 200

**Bollinger Bands (light blue mid / light red upper / light green lower):**
- Where is price within the bands — near upper, mid, or lower?
- Are bands expanding (trend/breakout mode) or contracting (squeeze)?
- Note: BB values are NOT support or resistance levels — never list them in Key Levels & Zones.
  BB values appear in the indicator label at the top-left; do not confuse with orange lines on the chart.

**Volume:**
- Are recent bars above or below average?
- Any climax bars (unusually large spikes near a high or low)?
- Does volume confirm or diverge from the price move?

**Gaps — only if rectangles are visible:**
Only analyze gaps if light green (Gap Up) or light red (Gap Down) rectangles are drawn in the chart.
If no rectangles are present, skip the Gaps sub-section entirely.

**Key Levels & Zones:**
- Read the current price from the price axis first
- **Orange lines** are the only Support/Resistance levels:
  - Current price **above** orange line → **Support**
  - Current price **below** orange line → **Resistance**
  - Current price is NOT a level — do not list it
- **AVWAPs**: read their exact prices from the axis labels (right side of chart)
  - Green = Long AVWAP (dynamic support)
  - Red = Short AVWAP (dynamic resistance)
- **SMA 200** is always included as the trend baseline

### Step 3 — Generate the HTML Report

Fill in `skills/technical-analysis/generate.js` with all analysis content, then run it.
The script base64-encodes the screenshot and writes a self-contained HTML file.
It also **automatically updates `dashboard-data.json`** — no manual step needed.

**Claude derives these CONFIG fields automatically — never ask Mike:**
- `DATE_ISO` → convert DATE to ISO format: "May 14, 2026" → "2026-05-14"
- `TEASER` → one plain-text sentence summarising bias + key signal, ~150 chars, no HTML tags

```bash
node skills/technical-analysis/generate.js
```

Output: `outputs/technical-analysis/lae-ta-{ASSET}-{YYYY-MM-DD}.html`

Then open the file in the browser:
```bash
start "" "outputs\technical-analysis\lae-ta-{ASSET}-{YYYY-MM-DD}.html"
```

---

## generate.js Template

Overwrite `skills/technical-analysis/generate.js` with this template, filling in all
`/* FILL IN */` placeholders with the analysis content:

```js
const fs = require('fs');
const path = require('path');

// ── CONFIG ────────────────────────────────────────────────────────
const SCREENSHOT = /* FILL IN: path to screenshot */
  path.join(__dirname, 'Tradingview Screenshots', 'ASSET_YYYY-MM-DD_HH-MM-SS.png');

const ASSET     = /* FILL IN: e.g. */ 'ES1! · S&P 500 E-Mini';
const TIMEFRAME = /* FILL IN: e.g. */ 'Daily (1D)';
const EXCHANGE  = /* FILL IN: e.g. */ 'CME';
const DATE      = /* FILL IN: e.g. */ 'May 14, 2026';
const DATE_ISO  = /* FILL IN: derived from DATE */ '2026-05-14';
const OUTPUT    = /* FILL IN: */
  path.join(__dirname, '../../outputs/technical-analysis/lae-ta-ASSET-YYYY-MM-DD.html');

// One-liner for dashboard — plain text, no HTML, ~150 chars
const TEASER = /* FILL IN */ 'Asset Daily – Bias. Key signal.';

// ── ANALYSIS CONTENT ─────────────────────────────────────────────
const BIAS_TEXT = /* FILL IN: 2–3 sentences */ `
  Overall bias is <strong>Bullish</strong>. ...
`;

const TREND_TEXT = /* FILL IN: SMA 200 analysis */ `
  Price is trading <strong>above the SMA 200</strong> at ...
`;

const BB_TEXT = /* FILL IN: Bollinger Bands analysis */ `
  Bollinger Bands are in an <strong>expanding state</strong> ...
`;

const VOLUME_TEXT = /* FILL IN: Volume analysis */ `
  Volume on the breakout candles shows ...
`;

// GAPS_TEXT: null if no gap rectangles visible in chart
const GAPS_TEXT = /* FILL IN: null or string */ null;

// LEVELS: highest price to lowest
// type: 'resistance' | 'support' | 'avwap-long' | 'avwap-short' | 'sma'
const LEVELS = [
  { type: 'resistance',   label: 'Resistance',                    price: '0.00' },
  { type: 'avwap-short',  label: 'Short AVWAP · reclaimed',       price: '0.00' },
  { type: 'sma',          label: 'SMA 200 · trend baseline',      price: '0.00' },
  { type: 'support',      label: 'Support',                       price: '0.00' },
  { type: 'avwap-long',   label: 'Long AVWAP · dynamic support',  price: '0.00' },
];
// ─────────────────────────────────────────────────────────────────

const imgExt   = path.extname(SCREENSHOT).toLowerCase();
const mimeType = imgExt === '.jpg' || imgExt === '.jpeg' ? 'image/jpeg' : 'image/png';
const b64      = fs.readFileSync(SCREENSHOT).toString('base64');
const chartSrc = `data:${mimeType};base64,${b64}`;

function buildLevels(levels) {
  const colorMap = {
    resistance:    '#ff9500',
    support:       '#ff9500',
    'avwap-long':  '#4cff6e',
    'avwap-short': '#ff8c8c',
    sma:           '#b57bff',
  };
  const bgMap = {
    resistance:    'rgba(255,149,0,0.06)',
    support:       'rgba(255,149,0,0.06)',
    'avwap-long':  'rgba(57,255,20,0.05)',
    'avwap-short': 'rgba(255,68,68,0.05)',
    sma:           'rgba(181,123,255,0.05)',
  };
  const borderMap = {
    resistance:    '1px solid rgba(255,149,0,0.18)',
    support:       '1px solid rgba(255,149,0,0.18)',
    'avwap-long':  '1px solid rgba(57,255,20,0.12)',
    'avwap-short': '1px solid rgba(255,68,68,0.1)',
    sma:           '1px solid rgba(181,123,255,0.15)',
  };

  const resistance = levels.filter(l => l.type === 'resistance');
  const support    = levels.filter(l => l.type === 'support');
  const dynamic    = levels.filter(l => ['avwap-long','avwap-short','sma'].includes(l.type));

  const row = l => {
    const bg     = bgMap[l.type]     ? `background:${bgMap[l.type]};` : '';
    const border = borderMap[l.type] ? `border:${borderMap[l.type]};` : '';
    return `<div class="level-row" style="${bg}${border}">
      <span class="level-label">${l.label}</span>
      <span class="level-value" style="color:${colorMap[l.type]}">${l.price}</span>
    </div>`;
  };

  let html = '';
  if (resistance.length) {
    html += `<div class="zone-label">Resistance — above current price</div>`;
    html += resistance.map(row).join('\n');
  }
  if (support.length) {
    html += `<div class="zone-label" style="margin-top:8px">Support — below current price</div>`;
    html += support.map(row).join('\n');
  }
  if (dynamic.length) {
    html += `<div class="zone-label" style="margin-top:8px">Dynamic zones</div>`;
    html += dynamic.map(row).join('\n');
  }
  return html;
}

const gapsBlock = GAPS_TEXT ? `
      <div class="indicator-block">
        <div class="indicator-title">Gaps</div>
        <p>${GAPS_TEXT}</p>
      </div>` : '';

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${ASSET} Technical Analysis – ${DATE}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#090c11; --bg2:#0d111a; --bg3:#111720;
    --green:#39ff14; --white:#f0f4f8; --gray:#7a8899;
    --border:rgba(255,255,255,0.07); --border-green:rgba(57,255,20,0.2);
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--white);font-family:"Inter",sans-serif;
       font-size:15px;line-height:1.6;}
  .page-header{padding:20px 28px 16px;border-bottom:1px solid var(--border);
    display:flex;align-items:center;gap:16px;flex-wrap:wrap;background:var(--bg);}
  .page-header h1{font-size:1.4rem;font-weight:800;color:var(--white);
    letter-spacing:-0.5px;font-family:"JetBrains Mono",monospace;}
  .header-meta{font-family:"JetBrains Mono",monospace;font-size:.75rem;
    color:var(--gray);margin-top:1px;}
  .ta-content{padding:20px 22px;display:flex;flex-direction:column;gap:16px;
    padding-bottom:28px;}
  .top-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
  .chart-panel{border-radius:16px;overflow:hidden;border:1px solid var(--border);
    background:#050709;height:100%;position:relative;cursor:zoom-in;}
  .chart-panel img{width:100%;height:100%;object-fit:contain;display:block;}
  .lightbox{display:none;position:fixed;inset:0;z-index:9999;
    background:rgba(0,0,0,0.88);backdrop-filter:blur(6px);
    align-items:center;justify-content:center;cursor:zoom-out;}
  .lightbox.open{display:flex;}
  .lightbox img{max-width:94vw;max-height:92vh;object-fit:contain;
    border-radius:12px;box-shadow:0 0 80px rgba(0,0,0,.9);cursor:default;}
  .lightbox-close{position:fixed;top:16px;right:18px;
    background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);
    border-radius:8px;color:var(--white);font-size:1.1rem;line-height:1;
    width:34px;height:34px;display:flex;align-items:center;justify-content:center;
    cursor:pointer;transition:background .15s;}
  .lightbox-close:hover{background:rgba(255,255,255,0.16);}
  .right-top{display:flex;flex-direction:column;gap:14px;height:100%;}
  .bottom-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
  .card{background:var(--bg2);border:1px solid var(--border);
    border-radius:12px;padding:18px 20px;}
  .card-title{font-size:.67rem;font-weight:700;letter-spacing:.12em;
    text-transform:uppercase;color:var(--green);
    font-family:"JetBrains Mono",monospace;margin-bottom:10px;}
  .card p{color:var(--gray);font-size:.9rem;line-height:1.75;}
  .card p+p{margin-top:8px;}
  .card strong{color:var(--white);font-weight:600;}
  .indicator-block{padding-top:13px;margin-top:13px;
    border-top:1px solid var(--border);}
  .indicator-block:first-child{padding-top:0;margin-top:0;border-top:none;}
  .indicator-title{font-size:.7rem;font-weight:700;
    font-family:"JetBrains Mono",monospace;color:var(--white);
    margin-bottom:7px;text-transform:uppercase;letter-spacing:.07em;opacity:.8;}
  .levels-list{display:flex;flex-direction:column;gap:6px;margin-top:4px;}
  .level-row{display:flex;justify-content:space-between;align-items:center;
    padding:7px 11px;border-radius:7px;background:var(--bg3);gap:12px;}
  .level-label{font-size:.78rem;color:var(--gray);}
  .level-value{font-family:"JetBrains Mono",monospace;font-size:.82rem;
    font-weight:700;white-space:nowrap;}
  .zone-label{font-size:.65rem;font-family:"JetBrains Mono",monospace;
    color:var(--gray);letter-spacing:.1em;text-transform:uppercase;
    padding:4px 0 2px;opacity:.55;}
  .footer{text-align:center;font-size:11px;color:var(--gray);
    font-family:"JetBrains Mono",monospace;padding:12px 22px 20px;}
  .footer span{color:var(--green);}
  @media(max-width:900px){
    .top-row,.bottom-row{grid-template-columns:1fr;}
  }
</style>
</head>
<body>
<header class="page-header">
  <div>
    <h1>${ASSET}</h1>
    <div class="header-meta">${TIMEFRAME} &nbsp;·&nbsp; ${EXCHANGE} &nbsp;·&nbsp; ${DATE}</div>
  </div>
</header>
<div class="ta-content">
  <div class="top-row">
    <div class="chart-panel" onclick="openLightbox()">
      <img src="${chartSrc}" alt="${ASSET} Chart">
    </div>
    <div class="right-top">
      <div class="card">
        <div class="card-title">Overall Bias</div>
        <p>${BIAS_TEXT}</p>
      </div>
      <div class="card">
        <div class="card-title">Trend</div>
        <p>${TREND_TEXT}</p>
      </div>
    </div>
  </div>
  <div class="bottom-row">
    <div class="card">
      <div class="card-title">Indicators</div>
      <div class="indicator-block">
        <div class="indicator-title">Bollinger Bands</div>
        <p>${BB_TEXT}</p>
      </div>
      <div class="indicator-block">
        <div class="indicator-title">Volume</div>
        <p>${VOLUME_TEXT}</p>
      </div>${gapsBlock}
    </div>
    <div class="card">
      <div class="card-title">Key Levels &amp; Zones</div>
      <div class="levels-list">
        ${buildLevels(LEVELS)}
      </div>
    </div>
  </div>
</div>
<div class="footer">
  <span>LAE Market Services</span> &middot; Learn. Analyze. Execute.
</div>
<div class="lightbox" id="lightbox" onclick="closeLightbox(event)">
  <img src="${chartSrc}" alt="${ASSET} Chart fullscreen">
  <button class="lightbox-close" onclick="closeLightbox()">✕</button>
</div>
<script>
  function openLightbox() {
    document.getElementById('lightbox').classList.add('open');
    window.parent.postMessage({ type: 'ta-zoom-open' }, '*');
  }
  function closeLightbox(e) {
    if (!e || e.target !== e.currentTarget.querySelector('img')) {
      document.getElementById('lightbox').classList.remove('open');
      window.parent.postMessage({ type: 'ta-zoom-close' }, '*');
    }
  }
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      document.getElementById('lightbox').classList.remove('open');
      window.parent.postMessage({ type: 'ta-zoom-close' }, '*');
    }
  });
  function reportHeight() {
    const h = Math.max(
      document.body.scrollHeight,
      document.body.offsetHeight,
      document.documentElement.scrollHeight
    );
    window.parent.postMessage({ frameHeight: h }, '*');
  }
  window.addEventListener('load', reportHeight);
  new ResizeObserver(reportHeight).observe(document.body);
</script>
</body>
</html>`;

const outDir = path.dirname(OUTPUT);
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(OUTPUT, html, 'utf8');
console.log('Saved:', OUTPUT);
console.log('Size:', Math.round(fs.statSync(OUTPUT).size / 1024), 'KB');

// ── Dashboard-Data aktualisieren ──────────────────────────────────
const dashPath = path.join(__dirname, '../../outputs/portal/dashboard-data.json');
let dash = {};
try { dash = JSON.parse(fs.readFileSync(dashPath, 'utf8')); } catch(_) {}
const newEntry = {
  type:   'Technical Analysis',
  title:  `Technical Analysis · ${ASSET}`,
  teaser: TEASER,
  link:   './products/technical-analysis.html',
  date:   DATE_ISO,
};
dash.updates = [newEntry, ...(dash.updates || []).filter(u => !(u.type === 'Technical Analysis' && u.title === newEntry.title))];
fs.writeFileSync(dashPath, JSON.stringify(dash, null, 2), 'utf8');
console.log('Dashboard updated.');
```

---

## Key Rules (summary)

| Rule | Detail |
|------|--------|
| **BB ≠ Level** | BB values never appear in Key Levels & Zones |
| **Current Price ≠ Level** | Never listed in Key Levels & Zones |
| **Orange lines** | Support if price above, Resistance if price below — shown in orange (`#ff9500`) |
| **AVWAP prices** | Read from price axis labels (right side), not from indicator header |
| **Gaps** | Only mention if colored rectangles are drawn in the chart |
| **No bias badge** | Bias appears only in the Overall Bias card, not in the page header |
| **Language** | English — direct, professional, no hedging |
| **Script** | Node.js (`generate.js`) — Python not required |

---

## Writing Tone

- English, direct, professional — like a seasoned trader briefing a client
- Use precise price values: "support at 7,421" not "there is some support"
- Each section: 2–4 sentences — concise, no padding
- Commit to a reading — no "seems like" or "possibly"

## After Saving

1. Open HTML in browser: `start "" "outputs\technical-analysis\lae-ta-{ASSET}-{YYYY-MM-DD}.html"`
2. Add a new `<option>` entry to the archive dropdown of the **asset-specific portal page**
   (`outputs/portal/products/technical-analysis-{ASSET_SLUG}.html`) between the
   `ARCHIV-START` and `ARCHIV-ENDE` comments:
   `<option value="../../technical-analysis/lae-ta-{ASSET}-{DATE_ISO}.html">{ASSET_SHORT} · {DATE}</option>`
   - ES1! → `technical-analysis-ES1.html`
   - CL1! → `technical-analysis-CL1.html`
   - TSLA → `technical-analysis-TSLA.html`
   - New asset: create a new asset page and add a tile to the hub (`technical-analysis.html`)
3. Update the asset tile in the hub page (`outputs/portal/products/technical-analysis.html`):
   - Set `asset-tile-date` to the new date (e.g. `Latest: May 18, 2026`)
   - Set `asset-tile-teaser` to the TEASER value from the report config
4. Confirm to Mike that report, dashboard, asset archive and hub tile are all updated
