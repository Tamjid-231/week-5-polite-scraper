"""HTML extraction helpers for catalogue and book pages."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class DiscoveredBook:
    product_url: str
    source_page: str


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
