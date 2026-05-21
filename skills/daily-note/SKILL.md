# Daily Note Skill

## Zweck
Pre-Market Sentiment-Dashboard mit interaktiven Signalzeigern und KI-Narrativ.
Generiert täglich Mo–Fr um 08:30 CEST (06:30 UTC) automatisch via GitHub Actions.

## Ausgabe
- `outputs/daily-note/Daily_Note_YYYY-MM-DD.html` – Standalone HTML
- `outputs/portal/products/daily-note.html` – Portal-Viewer (Archive-Dropdown)
- `outputs/portal/dashboard-data.json` – Dashboard-Update-Eintrag

## Inhalte

### Signal-Indikatoren (Vortagsschlusskurse)
| Indikator | Quelle | Beschreibung |
|-----------|--------|-------------|
| VIX | Finnhub `^VIX` | CBOE Volatility Index. Zonen: <15 Low · 15–25 Elevated · >25 High |
| Fear & Greed | CNN API | 0–25 Extreme Fear · 26–45 Fear · 46–55 Neutral · 56–75 Greed · 76–100 Extreme Greed |
| Expected Move | Berechnung aus VIX + SPX | SPX × (VIX/100) / √252 → Punkte, Prozent, heutige Range |

### KI-Narrativ (Gemini)
Drei strukturierte Abschnitte:
1. **Yesterday** – Marktstimmung des Vortages aus Indikatoren ablesen
2. **Current Sentiment** – VIX, F&G und Expected Move gemeinsam interpretieren
3. **Today's Outlook** – Was Trader heute beobachten sollten; 3-Sterne-Events einbeziehen

## Ausführen
```bash
python skills/daily-note/generate.py
```

## Benötigte Secrets
- `FINNHUB_API_KEY`
- `GEMINI_API_KEY`
