---
name: earnings-analysis
description: Create a post-earnings HTML analysis report for the LAE portal. Shows actual results vs. estimates (beat/miss), which scenario from the preview played out, catalyst review, forward guidance, and outlook. Use when user requests "Earnings Analysis für [Unternehmen]", "Ergebnisse auswerten", "Post-Earnings Report", "was hat [TICKER] reported", or after earnings are published.
---

# Earnings Analysis Skill

Erstellt einen **HTML-Report** nach der Veröffentlichung von Quartalsergebnissen – als Gegenstück zum Earnings Preview.

**Kernfunktion:** Tatsächliche Ergebnisse aufbereiten, mit dem Preview vergleichen und einen Ausblick liefern.

---

## Wann verwenden

Nutze diesen Skill wenn:
- Earnings veröffentlicht wurden und ausgewertet werden sollen
- Der Nutzer fragt: „Earnings Analysis für [Unternehmen]"
- Der Nutzer fragt: „Ergebnisse von [TICKER] auswerten"
- Ein Earnings Preview bereits existiert und der Report dazu erstellt werden soll

**Nicht verwenden wenn:**
- Earnings noch nicht berichtet wurden → Earnings Preview Skill verwenden
- Nur eine schnelle Zusammenfassung gefragt ist (kein vollständiger Report nötig)

---

## Output

