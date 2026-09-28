# Polite Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the required Python scraper that politely collects and validates 60 books from the first three Books to Scrape catalogue pages and reports every run.

**Architecture:** A small command-line pipeline coordinates a cache-aware HTTP client, focused Beautiful Soup parsers, and a Pydantic record model. Each page is processed independently; valid records and failures are written atomically as JSON, making reruns idempotent.

**Tech Stack:** Python 3.10+, Requests, Beautiful Soup 4, Pydantic 2, Pytest

**Spec:** `docs/superpowers/specs/2026-09-28-polite-scraper-design.md`

## Global Constraints

- Process exactly the first 3 catalogue pages and discover 60 unique book URLs.
- Use an honest user-agent, a finite timeout, status checks, caching, and at least 500 ms between real requests.
- Retry timeouts and 5xx responses once; never retry 403 or 404 responses.
- Preserve the eight raw fields and add numeric `price_gbp`; missing descriptions are `null`.
- Validate before storing; valid and invalid records go to separate JSON files.
- One deliberately broken URL must be skipped and reported without losing the 60 valid records.
- Implement required scope only; no optional, stretch, bonus, dashboard, CSV, browser, or AI features.

## Review Focus

- A cached empty or corrupted file must not be accepted as valid HTML; fetch it again or report a controlled failure.
- A catalogue page without a next link must stop safely instead of inventing a URL.
- Whitespace and currency formatting in `price_text` must normalize deterministically or fail validation.
- A book page without a description must produce `description: null`, not an exception or invented text.
- A timeout, 500, 403, or 404 must follow the exact retry policy and still allow the remaining pages to finish.

---

### Task 1: Stage 0 - Project setup and target classification

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `src/__init__.py`
- Create: `README.md`

**Interfaces:**
- Consumes: ToScrape's sandbox statement and the observed `https://books.toscrape.com/robots.txt` response.
- Produces: Install/run instructions and the required target-classification text used by the final submission.

- [ ] **Step 1: Record the live robots response once and confirm the sandbox statement**

Run one identified request with a finite timeout. Record the actual status; if absent, write exactly `no robots file found` and do not call that permission.

- [ ] **Step 2: Create the minimum Python project files**

Pin compatible ranges for Requests, Beautiful Soup, and Pydantic in `requirements.txt`; put Pytest in `requirements-dev.txt`; ignore `.venv/`, `__pycache__/`, `.pytest_cache/`, and `cache/`.

- [ ] **Step 3: Write the README target classification**

Name the target, the three-page limit, collected fields, robots result, appropriate sandbox use, and the exact sentence: `I will not reuse this code on another site without checking its rules and terms first.`

- [ ] **Step 4: Verify setup**

Run: `python -m pip install -r requirements.txt -r requirements-dev.txt`

Expected: dependencies install and `python -c "import requests, bs4, pydantic"` exits successfully.

- [ ] **Step 5: Commit**

Commit message: `Stage 0: classify scraping target`

### Task 2: Stage 1 - Polite fetch and cache

**Files:**
- Create: `src/fetcher.py`
- Create: `tests/test_fetcher.py`

**Interfaces:**
- Consumes: URL and stable relative cache key.
- Produces: `PoliteFetcher.fetch(url: str, cache_key: str) -> str`, `FetchStats`, and `FetchError`; stats expose `pages_fetched` and `cache_hits`.

- [ ] **Step 1: Write failing fetcher tests**

Add tests proving a 200 response is cached, the second call is a cache hit, an empty cache file is rejected, the user-agent and timeout are sent, real requests are spaced by at least 0.5 seconds, a 500/timeout is retried once, and 403/404 responses are not retried.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_fetcher.py -v`

Expected: FAIL because `src.fetcher` does not exist.

- [ ] **Step 3: Implement the fetcher**

Implement `PoliteFetcher(cache_dir: Path, user_agent: str, timeout_seconds: float = 10.0, delay_seconds: float = 0.5)` and `fetch`. Use injected session/sleep/clock collaborators where needed for deterministic tests, print `FETCH` or `CACHE HIT` with response size, and raise `FetchError` after policy-compliant attempts.

- [ ] **Step 4: Run tests and confirm success**

Run: `python -m pytest tests/test_fetcher.py -v`

Expected: all fetcher tests PASS.

- [ ] **Step 5: Commit**

Commit message: `Stage 1: fetch and cache HTML`

### Task 3: Stage 2 - Discover exactly three catalogue pages

**Files:**
- Create: `src/parser.py`
- Create: `tests/fixtures/catalogue-page.html`
- Create: `tests/fixtures/catalogue-last-page.html`
- Create: `tests/test_catalogue_parser.py`

**Interfaces:**
- Consumes: catalogue HTML and its absolute page URL.
- Produces: `DiscoveredBook(product_url: str, source_page: str)`, `parse_catalogue(html: str, page_url: str) -> tuple[list[DiscoveredBook], str | None]`, and `deduplicate_books(items) -> list[DiscoveredBook]`.

- [ ] **Step 1: Write failing catalogue parser tests**

Test absolute URL resolution with `urljoin`, product-area link selection, duplicate removal by `product_url`, next-link resolution, and safe `None` when the next link is missing.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_catalogue_parser.py -v`

Expected: FAIL because the parser functions are missing.

- [ ] **Step 3: Implement catalogue parsing**

Use Beautiful Soup selectors scoped to `article.product_pod` and `li.next a`. Keep first-seen order while deduplicating.

- [ ] **Step 4: Run tests and confirm success**

