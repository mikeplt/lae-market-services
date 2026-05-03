#!/usr/bin/env python3
"""Aktualisiert top_mover-Felder in outputs/portal/dashboard-data.json via yfinance."""

import json, os
from datetime import datetime
from pathlib import Path

# .env laden
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

try:
    import yfinance as yf
except ImportError:
    print("Fehler: yfinance nicht installiert. Bitte: pip install yfinance")
    raise SystemExit(1)

WATCHLIST = {
    "^GSPC": "S&P 500",
    "^NDX":  "Nasdaq 100",
    "GC=F":  "Gold",
    "CL=F":  "WTI Oil",
}

OUTPUT_JSON = Path(__file__).parent.parent / "outputs" / "portal" / "dashboard-data.json"


def main():
    print("Top Mover Update...")

    best_name, best_chg = None, 0.0

    for ticker, name in WATCHLIST.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) >= 2:
                chg = (hist["Close"].iloc[-1] / hist["Close"].iloc[-2] - 1) * 100
                print(f"  {name}: {chg:+.2f}%")
                if abs(chg) > abs(best_chg):
                    best_chg, best_name = chg, name
        except Exception as e:
            print(f"  {name}: Fehler ({e})")

    if best_name is None:
        print("Keine Daten verfügbar.")
        return

    data = {}
    if OUTPUT_JSON.exists():
        try:
            data = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass

    data["top_mover_symbol"]    = best_name
    data["top_mover_change"]    = f"{best_chg:+.1f}%"
    data["top_mover_direction"] = "up" if best_chg >= 0 else "down"
    data["updated_at"]          = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nTop Mover: {best_name} {best_chg:+.1f}%")
    print(f"Gespeichert: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
