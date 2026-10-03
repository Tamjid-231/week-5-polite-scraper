import json
from pathlib import Path

from src.models import validate_record
from src.storage import deduplicate_records, write_json_atomic
from tests.test_models import RAW_RECORD


def test_records_are_deduplicated_by_canonical_product_url() -> None:
    first = validate_record(RAW_RECORD)
    duplicate = validate_record({**RAW_RECORD, "title": "Changed duplicate"})
    second = validate_record(
        {
            **RAW_RECORD,
            "title": "Second book",
            "product_url": "https://books.toscrape.com/catalogue/second_2/index.html",
        }
    )

    assert deduplicate_records([first, duplicate, second]) == [first, second]


def test_json_is_utf8_indented_and_replaces_existing_file(tmp_path: Path) -> None:
    output = tmp_path / "output" / "books.json"
    write_json_atomic(output, [{"title": "First", "price_text": "£1.00"}])
    write_json_atomic(output, [{"title": "Second", "price_text": "£2.00"}])

    assert json.loads(output.read_text(encoding="utf-8")) == [
        {"title": "Second", "price_text": "£2.00"}
    ]
    assert "£2.00" in output.read_text(encoding="utf-8")
    assert list(output.parent.glob("*.tmp")) == []
