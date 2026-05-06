"""
LAE Market Services – Weekly Note Generator
Daten werden automatisch abgerufen. Ausführen:
  python skills/weekly-note/generate.py
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# data_fetcher aus gleichem Verzeichnis laden
sys.path.insert(0, str(Path(__file__).parent))
import data_fetcher


# ─────────────────────────────────────────────────────────────────────────────
# HTML-Hilfsfunktionen
# ─────────────────────────────────────────────────────────────────────────────

def index_badge(idx):
    color = "#39ff14" if idx["positiv"] else "#ff4444"
    return f'<span class="idx-val" style="color:{color}">{idx["woche"]}</span>'

def sektor_row(s, is_top):
    arrow = "↑" if is_top else "↓"
    color = "#39ff14" if is_top else "#ff4444"
    return f'<div class="sektor-row"><span style="color:{color}">{arrow} {s["name"]}</span><span class="mono" style="color:{color}">{s["perf"]}</span></div>'

def macro_asset_items(macro_assets):
    order = ["gold", "dxy", "oil", "yield10y"]
    html = ""
    for key in order:
        a = macro_assets.get(key)
        if not a:
            continue
        color = "#39ff14" if a["positiv"] else "#ff4444"
        html += (f'<div class="idx-item">'
                 f'<span class="idx-name">{a["name"]}</span>'
                 f'<span class="idx-val" style="color:{color}">{a["wow"]}</span>'
                 f'</div>')
    return html

def earnings_rows(earnings):
    rows = ""
    for e in earnings:
        rows += f"""
        <tr>
          <td class="mono green">{e['ticker']}</td>
          <td>{e['name']}</td>
          <td class="mono">{e['tag']}</td>
          <td class="mono">{e['eps_erw']}</td>
        </tr>"""
    return rows

def makro_rows(makro):
    rows = ""
    for m in makro:
        rows += f"""
        <tr>
          <td class="mono green">{m['tag']}</td>
          <td>{m['event']}</td>
          <td class="mono gray">{m['uhrzeit']} ET</td>
        </tr>"""
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# HTML generieren
# ─────────────────────────────────────────────────────────────────────────────

def generate_html(data: dict) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAE Weekly Note – CW{data['kw']}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #090c11;
    color: #f0f4f8;
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    height: fit-content;
    padding: 16px 16px 6px;
  }}

  .page {{
    width: 100%;
    max-width: 100%;
    display: grid;
    gap: 12px;
  }}

  /* HEADER */
  .header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    background: #0d111a;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
  }}
  .header-left {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .logo-text {{
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 16px;
  }}
  .logo-text .lae {{ color: #39ff14; }}
  .logo-text .ms  {{ color: #f0f4f8; }}
  .header-meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: #7a8899;
    text-align: right;
    line-height: 1.6;
  }}
  .header-meta span {{ color: #39ff14; }}

  /* GRID: 3 Spalten oben */
  .top-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
  }}

  /* KARTE */
  .card {{
    background: #0d111a;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 16px 18px;
  }}
  .card-title {{
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #7a8899;
    margin-bottom: 12px;
  }}

  /* INDEX */
  .idx-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px 14px;
  }}
  .idx-item {{ display: flex; flex-direction: column; gap: 2px; }}
  .idx-name {{ font-size: 12px; color: #7a8899; }}
  .idx-val  {{ font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 17px; }}
  /* SEKTOR */
  .sektor-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    font-size: 14px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
  }}
  .sektor-row:last-child {{ border-bottom: none; }}
  .sektor-divider {{ height: 1px; background: rgba(255,255,255,0.07); margin: 6px 0; }}

  /* NARRATIVE */
  .narrative-card {{
    border-left: 3px solid #39ff14;
  }}
  .narrative-headline {{
    font-size: 15px;
    font-weight: 700;
    color: #f0f4f8;
    margin-bottom: 8px;
    line-height: 1.4;
  }}
  .narrative-body {{
    font-size: 14px;
    color: #7a8899;
    line-height: 1.65;
  }}

  /* BOTTOM GRID */
  .bottom-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }}

  /* TABELLE */
  table {{ width: 100%; border-collapse: collapse; }}
  td {{
    padding: 6px 7px;
    font-size: 13px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    color: #f0f4f8;
    vertical-align: middle;
  }}
  tr:last-child td {{ border-bottom: none; }}
  .mono  {{ font-family: 'JetBrains Mono', monospace; }}
  .green {{ color: #39ff14; }}
  .gray  {{ color: #7a8899; }}

  /* FOOTER */
  .footer {{
    text-align: center;
    font-size: 11px;
    color: #7a8899;
    font-family: 'JetBrains Mono', monospace;
    padding: 8px;
  }}
  .footer span {{ color: #39ff14; }}
</style>
</head>
<body>
<div class="page">

  <!-- HEADER -->
  <div class="header">
    <div class="header-left">
      <svg width="28" height="28" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M30,4 L54,17 L54,43 L30,56 L6,43 L6,17 Z" fill="rgba(57,255,20,.08)" stroke="#39ff14" stroke-width="1.5"/>
        <polyline points="16,40 24,28 30,33 40,18" fill="none" stroke="#39ff14" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        <polyline points="40,25 40,18 34,21" fill="none" stroke="#39ff14" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <div class="logo-text"><span class="lae">LAE</span><span class="ms"> Market Services</span></div>
    </div>
    <div class="header-meta">
      <div>WEEKLY NOTE</div>
      <div><span>CW {data['kw']}</span> &middot; {data['datum']}</div>
    </div>
  </div>

  <!-- RÜCKBLICK: Index + Sektor + Technisch -->
  <div class="top-grid">

    <!-- Index Performance -->
    <div class="card">
      <div class="card-title">Index Performance</div>
      <div class="idx-grid">
        {"".join(f'''<div class="idx-item"><span class="idx-name">{v["name"]}</span>{index_badge(v)}</div>''' for v in data["indizes"].values())}
      </div>
    </div>

    <!-- Sektor -->
    <div class="card">
      <div class="card-title">Sectors</div>
      {"".join(sektor_row(s, True)  for s in data["sektor_top"])}
      <div class="sektor-divider"></div>
      {"".join(sektor_row(s, False) for s in data["sektor_flop"])}
    </div>

    <!-- Macro Assets -->
    <div class="card">
      <div class="card-title">Macro Assets</div>
      <div class="idx-grid">
        {macro_asset_items(data['macro_assets'])}
      </div>
    </div>

  </div>

  <!-- MARKET NARRATIVE -->
  <div class="card narrative-card">
    <div class="card-title">Market Narrative</div>
    <div class="narrative-headline">{data['narrative']['headline']}</div>
    <div class="narrative-body">{data['narrative']['body']}</div>
  </div>

  <!-- VORSCHAU: Makro + Earnings -->
  <div class="bottom-grid">

    <!-- Makro-Kalender -->
    <div class="card">
      <div class="card-title">Macro Calendar – Next Week</div>
      <table>
        {makro_rows(data['makro'])}
      </table>
    </div>

    <!-- Earnings -->
    <div class="card">
      <div class="card-title">Earnings – Next Week</div>
      <table>
        <tr style="border-bottom:1px solid rgba(255,255,255,0.07)">
          <td class="gray" style="font-size:10px">Ticker</td>
          <td class="gray" style="font-size:10px">Company</td>
          <td class="gray" style="font-size:10px">Day</td>
          <td class="gray" style="font-size:10px">EPS Est.</td>
        </tr>
        {earnings_rows(data['earnings'])}
      </table>
    </div>

  </div>

  <!-- FOOTER -->
  <div class="footer">
    <span>LAE Market Services</span> &middot; Learn. Analyze. Execute. &middot; CW {data['kw']} / {data['datum']}
  </div>

</div>
<script>
  window.addEventListener('load', function() {{
    var h = document.documentElement.scrollHeight || document.body.scrollHeight;
    window.parent.postMessage({{ frameHeight: h }}, '*');
  }});
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("LAE Weekly Note Generator")
    print("-" * 40)
    print("\nDaten werden abgerufen ...")

    data = data_fetcher.fetch_all()

    html = generate_html(data)

    # Speichern
    datum_str  = datetime.now().strftime("%Y-%m-%d")
    base_dir   = Path(__file__).parents[2]
    output_dir = base_dir / "outputs" / "weekly-note"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename    = f"Weekly_Note_CW{data['kw']}_{datum_str}.html"
    output_path = output_dir / filename
    output_path.write_text(html, encoding="utf-8")

    print(f"\n  Report:  {output_path}")
    print(f"  KW:      {data['kw']}")
    print(f"  Datum:   {data['datum']}")
    print(f"  Earnings gefunden: {len(data['earnings'])}")

    # Portal-Archiv aktualisieren
    portal_path = base_dir / "outputs" / "portal" / "products" / "weekly-note.html"
    if portal_path.exists():
        portal_html = portal_path.read_text(encoding="utf-8")
        dt = datetime.strptime(datum_str, "%Y-%m-%d")
        rel_src  = f"../../weekly-note/{filename}"
        label    = f"CW {data['kw']} · {dt.year}"
        new_item = f'              <option value="{rel_src}">{label}</option>'
        marker   = "              <!-- ARCHIV-START -->"
        if rel_src not in portal_html:
            portal_html = portal_html.replace(marker, marker + "\n" + new_item)
            portal_path.write_text(portal_html, encoding="utf-8")
            print(f"  Portal:  aktualisiert ({label})")
        else:
            print(f"  Portal:  Eintrag bereits vorhanden")


if __name__ == "__main__":
    main()
