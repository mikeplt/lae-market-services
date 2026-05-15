const fs = require('fs');
const path = require('path');

// ── CONFIG ────────────────────────────────────────────────────────
const SCREENSHOT = path.join(__dirname, 'Tradingview Screenshots', 'CL1!_2026-05-15_11-16-31.png');

const ASSET     = 'CL1! · Crude Oil Future';
const TIMEFRAME = 'Daily (1D)';
const EXCHANGE  = 'NYMEX';
const DATE      = 'May 15, 2026';
const DATE_ISO  = '2026-05-15';
const OUTPUT    = path.join(__dirname, '../../outputs/technical-analysis/lae-ta-CL1-2026-05-15.html');

// One-liner for the dashboard Updates section (no HTML tags)
const TEASER = 'Crude Oil Daily – Neutral bias. Price at 100.29, pressing resistance at 102.13. Bounced from 84 lows; clean break needed to turn bullish.';

// ── ANALYSIS CONTENT ─────────────────────────────────────────────
const BIAS_TEXT = `
  <strong>Neutral.</strong> Crude Oil has staged a solid recovery from the April correction low
  near <strong>84</strong>, reclaiming the 90.48 support level and pushing back toward the
  100 handle. However, two overhead resistance levels at <strong>102.13</strong> and
  <strong>105.24</strong> are capping upside. A clean daily close above 102.13 would shift
  the bias to Bullish; a reversal back below 93.26 (BB mid) would signal renewed downside pressure.
`;

const TREND_TEXT = `
  Price is trading <strong>well above the SMA 200</strong> (purple) at <strong>62.18</strong>,
  sitting approximately <strong>+61.3% above</strong> the long-term average — a direct legacy
  of the February–March spike. The SMA 200 is sloping upward and provides no actionable
  short-term reference at current prices. The extreme separation confirms the long-term
  structural trend is bullish, but mean-reversion risk remains elevated.
`;

const BB_TEXT = `
  Bands remain in an <strong>expanded state</strong> (upper: 105.68 / mid: 93.26 /
  lower: 80.84), reflecting the high volatility generated during the March–April period.
  Price at <strong>100.29</strong> is positioned in the upper half of the bands, between
  the mid and the upper band. The upper band at 105.68 aligns closely with the 105.24
  resistance level, forming a confluent ceiling. Bands show early signs of contraction —
  a squeeze breakout in either direction is possible.
`;

const VOLUME_TEXT = `
  Volume spiked to extreme levels during the February–March rally, providing strong
  institutional confirmation of the move. Current volume at <strong>33.55K</strong> has
  normalized well below the spike peaks. The April recovery from the lows was accompanied
  by declining volume — a mild divergence that warrants caution. No climax bars visible
  in recent sessions.
`;

// Set to null if no gap rectangles are visible in the chart
const GAPS_TEXT = null;

// ── KEY LEVELS ───────────────────────────────────────────────────
// List from highest price to lowest.
// type: 'resistance' | 'support' | 'avwap-long' | 'avwap-short' | 'sma'
const LEVELS = [
  { type: 'resistance',  label: 'Resistance',                       price: '105.24' },
  { type: 'resistance',  label: 'Resistance',                       price: '102.13' },
  { type: 'support',     label: 'Support',                          price: '90.48'  },
  { type: 'avwap-long',  label: 'Long AVWAP · dynamic support',     price: '85.43'  },
  { type: 'sma',         label: 'SMA 200 · trend baseline',         price: '62.18'  },
];

// ─────────────────────────────────────────────────────────────────
// DO NOT EDIT BELOW THIS LINE
// ─────────────────────────────────────────────────────────────────

const imgExt   = path.extname(SCREENSHOT).toLowerCase();
const mimeType = (imgExt === '.jpg' || imgExt === '.jpeg') ? 'image/jpeg' : 'image/png';
const b64      = fs.readFileSync(SCREENSHOT).toString('base64');
const chartSrc = `data:${mimeType};base64,${b64}`;

const colorMap = {
  resistance:    '#ff9500',
  support:       '#ff9500',
  'avwap-long':  '#4cff6e',
  'avwap-short': '#ff8c8c',
  sma:           '#b57bff',
};
const styleMap = {
  resistance:    'background:rgba(255,149,0,0.06);border:1px solid rgba(255,149,0,0.18);',
  support:       'background:rgba(255,149,0,0.06);border:1px solid rgba(255,149,0,0.18);',
  'avwap-long':  'background:rgba(57,255,20,0.05);border:1px solid rgba(57,255,20,0.12);',
  'avwap-short': 'background:rgba(255,68,68,0.05);border:1px solid rgba(255,68,68,0.1);',
  sma:           'background:rgba(181,123,255,0.05);border:1px solid rgba(181,123,255,0.15);',
};

