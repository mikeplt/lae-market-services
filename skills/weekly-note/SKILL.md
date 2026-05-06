---
name: Weekly Note
description: Erstellt das wöchentliche Briefing als HTML-Dashboard für US Markets Trader. Verwende diesen Skill immer wenn der Nutzer ein Briefing, eine Note, oder ein wöchentliches Markt-Briefing erstellen möchte — unabhängig davon, ob er "weekly note" oder "briefing" explizit erwähnt. 
---

# Weekly Note

Erstellt das wöchentliche Briefing als **HTML-Datei** für US Markets Trader. Ziel: fertig vor Wochenstart (Sonntag).

**Ausgabe:** `outputs/Weekly_Note_DATUM.html`

---

## Aufbau

| Bereich | Beschreibung | Pflicht |
|---------|-------------|---------|
| **Header** | KW, Datum, LAE-Logo | ✓ |
| **Index-Performance** | S&P 500, Nasdaq, Dow, Russell 2000 – WoW % + Vorwoche (Momentum) | ✓ |
| **Sektor Top/Flop** | Top 2 / Flop 2 Sektoren – WoW % + Vorwoche (Momentum) | ✓ |
| **Market Narrative** | Headline + 3–5 Sätze – das bestimmende Marktthema | ✓ |
| **Macro Assets** | Gold, Crude Oil, US Dollar, 10Y Yield – WoW % + aktueller Kurs/Stand | ✓ |
| **Makro-Kalender** | Top 3–5 Ereignisse der kommenden Woche | ✓ |
| **Earnings** | Top 5 Schwergewichte S&P 500 / Nasdaq-100 | ✓ |

---

## Feste Quellen

| Bereich | Quelle | URL |
|---------|--------|-----|
| Index-Performance + Sektor Top/Flop | Alpha Vantage (TIME_SERIES_WEEKLY) | alphavantage.co |
| Macro Assets (Gold, Oil, Dollar, 10Y) | Alpha Vantage (TIME_SERIES_WEEKLY + TREASURY_YIELD) | alphavantage.co |
| Earnings Next Week | Alpha Vantage (EARNINGS_CALENDAR) | alphavantage.co |
| Makro-Kalender | Investing.com | investing.com/economic-calendar |
| Market Narrative | Google Gemini API | – |

---

## Daten recherchieren

### Schritt 1: Index-Performance + Sektor Top/Flop

Quelle: **Yahoo Finance** → finance.yahoo.com

**Indizes (wöchentliche % Veränderung):**
- S&P 500 (^GSPC)
- Nasdaq Composite (^IXIC)
- Dow Jones (^DJI)
- Russell 2000 (^RUT)

**Sektoren:** Top 2 Gewinner + Top 2 Verlierer der Woche
- Kürzel: XLK (Tech), XLF (Finanzen), XLE (Energie), XLV (Gesundheit), XLI (Industrie), XLC (Kommunikation), XLY (Konsum zyklisch), XLP (Konsum defensiv), XLRE (Immobilien), XLU (Versorger), XLB (Materialien)

### Schritt 2: Macro Assets

Quelle: **Alpha Vantage** (automatisch via `data_fetcher.py`)

- **Gold** (GLD ETF) – WoW % + aktueller Kurs
- **Crude Oil** (USO ETF) – WoW % + aktueller Kurs
- **US Dollar** (UUP ETF) – WoW % + aktueller Kurs
- **10Y Treasury Yield** (TREASURY_YIELD API) – WoW Veränderung in Basispunkten + aktueller Zinssatz

### Schritt 3: Earnings Current and next Week

Quelle: **Investing.com** → investing.com/earnings-calendar

- Maximal 5 Einträge – nur S&P 500 / Nasdaq-100 Schwergewichte
- Falls keine relevanten Earnings: Liste leer lassen (`[]`)
- **BMO** = Before Market Open | **AMC** = After Market Close

Pro Eintrag: Ticker · Unternehmensname · Tag + Zeit (BMO/AMC) · Erwarteter EPS · Vorjahr EPS

### Schritt 4: Makro-Kalender + Market Narrative

**Makro-Kalender:** Quelle: **Investing.com** → investing.com/economic-calendar
- Top 3–5 Ereignisse der **kommenden Woche** mit hoher Marktrelevanz (nur ★★★-Ereignisse)
- Format: Wochentag · Ereignis · Uhrzeit (ET)
- Wichtigste Events: FOMC, CPI, PPI, NFP, GDP, Retail Sales, ISM, Jobless Claims

