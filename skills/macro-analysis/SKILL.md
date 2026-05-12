---
name: macro-analysis
description: >
  Generiert das US Macro Analysis Dashboard als hochwertige HTML-Seite im LAE Dark Theme.
  Nutze diesen Skill immer wenn der Benutzer eine Makroanalyse, einen Makro-Check, ein
  Macro Dashboard, eine Übersicht der US-Konjunkturlage oder eine Einschätzung von Inflation,
  Zinsen, Arbeitsmarkt oder GDP anfragt – auch wenn er nur "Makro" oder "wie sieht das
  Makrobild aus?" sagt.
---

# Macro Analysis Skill

Erstellt ein professionelles, vollständig automatisiertes Makroanalyse-Dashboard für US-Märkte.
Alle Daten werden automatisch geladen – kein manuelles Befüllen nötig.

## Was dieser Skill tut

1. Lädt Treasury Yields, VIX, DXY, Gold, Öl, Kupfer und S&P 500 von Yahoo Finance
2. Lädt CPI, Core CPI, Unemployment Rate und NFP von der BLS API (mit lokalem Tages-Cache)
3. Lädt Real GDP QoQ – bei vorhandenem FRED-Key live, sonst aus eingebettetem Fallback
4. Berechnet einen Macro Score (0–100) aus 9 Indikatoren mit Ampel-System
5. Bestimmt das aktuelle Makroregime (Goldilocks, Overheating, Stagflation, Rezession etc.)
6. Generiert eine analytische Textzusammenfassung mit Zusammenhängen zwischen den Indikatoren
7. Erzeugt 10 interaktive Charts (Chart.js, eingebettet) und gibt alles als HTML-Dashboard aus

## Output

**Datei:** `outputs/macro-analysis/lae-macro-analysis-YYYY-MM-DD.html`

## Workflow

### Schritt 1: Skript ausführen

```bash
cd "C:\Users\mikep\Claude LAE Market Services"
python skills/macro-analysis/generate.py
```

Optional mit FRED-Key für erweiterte Daten (Core PCE, Jobless Claims, Fed Funds Rate):

```bash
python skills/macro-analysis/generate.py --api-key DEIN_FRED_KEY
```

### Schritt 2: Ergebnis prüfen

Öffne die generierte HTML-Datei im Browser und bestätige dem Benutzer den Pfad.

---

## Indikatoren & Scoring

| Indikator | Quelle | Bullish | Neutral | Bearish |
|---|---|---|---|---|
| CPI YoY | BLS | ≤ 2.5% | 2.5–3.5% | > 3.5% |
| Core CPI YoY | BLS | ≤ 2.5% | 2.5–3.5% | > 3.5% |
| Real GDP QoQ | FRED / Fallback | ≥ 2.5% | 0–2.5% | < 0% |
| Yield Curve 10Y–3M | Yahoo Finance | > 0.05% | –0.15–0.05% | < –0.15% |
| 10Y Yield | Yahoo Finance | < 4.0% | 4.0–4.8% | > 4.8% |
| Unemployment Rate | BLS | ≤ 4.2% | 4.2–5.0% | > 5.0% |
| NFP Monthly Change | BLS | > 150k | 0–150k | < 0k |
| VIX | Yahoo Finance | ≤ 15 | 15–25 | > 25 |
| DXY | Yahoo Finance | ≤ 100 | 100–107 | > 107 |

**Score:** Bullish = 100 Punkte · Neutral = 50 · Bearish = 0 → Durchschnitt aller Indikatoren

---

## Charts im Dashboard

Alle Charts sind interaktiv (Hover, Tooltip, Range-Filter 6M / 1Y / All, Toggle-Legende).

| Chart | Beschreibung |
|---|---|
| Macro Score Gauge | Gesamtscore 0–100 mit Ampelfarben + analytischer Textzusammenfassung |
| 9 Key Metrics Karten | Jeder Indikator mit Wert, Trend-Pfeil und Signal-Badge |
| CPI & Core CPI | YoY-Entwicklung + 2%-Ziellinie |
| Real GDP QoQ | Quartalsbalken mit Farbkodierung (blau ≥ 2%, gedämpft 0–2%, rot < 0%) |
| Yield Curve (10Y–3M) | Spread-Verlauf mit Fill über/unter 0 |
| Treasury Yields | 10Y / 5Y / 3M im Vergleich |
| Non-Farm Payrolls | Monatliche Jobzuwächse als Balkendiagramm |
| Unemployment Rate | Verlauf mit Gradient-Fill |
| S&P 500 mit 200-Tage-MA | Trendvisualisierung mit Fill zwischen Kurs und MA |
| VIX | Volatilitätsindex mit farbigen Zonen (Low / Neutral / Fear) |
| DXY & Gold | Dual-Achsen-Chart |
| WTI Crude & Copper | Dual-Achsen-Chart, indexiert auf Base 100 |

---

## Datenquellen

| Quelle | Art | Limits |
|---|---|---|
| Yahoo Finance (yfinance) | Automatisch | Keine |
| BLS Public API v1 | Automatisch + Tages-Cache | 25 Anfragen/Tag ohne Key |
| FRED API | Optional (`--api-key` oder `FRED_API_KEY` Secret) | Kostenloser Key: fred.stlouisfed.org |
| Gemini API | Optional (`GEMINI_API_KEY` Secret) | Für KI-generierte Textzusammenfassung |

### BLS-Cache

Das Skript speichert BLS-Daten täglich unter:
`outputs/macro-analysis/_bls_cache_YYYY-MM-DD.json`

Bei erneutem Ausführen am gleichen Tag wird der Cache automatisch verwendet – keine erneute API-Anfrage.

Falls der Cache fehlt oder veraltet ist: Skript einfach neu ausführen.

---

## Fehlerbehandlung

| Problem | Lösung |
|---|---|
| BLS-Limit erreicht (25/Tag) | Cache vom gleichen Tag wird automatisch genutzt |
| BLS-Daten fehlen komplett | `_create_cache.py` ausführen (befüllt Cache mit realistischen Daten) |
| FRED nicht verfügbar | GDP läuft automatisch auf eingebettete Fallback-Daten zurück |
| Yahoo Finance Timeout | Skript erneut ausführen – yfinance hat automatische Retries |

### Cache manuell neu befüllen

```bash
python skills/macro-analysis/_create_cache.py
```

---

## Hinweise

- Das Dashboard wird immer mit dem heutigen Datum im Dateinamen gespeichert.
- Das Skript ist vollständig ohne FRED-Key lauffähig – alle 9 Kern-Indikatoren sind verfügbar.
- Mit FRED-Key werden zusätzlich Core PCE, Jobless Claims und Fed Funds Rate geladen (noch nicht im Scoring, aber als Chart-Ergänzung).
- Die analytische Textzusammenfassung erkennt automatisch das Makroregime und benennt Zusammenhänge zwischen Indikatoren (z.B. Stagflation, Goldilocks, Overheating).
