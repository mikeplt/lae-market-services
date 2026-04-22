"""
LAE Market Services – Weekly Note Data Fetcher
Ruft alle Marktdaten automatisch ab und gibt sie im generate.py-Format zurück.
"""

import os
import math
from datetime import datetime, timedelta

import yfinance as yf
from google import genai


# ── Konfiguration ─────────────────────────────────────────────────────────────

INDEX_TICKERS = {
    "sp500":   ("^GSPC",   "S&P 500"),
    "nasdaq":  ("^IXIC",   "Nasdaq"),
    "dow":     ("^DJI",    "Dow"),
    "russell": ("^RUT",    "Russell"),
}

SECTOR_ETFS = {
    "XLK":  "Technologie",
    "XLE":  "Energie",
    "XLF":  "Finanzen",
    "XLY":  "Konsum Zyklisch",
    "XLP":  "Konsum Defensiv",
    "XLV":  "Gesundheit",
    "XLU":  "Versorger",
    "XLB":  "Materialien",
    "XLI":  "Industrie",
    "XLRE": "Immobilien",
}

FUTURES = {
    "es": ("ES=F",  "ES (S&P Futures)"),
    "nq": ("NQ=F",  "NQ (Nasdaq Futures)"),
}

TOP_EARNINGS_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "BRK-B",
    "JPM", "UNH", "V", "XOM", "JNJ", "PG", "MA", "HD", "COST", "LLY",
    "AVGO", "ABBV", "MRK", "KO", "PEP", "ADBE", "CRM", "AMD", "ORCL",
    "CSCO", "IBM", "INTC", "NOW", "QCOM", "TXN", "AMAT", "MU", "LRCX",
    "GS", "MS", "BAC", "WFC", "C", "SPY", "QQQ",
]


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _pct(new_val: float, old_val: float) -> str:
    if old_val == 0:
        return "n/a"
    pct = (new_val - old_val) / old_val * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def _woche_start_ende() -> tuple[datetime, datetime]:
    """Gibt Start und Ende der vergangenen Handelswoche zurück (Mo–Fr)."""
    today = datetime.now()
    weekday = today.weekday()  # 0=Mo, 6=So
    # Letzten Freitag finden
    days_since_friday = (weekday - 4) % 7
    last_friday = today - timedelta(days=days_since_friday)
    last_monday = last_friday - timedelta(days=4)
    return last_monday, last_friday


def _next_week_range() -> tuple[datetime, datetime]:
    """Nächste Handelswoche Mo–Fr."""
    today = datetime.now()
    weekday = today.weekday()
    days_until_monday = (7 - weekday) % 7 or 7
    next_monday = today + timedelta(days=days_until_monday)
    next_friday = next_monday + timedelta(days=4)
    return next_monday, next_friday


def _format_level(val: float, ticker: str) -> str:
    """Formatiert Preisniveaus passend zur Größenordnung."""
    if val >= 10000:
        return f"{val:,.0f}"
    if val >= 1000:
        return f"{val:,.0f}"
    return f"{val:,.2f}"


# ── Indexperformance ──────────────────────────────────────────────────────────

def get_index_performance() -> dict:
    """Wöchentliche Performance der vier Hauptindizes."""
    result = {}
    _, last_fri = _woche_start_ende()

    # 10 Tage Puffer für Handelstage
    start = (last_fri - timedelta(days=10)).strftime("%Y-%m-%d")
    end   = (last_fri + timedelta(days=1)).strftime("%Y-%m-%d")

    for key, (ticker, name) in INDEX_TICKERS.items():
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                result[key] = {"name": name, "woche": "n/a", "positiv": True}
                continue
            # Letzter und vorletzter Wochenschluss
            close_now  = float(df["Close"].iloc[-1])
            close_prev = float(df["Close"].iloc[-6]) if len(df) >= 6 else float(df["Close"].iloc[0])
            perf = _pct(close_now, close_prev)
            result[key] = {
                "name":    name,
                "woche":   perf,
                "positiv": close_now >= close_prev,
            }
        except Exception:
            result[key] = {"name": name, "woche": "n/a", "positiv": True}

    return result


