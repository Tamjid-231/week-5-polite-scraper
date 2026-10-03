from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.parser import ParseError, parse_book


FIXTURES = Path(__file__).parent / "fixtures"
PRODUCT_URL = "https://books.toscrape.com/catalogue/a-light_1/index.html"
SOURCE_PAGE = "https://books.toscrape.com/catalogue/page-1.html"
FETCHED_AT = datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc)


def test_book_parser_returns_all_eight_raw_fields() -> None:
    html = (FIXTURES / "book-with-description.html").read_text(encoding="utf-8")

    result = parse_book(html, PRODUCT_URL, SOURCE_PAGE, FETCHED_AT)

    assert result == {
        "title": "A Light in the Attic",
        "product_url": PRODUCT_URL,
        "price_text": "£51.77",
        "availability_text": "In stock (22 available)",
        "rating_text": "Three",
        "description": "A funny and thoughtful collection of poems.",
        "source_page": SOURCE_PAGE,
        "fetched_at": "2026-09-28T10:00:00Z",
    }


def test_missing_description_is_none() -> None:
    html = (FIXTURES / "book-without-description.html").read_text(encoding="utf-8")

    result = parse_book(html, PRODUCT_URL, SOURCE_PAGE, FETCHED_AT)

    assert result["description"] is None
    assert set(result) == {
        "title",
        "product_url",
        "price_text",
        "availability_text",
        "rating_text",
        "description",
        "source_page",
        "fetched_at",
    }


def test_missing_required_product_field_raises_controlled_error() -> None:
    with pytest.raises(ParseError, match="title"):
        parse_book(
            "<html><div class='product_main'></div></html>",
            PRODUCT_URL,
            SOURCE_PAGE,
            FETCHED_AT,
        )
