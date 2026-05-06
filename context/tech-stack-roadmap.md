# Tech-Stack & Roadmap – LAE Market Services

## Kontext

Mike baut LAE Market Services als Kundenprodukt auf: Finanzreports, Dashboards und Marktanalysen sollen an zahlende Kunden ausgeliefert werden. Der aktuelle Stack ist rein statisch (HTML + GitHub Pages + GitHub Actions) – es gibt keine Authentifizierung, keinen Kundenzugang und keine Nutzerverwaltung.

Ziele:
- **Kundenprodukt** mit echten, individuellen Nutzerkonten (E-Mail + Passwort)
- **Vollautomatische** Inhaltsgenerierung und -aktualisierung
- Fortschritt auf **allen Fronten**: Inhalte, Stabilität, Kundenzugang

---

## Stack-Vergleich: Ist ↔ Soll

| Baustein | Referenz-Stack | LAE Ist | LAE Soll | Komplexität |
|----------|---------------|---------|----------|-------------|
| **01 Frontend** | Next.js | HTML5 + Vanilla JS | HTML5 + Vanilla JS (beibehalten) | – |
| **02 Styling** | Tailwind CSS | Custom CSS (LAE Brand) | Custom CSS (beibehalten) | – |
| **03 Backend** | Node.js | Python via GitHub Actions | Vercel Serverless Functions (wenn nötig) | Mittel |
| **04 Datenbank & Auth** | Supabase | Keines | Supabase (Zukunft) | Mittel |
| **05 Hosting** | Vercel | GitHub Pages | Vercel (Upgrade, wenn Auth benötigt) | Gering |
| **06 KI-Layer** | Claude API | Claude + Gemini API | Bleibt (bereits im Einsatz) | – |

**Begründung:** Next.js und Tailwind würden einen kompletten Rewrite aller bestehenden HTML-Seiten erfordern – zu viel Aufwand ohne direkten Nutzen für jetzt. Der Rest des Referenz-Stacks passt gut zu LAE und wird schrittweise integriert.

---

## Aktueller Stack (Ist-Zustand)

| Schicht | Technologie | Status |
|--------|-------------|--------|
| Frontend | HTML5, CSS3, Vanilla JS | ✅ Läuft |
| Hosting | GitHub Pages (statisch) | ✅ Läuft |
| Automatisierung | GitHub Actions (Cron) | ⚠️ Teilweise instabil |
| Content-Generierung | Python-Scripts + Gemini/Claude API | ✅ Läuft |
| Datenquellen | Alpha Vantage, BLS, CFTC, Yahoo Finance, TradingView | ✅ Läuft |
| Authentifizierung | Keines | ❌ Fehlt |
| Nutzerverwaltung | Keines | ❌ Fehlt |
| Zahlungsanbindung | Keines | ❌ Fehlt |

---

## Roadmap – 3 Phasen

### Phase 1: Stabilität
*Sicherstellen, dass alles Bestehende zuverlässig läuft*

- [ ] GitHub Actions Dashboard-Update debuggen und stabilisieren
- [ ] BLS-Cache-Problem im Macro-Analysis-Skill lösen
- [ ] Alle Skills auf Fehler prüfen und durchtesten
- [ ] COT-Report-Skill finalisieren
- [ ] Weekly Note Workflow validieren

### Phase 2: Hosting-Upgrade auf Vercel
*Vorbereitung für Authentifizierung – setzt Vercel voraus*

- [ ] Vercel-Konto anlegen (kostenloser Free Tier)
- [ ] Repository mit Vercel verbinden (automatisches Deployment bei Git Push)
- [ ] GitHub Actions Cron-Jobs auf Vercel umstellen oder parallel betreiben
- [ ] Domain/Subdomain konfigurieren

### Phase 3: Authentifizierung & Nutzerverwaltung (Zukunft)
*Echte Nutzerkonten in das Portal integrieren – wenn Kunden bereit sind*

- [ ] Supabase-Projekt anlegen (kostenloser Free Tier)
- [ ] Login-Seite im Portal erstellen (`outputs/portal/login.html`)
- [ ] Portal-Seiten hinter Auth-Check sichern (JS-basiert)
- [ ] Admin-Ansicht: Nutzer anlegen und verwalten
- [ ] Stripe-Integration für Abonnements (Zukunft)

---

## Kritische Dateien

| Datei | Relevanz |
|-------|----------|
| `outputs/portal/index.html` | Portal-Einstieg |
| `outputs/portal/dashboard.html` | Haupt-Dashboard |
| `outputs/portal/products/*.html` | Alle Produktseiten |
| `.github/workflows/dashboard-update.yml` | Instabiler Cron – Phase 1 Priorität |
| `scripts/update_dashboard_news.py` | News-Update-Script |
| `requirements.txt` | Python-Abhängigkeiten |

---

## Was wir NICHT tun

- Kein Rewrite auf Next.js / React – zu viel Aufwand ohne direkten Nutzen jetzt
- Kein Tailwind CSS – eigenes Design-System ist bereits etabliert
- Kein eigener Backend-Server – Vercel Serverless Functions reichen
- Keine Umsetzung in einem Rutsch – Schritt für Schritt nach Mikes Tempo
