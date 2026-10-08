"""Gemeinsame Bausteine: Datensatz, HTTP mit Pausen, Preis-Parsing."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict, field
from datetime import date
from typing import Optional

import requests

USER_AGENT = "FooDexFeed/1.0 (+https://github.com/HausAmStiel/aktionen-feed)"
PAUSE_SECONDS = 1.2

STORES = {
    "migros": "Migros",
    "coop": "Coop",
    "denner": "Denner",
    "spar": "SPAR",
}


@dataclass
class Deal:
    id: str
    store: str
    title: str
    description: str = ""
    price: Optional[float] = None
    oldPrice: Optional[float] = None
    discountPercent: Optional[int] = None
    validFrom: Optional[str] = None  # ISO-Datum
    validTo: Optional[str] = None
    image: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    source: str = ""
    keywords: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        data = asdict(self)
        return {k: v for k, v in data.items() if v not in (None, "", [])}


_session = requests.Session()
_session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept-Language": "de-CH,de;q=0.9",
})


def get(url: str, timeout: int = 30) -> str:
    """Lädt eine Seite, mit kurzer Pause davor (fair gegenüber der Quelle)."""
    time.sleep(PAUSE_SECONDS)
    response = _session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse_price(text: str | None) -> Optional[float]:
    if not text:
        return None
    cleaned = text.replace("'", "").replace("’", "").replace(",", ".")
    match = re.search(r"\d+(?:\.\d{1,2})?", cleaned)
    if not match:
        return None
    try:
        return round(float(match.group(0)), 2)
    except ValueError:
        return None


def parse_percent(text: str | None) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"(\d{1,3})\s*%", text)
    return int(match.group(1)) if match else None


def parse_swiss_date(text: str) -> Optional[str]:
    """'01.10.2026' -> '2026-10-01'."""
    match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if not match:
        return None
    day, month, year = (int(x) for x in match.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def clean_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()