**Market Narrative:** Quellen: **Yahoo Finance + CNBC**
- **Headline** – ein prägnanter Satz: Was war das bestimmende Thema dieser Woche?
- **Body** – 3–5 Sätze: konkrete Fakten, keine Allgemeinaussagen, kurzer Ausblick auf die kommende Woche

---

## generate.py befüllen

```python
data = {
    "kw": 17,
    "datum": "20. April 2026",
    
    # Schritt 1
    "indizes": {
        "sp500":  {"name": "S&P 500",  "woche": "+1.2%", "woche_prev": "+2.9%", "positiv": True,  "momentum_up": False},
        "nasdaq": {"name": "Nasdaq",   "woche": "+0.8%", "woche_prev": "+6.1%", "positiv": True,  "momentum_up": False},
        "dow":    {"name": "Dow",      "woche": "+0.5%", "woche_prev": "+0.6%", "positiv": True,  "momentum_up": False},
        "russell":{"name": "Russell",  "woche": "-0.3%", "woche_prev": "+8.1%", "positiv": False, "momentum_up": False},
    },
    "sektor_top":  [{"name": "Technologie", "kuerzel": "XLK", "perf": "+2.1%", "perf_prev": "+6.3%"}, {"name": "Energie", "kuerzel": "XLE", "perf": "+1.8%", "perf_prev": "-0.2%"}],
    "sektor_flop": [{"name": "Versorger",   "kuerzel": "XLU", "perf": "-1.2%", "perf_prev": "+0.5%"}, {"name": "Immobilien", "kuerzel": "XLRE", "perf": "-0.9%", "perf_prev": "+1.1%"}],

    # Schritt 2
    "macro_assets": {
        "gold":    {"name": "Gold",      "price": "189.45", "wow": "+2.3%", "positiv": True},
        "oil":     {"name": "Crude Oil", "price": "62.30",  "wow": "-2.1%", "positiv": False},
        "dxy":     {"name": "US Dollar", "price": "27.12",  "wow": "-0.8%", "positiv": False},
        "yield10y":{"name": "10Y Yield", "price": "4.38%",  "wow": "+5bp",  "positiv": True},
    },
    
    # Schritt 3
    "earnings": [
        {"ticker": "NFLX", "name": "Netflix",   "tag": "Tue", "eps_erw": "5.68"},
        {"ticker": "TSLA", "name": "Tesla",     "tag": "Thu", "eps_erw": "0.43"},
        {"ticker": "MSFT", "name": "Microsoft", "tag": "Wed", "eps_erw": "3.22"},
    ],
    
    # Schritt 4
    "makro": [
        {"tag": "Tue", "event": "Consumer Price Index (CPI)",  "uhrzeit": "08:30"},
        {"tag": "Thu", "event": "Initial Jobless Claims",      "uhrzeit": "08:30"},
        {"tag": "Fri", "event": "Retail Sales",                "uhrzeit": "08:30"},
    ],
    "narrative": {
        "headline": "Fed-Pause-Erwartungen stützen die Tech-Rally",
        "body": "Die Hoffnung auf eine baldige Zinspause der Fed trieb S&P 500 und Nasdaq auf Wochensicht ins Plus. Nvidia und Microsoft sorgten für die größten Kursgewinne im Nasdaq-100. Der Rückgang bei Versorgern und Immobilienwerten zeigt, dass Anleger weiterhin auf Wachstumswerte setzen. Kommende Woche rücken der CPI-Bericht am Dienstag und die Einzelhandelsumsätze am Freitag in den Fokus."
    }
}
```

---

## HTML erzeugen

```
python skills/weekly-note/generate.py
```

→ Datei wird gespeichert in `outputs/Weekly_Note_DATUM.html`

---

## Hinweise

- Kommuniziere auf Deutsch.
- Market Narrative immer mit konkreten Aussagen – keine Allgemeinplätze.
- Key Levels nur angeben wenn du sie selbst auf TradingView geprüft hast.
- Frage nicht ob du das Briefing erstellen sollst – führe `generate.py` direkt aus.
- Earnings: Maximal 5 Einträge, nur Schwergewichte (Marktkapitalisierung > 100 Mrd. USD).
