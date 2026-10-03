from pathlib import Path

from src.parser import DiscoveredBook, deduplicate_books, parse_catalogue


FIXTURES = Path(__file__).parent / "fixtures"
PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"


def test_catalogue_parser_resolves_book_and_next_urls() -> None:
    html = (FIXTURES / "catalogue-page.html").read_text(encoding="utf-8")

    books, next_url = parse_catalogue(html, PAGE_URL)

    assert books == [
        DiscoveredBook(
            product_url="https://books.toscrape.com/catalogue/book-one_1/index.html",
            source_page=PAGE_URL,
        ),
        DiscoveredBook(
            product_url="https://books.toscrape.com/catalogue/book-two_2/index.html",
            source_page=PAGE_URL,
        ),
    ]
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_catalogue_without_next_link_stops_safely() -> None:
    html = (FIXTURES / "catalogue-last-page.html").read_text(encoding="utf-8")

    _, next_url = parse_catalogue(html, PAGE_URL)

    assert next_url is None


def test_duplicate_product_urls_keep_first_source_page() -> None:
    items = [
        DiscoveredBook("https://example.test/book-1", "https://example.test/page-1"),
        DiscoveredBook("https://example.test/book-2", "https://example.test/page-1"),
        DiscoveredBook("https://example.test/book-1", "https://example.test/page-2"),
    ]

    assert deduplicate_books(items) == items[:2]
