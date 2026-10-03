"""HTML extraction helpers for catalogue and book pages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class DiscoveredBook:
    product_url: str
    source_page: str


class ParseError(ValueError):
    """Raised when required product data is missing or malformed."""


def parse_catalogue(
    html: str, page_url: str
) -> tuple[list[DiscoveredBook], str | None]:
    soup = BeautifulSoup(html, "html.parser")
    books: list[DiscoveredBook] = []
    for link in soup.select("article.product_pod h3 a[href]"):
        books.append(
            DiscoveredBook(
                product_url=urljoin(page_url, str(link["href"])),
                source_page=page_url,
            )
        )

    next_link = soup.select_one("li.next a[href]")
    next_url = urljoin(page_url, str(next_link["href"])) if next_link else None
    return books, next_url


def deduplicate_books(items: list[DiscoveredBook]) -> list[DiscoveredBook]:
    unique: dict[str, DiscoveredBook] = {}
    for item in items:
        unique.setdefault(item.product_url, item)
    return list(unique.values())


def parse_book(
    html: str,
    product_url: str,
    source_page: str,
    fetched_at: datetime,
) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    product = soup.select_one("div.product_main")
    if product is None:
        raise ParseError("missing product area")

    title = _required_text(product.select_one("h1"), "title")
    price_text = _required_text(product.select_one("p.price_color"), "price")
    availability_text = _required_text(
        product.select_one("p.instock.availability"), "availability"
    )

    rating_element = product.select_one("p.star-rating")
    rating_text = None
    if rating_element is not None:
        rating_text = next(
            (
                class_name
                for class_name in rating_element.get("class", [])
                if class_name != "star-rating"
            ),
            None,
        )
    if not rating_text:
        raise ParseError("missing rating")

    description_element = soup.select_one("#product_description + p")
    description = (
        _clean_text(description_element.get_text(" ", strip=True))
        if description_element is not None
        else None
    )
    timestamp = fetched_at.isoformat().replace("+00:00", "Z")

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": timestamp,
    }


def _required_text(element: object, field_name: str) -> str:
    if element is None or not hasattr(element, "get_text"):
        raise ParseError(f"missing {field_name}")
    value = _clean_text(element.get_text(" ", strip=True))
    if not value:
        raise ParseError(f"missing {field_name}")
    return value


def _clean_text(value: str) -> str:
    return " ".join(value.split())
