---
name: cot-report
description: >
  Generiert einen visuellen COT-Report (Commitment of Traders) für den S&P 500 E-Mini Future (ES)
  als hochwertige HTML-Seite im LAE Dark Theme. Nutze diesen Skill immer wenn der Benutzer einen
  COT-Report, COT-Analyse, Commitment of Traders, Positionierungsdaten der CFTC oder eine
  Auswertung der Futures-Positionierung für den S&P 500 anfragt – auch wenn er nur "COT" sagt
  oder fragt "wie sind die Hedgefonds positioniert?".
---

# COT Report Skill

Erstellt eine professionelle, visuelle Aufbereitung des wöchentlichen COT-Reports (TFF-Format)
für den S&P 500 E-Mini Future – optimiert für Kunden mit hohem Anspruch an Visualisierung.

## Was dieser Skill tut

1. Lädt die aktuellen TFF-Daten automatisch vom CFTC-Server herunter (CSV/ZIP)
2. Filtert die S&P 500 E-Mini Daten (letzten 52 Wochen)
3. Berechnet alle relevanten Metriken
4. Generiert eine vollständige HTML-Seite im LAE Dark Theme

## Output

**Datei:** `outputs/cot-report/lae-cot-report-YYYY-MM-DD.html`
(Datum = Veröffentlichungsdatum des Reports, also der Freitag)

## Workflow

### Schritt 1: Skript ausführen

Führe das Skript aus:

```bash
cd "C:\Users\mikep\Claude LAE Market Services"
python skills/cot-report/scripts/generate.py
```

Das Skript:
- Lädt automatisch die TFF-Daten des aktuellen + vorherigen Jahres herunter
- Filtert den S&P 500 E-Mini Future
- Berechnet alle Metriken
- Speichert den Output unter `outputs/cot-report/`

### Schritt 2: Ergebnis prüfen

Öffne die generierte HTML-Datei im Browser und bestätige dem Benutzer den Pfad.

## Metriken im Report

| Metrik | Beschreibung |
|--------|-------------|
| **Net Position** | Long minus Short für Asset Manager und Leveraged Funds |
| **WoW Change** | Wöchentliche Veränderung der Netto-Position |
| **COT Index (52W)** | Normalisierte Position: (Aktuell - Min) / (Max - Min) × 100 |
| **Open Interest** | Gesamtes offenes Interesse + wöchentliche Veränderung |

## Gruppen-Fokus (TFF)

- **Asset Manager / Institutional** → "Smart Money", institutionelle Käufer
- **Leveraged Funds** → Hedgefonds, trendfolgende Trader (oft contrarian interpretiert)
- Dealer und Other werden als Kontext angezeigt, aber nicht im Fokus

## Datenquelle

- CFTC TFF Report: `https://www.cftc.gov/files/dea/history/fin_fut_txt_{YEAR}.zip`
- Veröffentlichung: Freitags ~21:30 Uhr MEZ (15:30 ET)
- Datenbasis: Dienstag der gleichen Woche

## Fehlerbehandlung

Falls der Download fehlschlägt:
- Prüfe Internetverbindung
- CFTC-Server ist manchmal freitags nach Veröffentlichung kurzzeitig überlastet – kurz warten und neu versuchen
- Manuelle Alternative: ZIP unter der CFTC-URL herunterladen und in `reference/` ablegen; Skript erkennt lokale Datei automatisch
