import pytest
from pydantic import ValidationError

from src.models import BookRecord, normalize_price, validate_record


RAW_RECORD = {
    "title": "A Light in the Attic",
    "product_url": "https://books.toscrape.com/catalogue/a-light_1/index.html",
    "price_text": "£51.77",
    "availability_text": "In stock (22 available)",
    "rating_text": "Three",
    "description": None,
    "source_page": "https://books.toscrape.com/catalogue/page-1.html",
    "fetched_at": "2026-09-28T10:00:00Z",
}


def test_price_text_becomes_numeric_gbp() -> None:
    assert normalize_price("£51.77") == 51.77
    assert normalize_price("  £10.00  ") == 10.0


@pytest.mark.parametrize("value", ["51.77", "$51.77", "£free", "", "£1,000.00"])
def test_malformed_price_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="price"):
        normalize_price(value)


def test_raw_record_is_normalized_and_validated() -> None:
    record = validate_record(RAW_RECORD)

    assert isinstance(record, BookRecord)
    assert record.price_text == "£51.77"
    assert record.price_gbp == 51.77
    assert record.description is None


def test_non_https_product_url_is_rejected() -> None:
    raw = {**RAW_RECORD, "product_url": "http://books.toscrape.com/book.html"}

    with pytest.raises(ValidationError):
        validate_record(raw)


def test_missing_required_field_is_rejected() -> None:
    raw = dict(RAW_RECORD)
    raw.pop("title")

    with pytest.raises(ValidationError):
        validate_record(raw)

