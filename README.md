# Wöchentlicher Aktionen-Feed für FooDex

Sammelt jeden Dienstag die Aktionen von Migros, Coop, Denner und SPAR und
veröffentlicht sie als eine JSON-Datei, die die FooDex-App lädt.

- Feed: https://hausamstiel.github.io/aktionen-feed/aktionen.json
- Status: https://hausamstiel.github.io/aktionen-feed/

## Aufbau

| Pfad | Zweck |
|---|---|
| `feed/common.py` | Datensatz `Deal`, HTTP mit Pause, Preis-/Datums-Parsing |
| `feed/categories.py` | Stichwörter → die 16 FooDex-Kategorien |
| `feed/aktionis.py` | Quelle aktionis.ch (alle vier Läden) |
| `feed/build.py` | Läuft alle Quellen, hält die letzte gute Woche je Laden, schreibt `public/` |
| `.github/workflows/feed.yml` | Zeitplan Dienstag 04:00 UTC, Hochladen nach GitHub Pages |

## Lokal ausführen

```bash
pip install -r requirements.txt
python -m feed.build
```

## Datenformat (`aktionen.json`)

```json
{
  "version": 1,
  "generatedAt": "2026-10-08T10:00:00+00:00",
  "stores": [{"id": "coop", "name": "Coop", "ok": true, "deals": 290, "source": "aktionis", "fetchedAt": "…"}],
  "deals": [{
    "id": "aktionis-1574506", "store": "coop", "title": "Frischback Baguettes 6 Stück",
    "price": 3.6, "oldPrice": 7.5, "discountPercent": 52,
    "validFrom": "2026-10-01", "validTo": "2026-10-14",
    "image": "https://…", "url": "https://www.aktionis.ch/deals/…",
    "category": "Brot & Gebäck", "source": "aktionis"
  }]
}
```

Fällt eine Quelle aus, bleibt die letzte gültige Woche des Ladens im Feed und
der Laden trägt `"ok": false` mit einer Fehlermeldung.

Es werden keine persönlichen Daten verarbeitet. Die Aktionsdaten stammen von
den öffentlichen Seiten von aktionis.ch; Rechte liegen bei den jeweiligen Läden.
