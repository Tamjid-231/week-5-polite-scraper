"""Command-line entry point for the Week 5 polite scraper."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from typing import Callable, Protocol
from urllib.parse import urlsplit

from pydantic import ValidationError

from src.fetcher import FetchError, PoliteFetcher
from src.models import BookRecord, validate_record
from src.parser import (
    DiscoveredBook,
    ParseError,
    deduplicate_books,
    parse_book,
    parse_catalogue,
)
from src.storage import deduplicate_records, write_json_atomic


START_URL = "https://books.toscrape.com/catalogue/page-1.html"
BROKEN_URL = (
    "https://books.toscrape.com/catalogue/this-page-does-not-exist/index.html"
)
USER_AGENT = "FlyRankInternship-A9/1.0 (student assignment)"


class Fetcher(Protocol):
    stats: object

    def fetch(self, url: str, cache_key: str) -> str: ...


def run(
    inject_broken_url: bool = False,
    *,
    fetcher: Fetcher | None = None,
    output_dir: Path = Path("output"),
    now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    timer_fn: Callable[[], float] = perf_counter,
) -> dict[str, object]:
    started_at = now_fn()
    started_timer = timer_fn()
    active_fetcher = fetcher or PoliteFetcher(Path("cache"), USER_AGENT)

    catalogue_pages = 0
    discovered: list[DiscoveredBook] = []
    failed_page_urls: list[str] = []
    invalid_records: list[dict[str, object]] = []
    valid_records: list[BookRecord] = []
    detail_pages = 0

    page_url: str | None = START_URL
    for _ in range(3):
        if page_url is None:
            break
        try:
            html = active_fetcher.fetch(page_url, _cache_key(page_url))
        except FetchError as exc:
            failed_page_urls.append(page_url)
            print(f"SKIP {page_url} reason={exc}")
            break
        page_books, page_url = parse_catalogue(html, page_url)
        discovered.extend(page_books)
        catalogue_pages += 1

    unique_books = deduplicate_books(discovered)
    unique_url_count = len(unique_books)
    work_items = list(unique_books)
    if inject_broken_url:
        work_items.append(DiscoveredBook(BROKEN_URL, START_URL))

    printed_raw_record = False
    for item in work_items:
        try:
            html = active_fetcher.fetch(item.product_url, _cache_key(item.product_url))
            detail_pages += 1
        except FetchError as exc:
            failed_page_urls.append(item.product_url)
            print(f"SKIP {item.product_url} reason={exc}")
            continue

        try:
            raw = parse_book(html, item.product_url, item.source_page, now_fn())
            if not printed_raw_record:
                print("RAW RECORD")
                print(json.dumps(raw, ensure_ascii=False, indent=2))
                printed_raw_record = True
            valid_records.append(validate_record(raw))
        except (ParseError, ValidationError, ValueError) as exc:
            invalid_records.append(
                {"product_url": item.product_url, "reason": str(exc)}
            )
            print(f"INVALID {item.product_url} reason={exc}")

    valid_records = deduplicate_records(valid_records)
    books_payload = [record.model_dump(mode="json") for record in valid_records]
    write_json_atomic(output_dir / "books.json", books_payload)
    write_json_atomic(output_dir / "errors.json", invalid_records)

    stats = active_fetcher.stats
    report: dict[str, object] = {
        "start_time": started_at.isoformat().replace("+00:00", "Z"),
        "duration_seconds": round(timer_fn() - started_timer, 3),
        "catalogue_pages": catalogue_pages,
        "discovered": len(discovered),
        "unique_urls": unique_url_count,
        "detail_pages": detail_pages,
        "pages_fetched": int(getattr(stats, "pages_fetched", 0)),
        "cache_hits": int(getattr(stats, "cache_hits", 0)),
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "failed_pages": len(failed_page_urls),
        "failed_page_urls": failed_page_urls,
    }
    write_json_atomic(output_dir / "run-report.json", report)
    print(
        f"catalogue_pages={catalogue_pages} discovered={len(discovered)} "
        f"unique_urls={unique_url_count} detail_pages={detail_pages}"
    )
    print(
        f"valid_records={len(valid_records)} invalid_records={len(invalid_records)} "
        f"failed_pages={len(failed_page_urls)}"
    )
    return report


def _cache_key(url: str) -> str:
    path = urlsplit(url).path.lstrip("/")
    return path or "index.html"


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape three Books to Scrape pages")
    parser.add_argument(
        "--test-broken-url",
        action="store_true",
        help="add one fake book URL to prove failures are isolated",
    )
    args = parser.parse_args()
    run(inject_broken_url=args.test_broken_url)


if __name__ == "__main__":
    main()
