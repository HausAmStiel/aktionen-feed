"""Quelle Aktionis.ch – fasst die Aktionen aller grossen Schweizer Läden zusammen.

Je Laden gibt es eine Seite /vendors/<laden> mit ca. 50 Aktionen pro Seite
und einer Seitennummer am Ende (/vendors/<laden>/2 …). Jede Karte trägt
Titel, Aktionspreis, Normalpreis, Prozent, Gültigkeit und Bild.
"""

from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup

from .categories import guess_category
from .common import Deal, clean_text, get, parse_percent, parse_price, parse_swiss_date

log = logging.getLogger(__name__)

BASE = "https://www.aktionis.ch"
VENDOR_SLUGS = {
    "migros": "migros",
    "coop": "coop",
    "denner": "denner",
    "spar": "spar",
}
MAX_PAGES = 30


def fetch_store(store: str) -> list[Deal]:
    slug = VENDOR_SLUGS[store]
    deals: list[Deal] = []
    seen: set[str] = set()
    page = 1
    last_page = 1
    while page <= min(last_page, MAX_PAGES):
        url = f"{BASE}/vendors/{slug}" + (f"/{page}" if page > 1 else "")
        html = get(url)
        soup = BeautifulSoup(html, "html.parser")
        last_page = max(last_page, _last_page(soup, slug))
        cards = soup.select("div.card.dealtype-deal")
        if not cards:
            break
        for card in cards:
            deal = _parse_card(card, store)
            if deal and deal.id not in seen:
                seen.add(deal.id)
                deals.append(deal)
        log.info("%s Seite %d/%d: %d Karten", store, page, last_page, len(cards))
        page += 1
    return deals


def _last_page(soup: BeautifulSoup, slug: str) -> int:
    pages = [1]
    for a in soup.select(f'a[href^="/vendors/{slug}/"]'):
        match = re.search(rf"/vendors/{slug}/(\d+)", a.get("href", ""))
        if match:
            pages.append(int(match.group(1)))
    return max(pages)


def _parse_card(card, store: str) -> Deal | None:
    upox = card.get("data-upox-id")
    title_el = card.select_one(".card-title")
    title = clean_text(title_el.get_text() if title_el else "")
    if not title:
        return None
    link = card.select_one("a[href^='/deals/']")
    url = BASE + link["href"] if link else None
    deal_id = f"aktionis-{upox}" if upox else f"aktionis-{store}-{re.sub(r'[^a-z0-9]+', '-', title.lower())}"

    description_el = card.select_one(".card-description")
    description = clean_text(description_el.get_text() if description_el else "")

    price = parse_price(_text(card, ".price-new"))
    old_price = parse_price(_text(card, ".price-old"))
    discount = parse_percent(_text(card, ".price-discount"))
    if discount is None and price and old_price and old_price > price:
        discount = round((1 - price / old_price) * 100)
    if discount is None:
        discount = parse_percent(title)

    valid_from = valid_to = None
    date_text = _text(card, ".card-date") or ""
    parts = [p.strip() for p in date_text.split("-")]
    if len(parts) == 2:
        valid_from, valid_to = parse_swiss_date(parts[0]), parse_swiss_date(parts[1])
    elif parts and parts[0]:
        valid_to = parse_swiss_date(parts[0])
    if not valid_to:
        valid_from, valid_to, description = _dates_from_description(description, valid_from)

    image_el = card.select_one(".card-image img")
    image = image_el.get("src") if image_el else None

    return Deal(
        id=deal_id,
        store=store,
        title=title,
        description=description,
        price=price,
        oldPrice=old_price,
        discountPercent=discount,
        validFrom=valid_from,
        validTo=valid_to,
        image=image,
        url=url,
        category=guess_category(title, description),
        source="aktionis",
    )


_VALID_RE = re.compile(
    r",?\s*Angebot gilt(?: nur)? (?:vom (\d{1,2})\.(\d{1,2})\.?\s*)?bis (\d{1,2})\.(\d{1,2})\.(\d{4})[^.]*\.?",
    re.IGNORECASE,
)


def _dates_from_description(description: str, valid_from: str | None):
    """Migros schreibt die Gültigkeit in den Beschreibungstext:
    '…, Angebot gilt nur vom 8.10. bis 14.10.2026, solange Vorrat.'"""
    match = _VALID_RE.search(description)
    if not match:
        return valid_from, None, description
    from_day, from_month, to_day, to_month, year = match.groups()
    valid_to = parse_swiss_date(f"{to_day}.{to_month}.{year}")
    if from_day and from_month:
        valid_from = parse_swiss_date(f"{from_day}.{from_month}.{year}") or valid_from
    cleaned = clean_text(description[: match.start()] + description[match.end():]).strip(" ,")
    return valid_from, valid_to, cleaned


def _text(card, selector: str) -> str | None:
    el = card.select_one(selector)
    return clean_text(el.get_text()) if el else None
