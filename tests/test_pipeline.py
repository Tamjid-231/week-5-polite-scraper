import json
from pathlib import Path

from src.fetcher import FetchError, FetchStats
from src.main import START_URL, run


class MappingFetcher:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.stats = FetchStats()

    def fetch(self, url: str, cache_key: str) -> str:
        del cache_key
        if url not in self.pages:
            raise FetchError(f"Failed to fetch {url}: HTTP 404")
        self.stats.pages_fetched += 1
        return self.pages[url]


def catalogue_html(page_number: int) -> str:
    products = "".join(
        f'<article class="product_pod"><h3><a href="book-{index}_{index}/index.html">Book</a></h3></article>'
        for index in range((page_number - 1) * 20 + 1, page_number * 20 + 1)
    )
    return (
        f"<html><body>{products}<li class='next'><a href='page-{page_number + 1}.html'>next</a></li></body></html>"
    )


def book_html(index: int, *, malformed: bool = False) -> str:
    title = "" if malformed else f"<h1>Book {index}</h1>"
    return f"""
    <html><body><div class="product_main">
      {title}<p class="price_color">£{index}.00</p>
      <p class="instock availability">In stock ({index} available)</p>
      <p class="star-rating Three"></p>
    </div><div id="product_description"><h2>Product Description</h2></div>
    <p>Description for book {index}.</p></body></html>
    """


def make_pages(*, malformed_book: int | None = None) -> dict[str, str]:
    pages: dict[str, str] = {}
    for page_number in range(1, 4):
        page_url = f"https://books.toscrape.com/catalogue/page-{page_number}.html"
        pages[page_url] = catalogue_html(page_number)
    for index in range(1, 61):
        pages[
            f"https://books.toscrape.com/catalogue/book-{index}_{index}/index.html"
        ] = book_html(index, malformed=index == malformed_book)
    return pages


def test_pipeline_processes_three_pages_and_writes_sixty_records(tmp_path: Path) -> None:
    report = run(fetcher=MappingFetcher(make_pages()), output_dir=tmp_path)
    books = json.loads((tmp_path / "books.json").read_text(encoding="utf-8"))

    assert report["catalogue_pages"] == 3
    assert report["discovered"] == 60
    assert report["unique_urls"] == 60
    assert report["detail_pages"] == 60
    assert report["valid_records"] == 60
    assert report["invalid_records"] == 0
    assert report["failed_pages"] == 0
    assert len(books) == 60
    assert len({book["product_url"] for book in books}) == 60
    assert all(isinstance(book["price_gbp"], float) for book in books)
    assert START_URL == "https://books.toscrape.com/catalogue/page-1.html"


def test_rerun_overwrites_instead_of_duplicating(tmp_path: Path) -> None:
    run(fetcher=MappingFetcher(make_pages()), output_dir=tmp_path)
    run(fetcher=MappingFetcher(make_pages()), output_dir=tmp_path)

    books = json.loads((tmp_path / "books.json").read_text(encoding="utf-8"))
    assert len(books) == 60


def test_invalid_record_goes_to_errors_and_other_books_survive(tmp_path: Path) -> None:
    report = run(
        fetcher=MappingFetcher(make_pages(malformed_book=7)), output_dir=tmp_path
    )
    errors = json.loads((tmp_path / "errors.json").read_text(encoding="utf-8"))

    assert report["valid_records"] == 59
    assert report["invalid_records"] == 1
    assert report["failed_pages"] == 0
    assert errors[0]["product_url"].endswith("book-7_7/index.html")
    assert "title" in errors[0]["reason"]


def test_deliberate_broken_url_is_reported_without_losing_good_books(
    tmp_path: Path,
) -> None:
    report = run(
        inject_broken_url=True,
        fetcher=MappingFetcher(make_pages()),
        output_dir=tmp_path,
    )
    books = json.loads((tmp_path / "books.json").read_text(encoding="utf-8"))

    assert report["failed_pages"] == 1
    assert report["valid_records"] == 60
    assert len(books) == 60
    assert report["failed_page_urls"] == [
        "https://books.toscrape.com/catalogue/this-page-does-not-exist/index.html"
    ]


def test_run_report_contains_required_measurements(tmp_path: Path) -> None:
    report = run(fetcher=MappingFetcher(make_pages()), output_dir=tmp_path)
    saved = json.loads((tmp_path / "run-report.json").read_text(encoding="utf-8"))

    assert saved == report
    assert set(report) >= {
        "start_time",
        "duration_seconds",
        "pages_fetched",
        "cache_hits",
        "valid_records",
        "invalid_records",
        "failed_pages",
    }