Run: `python -m pytest tests/test_catalogue_parser.py -v`

Expected: all catalogue parser tests PASS.

- [ ] **Step 5: Commit**

Commit message: `Stage 2: discover three catalogue pages`

### Task 4: Stage 3 - Extract the eight raw detail fields

**Files:**
- Modify: `src/parser.py`
- Create: `tests/fixtures/book-with-description.html`
- Create: `tests/fixtures/book-without-description.html`
- Create: `tests/test_book_parser.py`

**Interfaces:**
- Consumes: book HTML, absolute product URL, source catalogue URL, and UTC fetch timestamp.
- Produces: `parse_book(html: str, product_url: str, source_page: str, fetched_at: datetime) -> dict[str, object]` containing all eight raw keys.

- [ ] **Step 1: Write failing book parser tests**

Assert exact extraction of title, price text, availability text, rating word, description, provenance, and ISO UTC time. Assert missing description is `None`, whitespace is cleaned, and malformed HTML raises `ParseError` without terminating other work.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_book_parser.py -v`

Expected: FAIL because `parse_book` and `ParseError` are missing.

- [ ] **Step 3: Implement detail parsing**

Scope selectors to the product summary and the description heading's following paragraph. Derive rating from the star element's class list and never invent absent values.

- [ ] **Step 4: Run tests and confirm success**

Run: `python -m pytest tests/test_book_parser.py -v`

Expected: all book parser tests PASS.

- [ ] **Step 5: Commit**

Commit message: `Stage 3: extract book details`

### Task 5: Stage 4 - Normalize, validate, and store records

**Files:**
- Create: `src/models.py`
- Create: `src/storage.py`
- Create: `tests/test_models.py`
- Create: `tests/test_storage.py`

**Interfaces:**
- Consumes: raw parser dictionaries.
- Produces: `normalize_price(price_text: str) -> float`, Pydantic `BookRecord`, `validate_record(raw) -> BookRecord`, and `write_json_atomic(path: Path, value: object) -> None`.

- [ ] **Step 1: Write failing model and storage tests**

Test `£51.77 -> 51.77`, surrounding whitespace, malformed currency rejection, HTTPS URL validation, all required keys, optional description, deterministic JSON, atomic replacement, and deduplication by canonical `product_url`.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_models.py tests/test_storage.py -v`

Expected: FAIL because model and storage modules do not exist.

- [ ] **Step 3: Implement models and atomic JSON storage**

Keep `price_text` beside numeric `price_gbp`; serialize URLs and datetimes as JSON strings. Write UTF-8, indented JSON through a same-directory temporary file followed by replacement.

- [ ] **Step 4: Run tests and confirm success**

Run: `python -m pytest tests/test_models.py tests/test_storage.py -v`

Expected: all model and storage tests PASS.

- [ ] **Step 5: Commit**

Commit message: `Stage 4: validate normalized records`

### Task 6: Stage 5 - Complete pipeline, failure survival, and run report

**Files:**
- Create: `src/main.py`
- Create: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: fetcher, parser, models, and storage interfaces from Tasks 2-5.
- Produces: `run(inject_broken_url: bool = False) -> dict[str, object]`, CLI option `--test-broken-url`, `output/books.json`, `output/errors.json`, and `output/run-report.json`.

- [ ] **Step 1: Write failing pipeline tests**

With mocked HTML, assert exactly three catalogue pages, stable 60-URL deduplication, 60 validated records, idempotent overwrite on rerun, invalid records routed to `errors.json`, and one fake 404 reported while all 60 valid books survive. Assert the report includes start time, duration, pages fetched, cache hits, valid records, invalid records, and failed pages.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_pipeline.py -v`

Expected: FAIL because the pipeline entry point does not exist.

- [ ] **Step 3: Implement the pipeline and CLI**

Stop catalogue traversal after three pages even if another next link exists. Catch fetch, parse, and validation failures per book; continue processing and write all three outputs in a `finally`-safe reporting path.

- [ ] **Step 4: Run the complete suite**

Run: `python -m pytest -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit**

Commit message: `Stage 5: survive failures and report the run`

### Task 7: Stage 6 - Live evidence and submission README

**Files:**
- Modify: `README.md`
- Create: `output/books.json`
- Create: `output/errors.json`
- Create: `output/run-report.json`

**Interfaces:**
- Consumes: the completed command-line pipeline and real cached pages.
- Produces: a locally submission-ready project with reproducible instructions and verified sample output.

- [ ] **Step 1: Perform the first live run**

Run: `python -m src.main`

Expected: `catalogue_pages=3`, `discovered=60`, `unique_urls=60`, `detail_pages=60`; output has exactly 60 valid records.

- [ ] **Step 2: Perform the cached rerun**

Run: `python -m src.main`

Expected: exactly 60 records again, mostly cache hits, and no duplicates.

- [ ] **Step 3: Perform the required broken-page proof**

Run: `python -m src.main --test-broken-url`

Expected: run finishes, `books.json` still has 60 valid records, and the report records one failed page.

- [ ] **Step 4: Finish and verify the README**

Document one copy-paste run command, installation, lane, record schema, politeness rules, real run report, one honest limitation, why no browser is needed, and the required ethics note. Check `books.json` contains 60 unique HTTPS product URLs and numeric prices.

- [ ] **Step 5: Commit**

Commit message: `Stage 6: publish scraper evidence`

- [ ] **Step 6: Final verification**

Run: `python -m pytest -v` and inspect `git log --oneline`.

Expected: all tests PASS and history contains the seven meaningful stage commits (plus planning history).
