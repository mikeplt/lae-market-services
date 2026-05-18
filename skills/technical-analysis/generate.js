const fs = require('fs');
const path = require('path');

// ── CONFIG ────────────────────────────────────────────────────────
const SCREENSHOT =
  path.join(__dirname, 'Tradingview Screenshots', 'NVDA_2026-05-18_14-57-30.png');

const ASSET     = 'NVDA · Nvidia Corporation';
const TIMEFRAME = 'Daily (1D)';
const EXCHANGE  = 'NASDAQ';
const DATE      = 'May 18, 2026';
const DATE_ISO  = '2026-05-18';
const OUTPUT    =
  path.join(__dirname, '../../outputs/technical-analysis/lae-ta-NVDA-2026-05-18.html');

const TEASER = 'NVDA Daily – Bullish bias. Price +21.2% above SMA 200 ($185.97), all three Long AVWAPs reclaimed. Approaching resistance at $235.83 with two Gap Up zones providing structural support below.';

// ── ANALYSIS CONTENT ─────────────────────────────────────────────
const BIAS_TEXT = `
  Overall bias is <strong>Bullish</strong>. After a significant drawdown, NVDA has staged a strong
  structural recovery — price at $225.32 trades 21.2% above the SMA 200 ($185.97) and above all
  three Long AVWAPs. Momentum is clearly with buyers as price presses toward resistance at $235.83.
  The two Gap Up zones below act as structural support cushions, reducing downside risk near-term.
`;

const TREND_TEXT = `
  Price is trading <strong>above the SMA 200</strong> at $185.97, with a distance of $39.35 (+21.2%).
  The SMA 200, previously declining through the drawdown phase, is beginning to flatten and turn upward —
  a sign that the long-term trend structure is repairing. The recovery from the lows has been impulsive
  and broad, confirming sustained buyer control above the long-term average.
`;

const BB_TEXT = `
  Bollinger Bands are in an <strong>expanding state</strong>, with price pressing against the upper band.
  The expansion confirms strong directional momentum rather than a low-volatility drift. Price is
  extended relative to the mid band, which could attract short-term profit-taking near resistance —
  but in trending conditions, the upper band acts as a momentum target, not a reversal signal.
`;

const VOLUME_TEXT = `
  Volume on the recovery rally shows elevated bars on the key upside sessions, confirming institutional
  participation in the move. As price approaches the $235.83 resistance zone, watch for volume behavior
  closely — a high-volume breakout would open the path to new highs, while fading volume near resistance
  would suggest a temporary pause or consolidation before continuation.
`;

const GAPS_TEXT = `
  Two unfilled <strong>Gap Up zones</strong> (light green rectangles) are visible below current price,
  representing breakaway gaps from the recovery move. These zones form near-term structural support —
  if price pulls back to test them, buyers are likely to step in and defend. Unfilled Gap Up zones in
  a bullish trend typically resolve to the upside.
`;

// LEVELS: highest to lowest price
const LEVELS = [
  { type: 'resistance',  label: 'Resistance',                   price: '235.83' },
  { type: 'support',     label: 'Support · AVWAP confluence',   price: '216.56' },
  { type: 'avwap-long',  label: 'Long AVWAP · dynamic support', price: '216.15' },
  { type: 'avwap-long',  label: 'Long AVWAP · dynamic support', price: '199.67' },
  { type: 'support',     label: 'Support · AVWAP confluence',   price: '196.39' },
  { type: 'sma',         label: 'SMA 200 · trend baseline',     price: '185.97' },
  { type: 'avwap-long',  label: 'Long AVWAP · deep support',    price: '168.80' },
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
