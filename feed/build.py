"""Baut public/aktionen.json aus allen Quellen.

Ablauf je Laden: Quelle abfragen → Plausibilität (mindestens MIN_DEALS,
gültig bis heute oder später) → sonst die letzte gute Woche aus der
bestehenden Datei behalten und den Laden als „nicht aktualisiert" markieren.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from . import aktionis
from .common import STORES, Deal

log = logging.getLogger("feed")

PUBLIC = Path(__file__).resolve().parent.parent / "public"
OUTPUT = PUBLIC / "aktionen.json"
MIN_DEALS = 5
FEED_VERSION = 1

SOURCES = {
    "migros": [aktionis.fetch_store],
    "coop": [aktionis.fetch_store],
    "denner": [aktionis.fetch_store],
    "spar": [aktionis.fetch_store],
}


def load_previous() -> dict:
    if OUTPUT.exists():
        try:
            return json.loads(OUTPUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("Bestehende Datei unlesbar, wird ersetzt")
    return {}


def still_valid(deal: dict, today: date) -> bool:
    valid_to = deal.get("validTo")
    if not valid_to:
        return True
    try:
        return date.fromisoformat(valid_to) >= today
    except ValueError:
        return True


def build() -> int:
    today = date.today()
    previous = load_previous()
    previous_deals = {s: [d for d in previous.get("deals", []) if d.get("store") == s] for s in STORES}
    previous_stores = {s["id"]: s for s in previous.get("stores", [])}

    stores_out: list[dict] = []
    deals_out: list[dict] = []
    failures = 0

    for store, name in STORES.items():
        collected: list[Deal] = []
        errors: list[str] = []
        for fetch in SOURCES[store]:
            try:
                collected = fetch(store)
                if len(collected) >= MIN_DEALS:
                    break
                errors.append(f"{fetch.__module__}: nur {len(collected)} Aktionen")
            except Exception as exc:  # noqa: BLE001 – jede Quelle darf scheitern
                errors.append(f"{fetch.__module__}: {exc}")
                log.exception("%s: Quelle fehlgeschlagen", store)

        fresh = [d for d in collected if still_valid(d.to_json(), today)]
        if len(fresh) >= MIN_DEALS:
            deals_out.extend(d.to_json() for d in fresh)
            stores_out.append({
                "id": store, "name": name, "ok": True,
                "deals": len(fresh), "source": fresh[0].source,
                "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            log.info("%s: %d Aktionen", name, len(fresh))
        else:
            kept = [d for d in previous_deals[store] if still_valid(d, today)]
            deals_out.extend(kept)
            old = previous_stores.get(store, {})
            stores_out.append({
                "id": store, "name": name, "ok": False,
                "deals": len(kept), "source": old.get("source", ""),
                "fetchedAt": old.get("fetchedAt"),
                "error": "; ".join(errors) or "keine Daten",
            })
            failures += 1
            log.error("%s: keine neuen Daten (%s) – %d alte behalten", name, "; ".join(errors), len(kept))

    feed = {
        "version": FEED_VERSION,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stores": stores_out,
        "deals": deals_out,
    }
    PUBLIC.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(feed, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (PUBLIC / "index.html").write_text(render_status(feed), encoding="utf-8")
    log.info("Geschrieben: %s (%d Aktionen, %d Läden ohne Update)", OUTPUT, len(deals_out), failures)
    # Nur wenn gar kein Laden klappt, gilt der Lauf als fehlgeschlagen.
    return 1 if failures == len(STORES) else 0


def render_status(feed: dict) -> str:
    rows = "".join(
        f"<tr><td>{s['name']}</td><td>{'✅' if s['ok'] else '⚠️'}</td><td>{s['deals']}</td>"
        f"<td>{s.get('source','')}</td><td>{(s.get('fetchedAt') or '')[:16].replace('T',' ')}</td>"
        f"<td>{s.get('error','')}</td></tr>"
        for s in feed["stores"]
    )
    cats: dict[str, int] = {}
    for d in feed["deals"]:
        cats[d.get("category", "Sonstiges")] = cats.get(d.get("category", "Sonstiges"), 0) + 1
    cat_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in sorted(cats.items(), key=lambda x: -x[1]))
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FooDex Aktionen-Feed</title>
<style>body{{font-family:-apple-system,system-ui,sans-serif;margin:2rem;background:#0e1512;color:#e8efe9}}
table{{border-collapse:collapse;margin:1rem 0}}td,th{{padding:.4rem .8rem;border-bottom:1px solid #2a3630;text-align:left}}
a{{color:#3dd484}}code{{background:#18211d;padding:.1rem .3rem;border-radius:4px}}</style></head><body>
<h1>FooDex Aktionen-Feed</h1>
<p>Stand: {feed['generatedAt'][:16].replace('T',' ')} UTC · {len(feed['deals'])} Aktionen · Datei: <a href="aktionen.json"><code>aktionen.json</code></a></p>
<table><tr><th>Laden</th><th></th><th>Aktionen</th><th>Quelle</th><th>Abgeholt</th><th>Hinweis</th></tr>{rows}</table>
<h2>Nach Kategorie</h2><table>{cat_rows}</table>
<p>Wird jeden Dienstag um 6 Uhr automatisch aktualisiert. Quelle: aktionis.ch. Keine persönlichen Daten.</p>
</body></html>"""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(build())
