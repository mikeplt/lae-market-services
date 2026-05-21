# Skill: COT Disaggregated Report

## Trigger-Phrasen
- "COT Disaggregated", "Commodity COT", "Rohstoff-Positionierung"
- "Gold COT", "Crude Oil COT", "Natural Gas COT", "Wheat COT"
- "Producers vs. Managed Money", "CFTC Disaggregated"

## Zweck
Wöchentlicher COT-Report für vier Rohstoffmärkte basierend auf CFTC Disaggregated-Daten.
Pro Lauf werden **vier separate HTML-Dateien** generiert (eine pro Markt).

## Märkte
| Markt        | Exchange | CFTC-Bezeichnung |
|--------------|----------|------------------|
| Gold         | COMEX    | GOLD - COMMODITY EXCHANGE INC. |
| Crude Oil    | ICE      | CRUDE OIL, LIGHT SWEET-WTI - ICE FUTURES EUROPE |
| Natural Gas  | NYMEX    | NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE |
| Wheat        | CBOT     | WHEAT-SRW - CHICAGO BOARD OF TRADE |

## Trader-Kategorien
- **Producer/Merchant** (Prod_Merc_Positions_Long/Short_All): Kombinierte Gruppe aus Producers, Merchants, Processors und Users – alle physischen Marktteilnehmer die hedgen. Typischerweise netto short. COT Index misst ob sie mehr oder weniger short als üblich sind.
- **Managed Money** (M_Money_Positions_Long/Short_All): Trend-folgende Spekulanten (Hedgefonds).

## COT Index Interpretation (Rohstoffe)
- **> 70 → Bullish**: Producers weniger short als üblich → weniger Supply-Hedging
- **30–70 → Neutral**: Mittlerer Bereich
- **< 30 → Bearish**: Producers stärker short als üblich → verstärktes Supply-Hedging

## Datenquelle
CFTC Disaggregated Futures Only:
`https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip`

## Output-Dateien (pro Lauf)
```
outputs/cot-disaggregated/
  lae-cot-disaggregated-gold-YYYY-MM-DD.html
  lae-cot-disaggregated-crude-oil-YYYY-MM-DD.html
  lae-cot-disaggregated-nat-gas-YYYY-MM-DD.html
  lae-cot-disaggregated-wheat-YYYY-MM-DD.html
```

## HTML-Struktur (pro Markt)
1. **Positioning Overview** – KPI-Karten: Producers Net, MM Net, COT Index, Open Interest
2. **Historical Positioning** – 4 Charts (52 Wochen): Producers Net, MM Net, COT Index, OI
3. **Quick Overview** – 3 Insights: Sentiment, Producers vs. MM, Open Interest Trend

## Portal-Integration
Portal-Seite: `outputs/portal/products/cot-disaggregated.html`
- Markt-Tab-Leiste: Gold | Crude Oil | Natural Gas | Wheat
- Archiv-Dropdown wechselt je nach aktivem Markt
- generate.py aktualisiert automatisch Archiv und dashboard-data.json

## Workflow

### Lokal ausführen
```
python skills\cot-disaggregated\scripts\generate.py
```
oder Doppelklick auf `skills\cot-disaggregated\scripts\run_cot.bat`

### GitHub Action
Läuft automatisch jeden Freitag um 19:30 UTC (21:30 CEST).
Manuell auslösen: GitHub → Actions → "COT Report – Disaggregated" → Run workflow

## Fehlerbehandlung
- Kein Internet: ZIP-Datei manuell in `reference/` ablegen (`fut_disagg_txt_{year}.zip`)
- Markt nicht gefunden: Fehlermeldung in der Konsole, andere Märkte werden trotzdem generiert
- Portal nicht vorhanden: generate.py überspringt den Portal-Update-Schritt