function buildLevels(levels) {
  const row = l =>
    `<div class="level-row" style="${styleMap[l.type]}">
      <span class="level-label">${l.label}</span>
      <span class="level-value" style="color:${colorMap[l.type]}">${l.price}</span>
    </div>`;

  const resistance = levels.filter(l => l.type === 'resistance');
  const support    = levels.filter(l => l.type === 'support');
  const dynamic    = levels.filter(l => ['avwap-long','avwap-short','sma'].includes(l.type));

  let html = '';
  if (resistance.length) {
    html += `<div class="zone-label">Resistance — above current price</div>\n`;
    html += resistance.map(row).join('\n') + '\n';
  }
  if (support.length) {
    html += `<div class="zone-label" style="margin-top:8px">Support — below current price</div>\n`;
    html += support.map(row).join('\n') + '\n';
  }
  if (dynamic.length) {
    html += `<div class="zone-label" style="margin-top:8px">Dynamic zones</div>\n`;
    html += dynamic.map(row).join('\n') + '\n';
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
  .lightbox{display:none;position:fixed;inset:0;z-index:999;
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
  .card.highlight{border-color:var(--border-green);
    box-shadow:0 0 28px rgba(57,255,20,.05);}
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
    <div class="lightbox" id="lightbox" onclick="closeLightbox(event)">
      <img src="${chartSrc}" alt="${ASSET} Chart – Zoom" onclick="event.stopPropagation()">
      <button class="lightbox-close" onclick="closeLightbox()">✕</button>
    </div>
    <div class="right-top">
      <div class="card">
        <div class="card-title">Overall Bias</div>
        <p>${BIAS_TEXT.trim()}</p>
      </div>
      <div class="card">
        <div class="card-title">Trend</div>
        <p>${TREND_TEXT.trim()}</p>
      </div>
    </div>
  </div>
  <div class="bottom-row">
    <div class="card">
      <div class="card-title">Indicators</div>
      <div class="indicator-block">
        <div class="indicator-title">Bollinger Bands</div>
        <p>${BB_TEXT.trim()}</p>
      </div>
      <div class="indicator-block">
        <div class="indicator-title">Volume</div>
        <p>${VOLUME_TEXT.trim()}</p>
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
<script>
  function openLightbox() {
    document.getElementById('lightbox').classList.add('open');
  }
  function closeLightbox(e) {
    if (!e || e.target !== e.currentTarget.querySelector('img')) {
      document.getElementById('lightbox').classList.remove('open');
    }
  }
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') document.getElementById('lightbox').classList.remove('open');
  });
  function reportHeight() {
    const h = Math.max(
      document.body.scrollHeight,
      document.body.offsetHeight,
      document.documentElement.scrollHeight,
      document.documentElement.offsetHeight
    );
    parent.postMessage({ frameHeight: h }, '*');
  }
  window.addEventListener('load', function() {
    reportHeight();
    setTimeout(reportHeight, 300);
  });
  new ResizeObserver(reportHeight).observe(document.body);
</script>
</body>
</html>`;

const outDir = path.dirname(OUTPUT);
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(OUTPUT, html, 'utf8');
console.log('Saved:', OUTPUT);
console.log('Size:', Math.round(fs.statSync(OUTPUT).size / 1024), 'KB');

// ── AUTO-UPDATE dashboard-data.json ──────────────────────────────
const dashboardPath = path.join(__dirname, '../../outputs/portal/dashboard-data.json');
if (fs.existsSync(dashboardPath)) {
  const dashboard = JSON.parse(fs.readFileSync(dashboardPath, 'utf8'));
  const newEntry = {
    type:   'Technical Analysis',
    title:  `Technical Analysis · ${ASSET} · ${DATE}`,
    teaser: TEASER,
    link:   './products/technical-analysis.html',
    date:   DATE_ISO,
  };
  // Remove any existing entry for this exact date+type to avoid duplicates
  dashboard.updates = dashboard.updates.filter(
    u => !(u.type === 'Technical Analysis' && u.date === DATE_ISO)
  );
  dashboard.updates.unshift(newEntry);
  fs.writeFileSync(dashboardPath, JSON.stringify(dashboard, null, 2), 'utf8');
  console.log('Dashboard updated:', dashboardPath);
}