# ── Sektorperformance ─────────────────────────────────────────────────────────

def get_sector_performance() -> tuple[list, list]:
    """Gibt Top-2 und Flop-2 Sektoren der letzten Woche zurück."""
    _, last_fri = _woche_start_ende()
    start = (last_fri - timedelta(days=10)).strftime("%Y-%m-%d")
    end   = (last_fri + timedelta(days=1)).strftime("%Y-%m-%d")

    performances = []
    for etf, name in SECTOR_ETFS.items():
        try:
            df = yf.download(etf, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                continue
            close_now  = float(df["Close"].iloc[-1])
            close_prev = float(df["Close"].iloc[-6]) if len(df) >= 6 else float(df["Close"].iloc[0])
            pct = (close_now - close_prev) / close_prev * 100
            sign = "+" if pct >= 0 else ""
            performances.append({
                "name":    name,
                "kuerzel": etf,
                "perf":    f"{sign}{pct:.1f}%",
                "pct":     pct,
            })
        except Exception:
            continue

    performances.sort(key=lambda x: x["pct"], reverse=True)
    top  = [{"name": s["name"], "kuerzel": s["kuerzel"], "perf": s["perf"]} for s in performances[:2]]
    flop = [{"name": s["name"], "kuerzel": s["kuerzel"], "perf": s["perf"]} for s in performances[-2:]]
    return top, flop


# ── Technische Niveaus ────────────────────────────────────────────────────────

def get_technical_levels() -> dict:
    """Berechnet Bias, Support und Resistance für ES und NQ aus Preishistorie."""
    result = {}
    end_dt   = datetime.now()
    start_dt = end_dt - timedelta(days=60)

    for key, (ticker, label) in FUTURES.items():
        try:
            df = yf.download(
                ticker,
                start=start_dt.strftime("%Y-%m-%d"),
                end=(end_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True,
            )
            if df.empty or len(df) < 10:
                result[key] = {"bias": "n/a", "support": "n/a", "resistance": "n/a"}
                continue

            close = df["Close"]
            low   = df["Low"]
            high  = df["High"]

            current = float(close.iloc[-1])
            ma20    = float(close.rolling(20).mean().iloc[-1])

            # Support: niedrigstes Tief der letzten 14 Tage
            support = float(low.iloc[-14:].min())
            # Resistance: höchstes Hoch der letzten 14 Tage
            resistance = float(high.iloc[-14:].max())

            bias = "Aufwärtstrend" if current > ma20 else "Abwärtstrend"

            result[key] = {
                "bias":       bias,
                "support":    _format_level(support, ticker),
                "resistance": _format_level(resistance, ticker),
            }
        except Exception:
            result[key] = {"bias": "n/a", "support": "n/a", "resistance": "n/a"}

    return result


# ── Earnings Kalender ─────────────────────────────────────────────────────────

_DAY_DE = {0: "Mo", 1: "Di", 2: "Mi", 3: "Do", 4: "Fr", 5: "Sa", 6: "So"}
_MONATE = {1:"Jan",2:"Feb",3:"Mär",4:"Apr",5:"Mai",6:"Jun",
           7:"Jul",8:"Aug",9:"Sep",10:"Okt",11:"Nov",12:"Dez"}


def get_earnings_calendar() -> list:
    """Findet Earnings-Termine für die nächste Woche aus einer Top-Ticker-Liste."""
    next_mon, next_fri = _next_week_range()
    earnings_next_week = []

    for symbol in TOP_EARNINGS_TICKERS:
        try:
            t = yf.Ticker(symbol)
            cal = t.calendar
            if cal is None:
                continue

            # yfinance gibt calendar als dict zurück
            dates = cal.get("Earnings Date", [])
            if not dates:
                continue

            # Erster Earnings-Termin
            if hasattr(dates, "__iter__") and not isinstance(dates, str):
                date_list = list(dates)
            else:
                date_list = [dates]

            for ed in date_list:
                if ed is None:
                    continue
                # Zu datetime konvertieren
                if hasattr(ed, "date"):
                    ed_date = ed.date() if hasattr(ed, "date") else ed
                else:
                    try:
                        ed_date = datetime.strptime(str(ed)[:10], "%Y-%m-%d").date()
                    except Exception:
                        continue

                if next_mon.date() <= ed_date <= next_fri.date():
                    # EPS-Schätzung holen
                    eps_erw = cal.get("Earnings Average", "n/a")
                    eps_low = cal.get("Earnings Low", "")
                    eps_high = cal.get("Earnings High", "")

                    if isinstance(eps_erw, (int, float)) and not math.isnan(float(eps_erw)):
                        eps_str = f"{float(eps_erw):.2f}"
                    else:
                        eps_str = "n/a"

                    # BMO / AMC heuristisch (ohne offizielle Quelle immer "TBC")
                    zeit = "n/a"

                    earnings_next_week.append({
                        "ticker":  symbol,
                        "name":    t.info.get("shortName", symbol) if hasattr(t, "info") else symbol,
                        "tag":     _DAY_DE.get(ed_date.weekday(), "?"),
                        "zeit":    zeit,
                        "eps_erw": eps_str,
                        "eps_vj":  "n/a",
                        "datum":   ed_date,
                    })
                    break  # Nur erster Termin pro Ticker
        except Exception:
            continue

    # Sortieren nach Datum, max. 5 Ergebnisse
    earnings_next_week.sort(key=lambda x: x["datum"])
    # Datum-Feld entfernen (wird im Template nicht gebraucht)
    for e in earnings_next_week:
        e.pop("datum", None)

    if not earnings_next_week:
        earnings_next_week = [{"ticker": "n/a", "name": "Keine Daten gefunden", "tag": "-", "zeit": "-", "eps_erw": "-", "eps_vj": "-"}]

    return earnings_next_week[:5]


# ── Makro-Kalender ────────────────────────────────────────────────────────────

def get_macro_calendar() -> list:
    """
    Generiert einen heuristischen Makro-Kalender für die nächste Woche.
    Basiert auf bekannten, wiederkehrenden US-Wirtschaftsdatenveröffentlichungen.
    """
    next_mon, next_fri = _next_week_range()
    events = []

    day = next_mon
    while day <= next_fri:
        wd  = day.weekday()
        dom = day.day  # Tag im Monat

        # Donnerstag: Erstanträge Arbeitslosenhilfe (immer)
        if wd == 3:
            events.append({
                "tag":     "Do",
                "event":   "Erstanträge Arbeitslosenhilfe",
                "uhrzeit": "08:30",
            })

        # Erster Freitag im Monat: Arbeitsmarktbericht (NFP)
        if wd == 4 and dom <= 7:
            events.append({
                "tag":     "Fr",
                "event":   "Arbeitsmarktbericht (NFP) – Beschäftigung & Arbeitslosenquote",
                "uhrzeit": "08:30",
            })

        # 2. Dienstag im Monat: typisch CPI
        if wd == 1 and 8 <= dom <= 14:
            events.append({
                "tag":     "Di",
                "event":   "Verbraucherpreisindex (CPI)",
                "uhrzeit": "08:30",
            })

        # 2. Mittwoch im Monat: typisch PPI oder Retail Sales
        if wd == 2 and 8 <= dom <= 15:
            events.append({
                "tag":     "Mi",
                "event":   "Erzeugerpreisindex (PPI) / Einzelhandelsumsätze",
                "uhrzeit": "08:30",
            })

        # 3. Woche Donnerstag: Philly Fed + Flash PMI (~Do/Fr)
        if wd == 3 and 15 <= dom <= 21:
            events.append({
                "tag":     "Do",
                "event":   "Philly Fed Manufacturing Index",
                "uhrzeit": "08:30",
            })
        if wd == 4 and 15 <= dom <= 21:
            events.append({
                "tag":     "Fr",
                "event":   "Flash PMI (Verarb. Gewerbe & Dienstleistungen)",
                "uhrzeit": "09:45",
            })

        day += timedelta(days=1)

    if not events:
        events.append({
            "tag":     "-",
            "event":   "Keine Hauptdaten diese Woche (prüfe Kalender)",
            "uhrzeit": "-",
        })

    return events[:5]


# ── Narrativ via Claude API ───────────────────────────────────────────────────

def generate_narrative(data: dict) -> dict:
    """Generiert Headline und Marktkommentar via Google Gemini (kostenlos)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "headline": "Wochenrückblick – bitte GEMINI_API_KEY setzen",
            "body":     "Kein API-Key gefunden. Setze die Umgebungsvariable GEMINI_API_KEY, um die automatische Narrativ-Generierung zu aktivieren.",
        }

    try:
        client = genai.Client(api_key=api_key)

        idx_lines   = "\n".join(f"  {v['name']}: {v['woche']}" for v in data["indizes"].values())
        top_lines   = ", ".join(f"{s['name']} ({s['perf']})" for s in data["sektor_top"])
        flop_lines  = ", ".join(f"{s['name']} ({s['perf']})" for s in data["sektor_flop"])
        earn_lines  = ", ".join(f"{e['ticker']} ({e['tag']})" for e in data["earnings"][:3])
        macro_lines = ", ".join(f"{m['event']} ({m['tag']})" for m in data["makro"][:3])

        prompt = f"""Du bist ein professioneller Marktanalyst für LAE Market Services.
Schreibe einen kurzen deutschen Wochenrückblick für die KW {data['kw']}.

Marktdaten der letzten Woche:
Indizes:
{idx_lines}

Beste Sektoren: {top_lines}
Schwächste Sektoren: {flop_lines}

Nächste Woche:
Earnings: {earn_lines if earn_lines else 'keine relevanten'}
Makro: {macro_lines if macro_lines else 'keine Hauptdaten'}

Erstelle:
1. Eine prägnante Headline (max. 12 Wörter, keine Anführungszeichen)
2. Einen Marktkommentar (4–5 Sätze, sachlich, professionell, auf Deutsch, Ton: direkt und klar)

Format – antworte NUR in diesem JSON-Format ohne Markdown-Blöcke:
{{"headline": "...", "body": "..."}}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )

        import json
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)
        return {
            "headline": parsed.get("headline", "Wochenrückblick"),
            "body":     parsed.get("body", ""),
        }

    except Exception as e:
        return {
            "headline": f"Wochenrückblick KW {data['kw']}",
            "body":     f"Narrativ konnte nicht generiert werden: {e}",
        }


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def fetch_all() -> dict:
    """Aggregiert alle Daten und gibt das fertige data-Dict zurück."""
    now = datetime.now()
    kw  = now.isocalendar()[1]
    monate_de = {1:"Januar",2:"Februar",3:"März",4:"April",5:"Mai",6:"Juni",
                 7:"Juli",8:"August",9:"September",10:"Oktober",11:"November",12:"Dezember"}
    datum_str = f"{now.day}. {monate_de[now.month]} {now.year}"

    print("  [1/5] Index-Performance wird abgerufen ...")
    indizes = get_index_performance()

    print("  [2/5] Sektor-Performance wird abgerufen ...")
    sektor_top, sektor_flop = get_sector_performance()

    print("  [3/5] Technische Niveaus werden berechnet ...")
    technisch = get_technical_levels()

    print("  [4/5] Earnings-Kalender wird abgerufen ...")
    earnings = get_earnings_calendar()

    print("  [5/6] Makro-Kalender wird erstellt ...")
    makro = get_macro_calendar()

    data = {
        "kw":          kw,
        "datum":       datum_str,
        "indizes":     indizes,
        "sektor_top":  sektor_top,
        "sektor_flop": sektor_flop,
        "technisch":   technisch,
        "earnings":    earnings,
        "makro":       makro,
    }

    print("  [6/6] Narrativ wird via Claude API generiert ...")
    data["narrative"] = generate_narrative(data)

    return data
