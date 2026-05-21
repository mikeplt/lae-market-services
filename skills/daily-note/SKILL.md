# Daily Note Skill

## Zweck
Pre-Market Sentiment-Dashboard mit interaktiven Signalzeigern und KI-Narrativ.
Generiert täglich Mo–Fr um 08:30 CEST (06:30 UTC) automatisch via GitHub Actions.

## Ausgabe
- `outputs/daily-note/Daily_Note_YYYY-MM-DD.html` – Archiv-Kopie (datiert)
- `outputs/daily-note/Daily_Note_current.html` – Immer aktuelle Version (wird täglich überschrieben)
- `outputs/portal/products/daily-note.html` – Portal-Viewer (zeigt `Daily_Note_current.html` via iframe)
- `outputs/portal/dashboard-data.json` – Dashboard-Update-Eintrag

## Inhalte

### Signal-Indikatoren (Vortagsschlusskurse)
| Indikator | Quelle | Beschreibung |
|-----------|--------|-------------|
| VIX | yfinance `^VIX` | CBOE Volatility Index. Zonen: <15 Low · 15–25 Elevated · >25 High |
| SPX | yfinance `^GSPC` | S&P 500 Schlusskurs (Basis für Expected Move) |
| Fear & Greed | CNN API | 0–25 Extreme Fear · 26–45 Fear · 46–55 Neutral · 56–75 Greed · 76–100 Extreme Greed |
| Expected Move | Berechnung aus VIX + SPX | SPX × (VIX/100) / √252 → Punkte, Prozent, heutige Range |
| Macro Events | Finnhub Economic Calendar | Nur Impact = 3 (drei Sterne), nur US-Events; fließen nur in Gemini-Prompt ein |

### KI-Narrativ (Gemini `gemini-2.5-flash`)
Drei strukturierte Abschnitte auf Englisch:
1. **Yesterday** – Marktstimmung des Vortages aus Indikatoren ablesen
2. **Current Sentiment** – VIX, F&G und Expected Move gemeinsam interpretieren
3. **Today's Outlook** – Was Trader heute beobachten sollten; 3-Sterne-Events einbeziehen

## Benötigte Secrets
| Secret | Verwendet für |
|--------|--------------|
| `FINNHUB_API_KEY` | Macro Events (Economic Calendar) |
| `GEMINI_API_KEY` | KI-Narrativ |

yfinance und CNN Fear & Greed benötigen keinen API-Key.

## Ausführen
```bash
python skills/daily-note/generate.py
```

## Dateien
| Datei | Beschreibung |
|-------|-------------|
| `data_fetcher.py` | Datenabruf: yfinance (VIX/SPX), CNN F&G, Finnhub Events, Gemini Narrativ |
| `generate.py` | HTML-Generator: SVG Arc-Gauges, Expected Move Card, Narrativ-Abschnitte |
| `SKILL.md` | Diese Dokumentation |
| `.github/workflows/daily-note.yml` | Cron Mo–Fr 06:30 UTC + `workflow_dispatch` |