- **Format:** Statische HTML-Datei (selbstständig, alle CSS inline)
- **Design:** LAE Dark Theme (identisch zum Earnings Preview)
- **Zielort:** `outputs/earnings-analysis/earnings-analysis-{TICKER}-{QUARTER}.html`
- **Portal:** Eintrag unter `outputs/portal/products/earnings.html` hinzufügen (Tab „Reports")

---

## Workflow

### Schritt 1 – Daten recherchieren
Nach der Earnings-Veröffentlichung folgende Quellen prüfen:
- **Earnings Release** (Investor Relations Seite des Unternehmens)
- **10-Q / Earnings Transcript** (Seeking Alpha, SEC EDGAR)
- **Yahoo Finance / CNBC** für Kursreaktion und Konsens-Vergleich
- **Kurs vor Earnings** aus dem Preview übernehmen

### Schritt 2 – generate.py befüllen
Datei öffnen: `skills/earnings-analysis/generate.py`

Folgende Abschnitte ausfüllen:

**DATA** – Basisinformationen:
```python
DATA = {
    "DATUM":           "...",          # Analysedatum (Tag nach Earnings)
    "TICKER":          "AAPL",
    "COMPANY_NAME":    "Apple Inc.",
    "QUARTER":         "Q1 FY2026",
    "REPORT_DATE":     "...",          # Tatsächliches Berichtsdatum
    "REPORT_TIME":     "After Close",  # oder "Before Open"
    "STOCK_PREV_DATE": "...",          # Tag vor Earnings
    "STOCK_PREV":      "$ ...",        # Kurs aus dem Preview
    "STOCK_POST_DATE": "...",          # Tag nach Earnings
    "STOCK_AFTER":     "$ ...",        # Schlusskurs nach Earnings
    "STOCK_REACT":     "▲/▼ X.X%",    # Tatsächliche Reaktion
    "REACT_CLASS":     "green",        # "green" oder "red"
    "TV_IFRAME_SRC":   "...",          # TradingView Widget URL
}
```

**RESULTS** – Actual vs. Estimate (aus Yahoo Finance / Earnings Release):
```python
# (Metric, Estimate aus Preview, Actual, vs_text, vs_class, status)
RESULTS = [
    ("Revenue (total)", "$ X.XB", "$ X.XB", "▲ +$X.XB", "pos", "beat"),
    ...
]
# vs_class: "pos" | "neg" | "neutral"
# status:   "beat" | "missed" | "in-line"
```

**SCENARIO_RESULT** – Welches Szenario ist eingetreten:
```python
SCENARIO_RESULT = {
    "played_out": "bull",   # "bull" | "base" | "bear"
    "tag":        "Bull",
    "reaction":   "▲ X.X%",
    "driver":     "Kurzer Treiber-Headline",
    "revenue":    "$ X.XB",
    "eps":        "$ X.XX",
    "summary":    "Beschreibung warum dieses Szenario eingetreten ist...",
}
```

**CATALYST_RESULTS** – Hat jeder Catalyst ausgelöst:
```python
# (Nr, Title aus Preview, status, Was ist tatsächlich passiert)
# status: "triggered" | "missed" | "partial"
CATALYST_RESULTS = [
    ("01", "Catalyst-Titel", "triggered", "Was passiert ist..."),
    ...
]
```

**GUIDANCE** – Neue Forward Guidance:
```python
# (Metric, Alte Guidance, Neue Guidance, change_class)
GUIDANCE = [
    ("Revenue Q[X]", "~ $ X.XB", "$ X.X–X.XB", "pos"),
    ...
]
# change_class: "pos" | "neg" | "neutral"
```

**OUTLOOK** – 3–4 Ausblickspunkte:
```python
# (Nr, Titel, Beschreibung)
OUTLOOK = [
    ("01", "Thema 1", "Ausblick und Bedeutung..."),
    ...
]
```

### Schritt 3 – HTML generieren
```bash
cd skills/earnings-analysis
python generate.py
```
→ Output: `outputs/earnings-analysis/earnings-analysis-{TICKER}-{QUARTER}.html`

### Schritt 4 – Portal aktualisieren
In `outputs/portal/products/earnings-TICKER.html` den neuen Analysis-Eintrag **oberhalb** des zugehörigen Previews einfügen (zwischen `<!-- REPORTS-START -->` und `<!-- REPORTS-END -->`):
```html
<div class="report-row" onclick="openPreview('../../earnings-analysis/earnings-analysis-TICKER-QUARTER.html', this)">
  <div class="report-row-left">
    <div class="report-row-meta">
      <span class="type-badge analysis">Analysis</span>
      <span style="font-family:var(--font-mono);font-size:0.75rem;color:var(--green);">QUARTER</span>
    </div>
    <span class="report-row-date">[Analysedatum] · Reported: [Berichtsdatum] · [Time]</span>
  </div>
  <span class="report-row-arrow">→</span>
</div>
```

### Schritt 5 – Dashboard aktualisieren
In `outputs/portal/dashboard-data.json` einen neuen Eintrag **ganz oben** in `"updates"` einfügen:
```json
{
  "type": "Earnings",
  "title": "Earnings Analysis · TICKER QUARTER",
  "teaser": "TICKER QUARTER reported. Revenue $X.XB (Beat/Missed), Data Center $X.XB, EPS adj. $X.XX. Q2 Guidance $X.XB. Kursreaktion: [Reaktion].",
  "link": "./products/earnings-TICKER.html",
  "date": "YYYY-MM-DD"
}
```

### Schritt 6 – GitHub pushen
```bash
git add .
git commit -m "Earnings Analysis: TICKER QUARTER"
git push
```

---

## HTML-Struktur des Reports

| Sektion | Inhalt |
|---------|--------|
| **Header** | LAE Logo + „Earnings Analysis" + Datum |
| **Company Banner** | Ticker, Name, Quarter, Kurs vorher → nachher, Reaktion % |
| **Actual vs. Estimates** | Tabelle: Metric \| Estimate \| Actual \| vs. Est. \| Beat/Missed |
| **Scenario Result** | Welches Szenario eingetreten ist (Bull/Base/Bear-Card) |
| **Catalyst Review** | Jeder Catalyst: Triggered / Missed / Partial mit Beschreibung |
| **Forward Guidance** | Tabelle: Metric \| Alte Guidance \| Neue Guidance \| Änderung |
| **Chart** | TradingView Mini-Chart |
| **Ausblick** | 3–4 nummerierte Ausblickspunkte |
| **Footer** | LAE Branding |

---

## TradingView Widget URL

Gleiches Format wie im Earnings Preview:
- **NASDAQ:** `symbol=NASDAQ%3ATICKER`
- **NYSE:** `symbol=NYSE%3ATICKER`
- **DAX:** `symbol=XETR%3ATICKER`

Basis-URL:
```
https://www.tradingview.com/embed-widget/mini-symbol-overview/?symbol=NASDAQ%3AMSFT&locale=en&dateRange=12M&colorTheme=dark&trendLineColor=%2339ff14&underLineColor=rgba(57%2C255%2C20%2C0.15)&underLineBottomColor=rgba(57%2C255%2C20%2C0)&isTransparent=true&autosize=true
```

---

## Abhängigkeiten

- Python (Standardbibliothek, keine zusätzlichen Pakete nötig)
- Daten: manuell recherchieren (Yahoo Finance, Earnings Release, Transcript)
- Verwandter Skill: `earnings-preview` (Preview-Daten als Vergleichsgrundlage)
