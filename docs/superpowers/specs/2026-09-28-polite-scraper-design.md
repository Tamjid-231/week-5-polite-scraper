# Polite Scraper Design

## Purpose and scope

Build the required Week 5 Assignment A9 project in Python. The scraper will process exactly the first three catalogue pages of Books to Scrape, discover 60 unique book URLs, fetch each detail page politely, validate the extracted data, save the valid records, and finish with an honest run report. Optional, stretch, and bonus features are outside scope.

## Project structure

- `src/main.py`: command-line entry point and pipeline orchestration.
- `src/fetcher.py`: polite HTTP requests, timeout, status handling, one retry for timeouts and 5xx responses, delay, and file cache.
- `src/parser.py`: catalogue link discovery and detail-page extraction.
- `src/models.py`: Pydantic schema and normalization rules.
- `tests/`: required behavior tests using local HTML fixtures and mocked requests.
- `output/books.json`: validated records.
- `output/errors.json`: invalid records with reasons.
- `output/run-report.json`: timing, fetch, cache, validation, and failure totals.
- `README.md`: target classification, robots result, setup/run command, schema, politeness rules, limitation, ethics note, and a real report example.
- `requirements.txt`, `.gitignore`, and local cache directory.

## Data flow

The entry point starts at `https://books.toscrape.com/catalogue/page-1.html`. It fetches or reads each catalogue page from cache, follows the page's own next link, and stops after page 3. Each book link is resolved with `urljoin`, associated with its source catalogue page, and deduplicated by absolute product URL.

Each detail page is fetched or read from cache and parsed into the eight required raw fields: `title`, `product_url`, `price_text`, `availability_text`, `rating_text`, `description`, `source_page`, and `fetched_at`. Missing descriptions become `null`. The price text is normalized to numeric `price_gbp`, while the original text is retained. Pydantic validates every finished record before it is stored.

Valid records are deduplicated by `product_url` and overwrite `output/books.json` as one deterministic collection, keeping reruns at 60 records. Invalid records go to `output/errors.json` with a reason. One deliberately fake URL is added by the program's required failure-demonstration mode; that page is logged and skipped without reducing the 60 valid records.

## Politeness and failure handling

Every real request sends an identifying user-agent, uses a finite timeout, checks the response status, and waits at least 500 milliseconds after the previous real request. Cached reads do not wait or contact the server. Timeouts and 5xx responses are retried once after a short wait. HTTP 403 and 404 responses are not retried. Other failed pages are recorded and skipped so the remaining work can finish.

The README will state that ToScrape identifies Books to Scrape as a practice sandbox. The live robots request result will be recorded exactly as observed; a missing file will be described as `no robots file found`, not as permission.

## Reporting

Every run writes `output/run-report.json` with start time, duration, catalogue/detail pages fetched, cache hits, valid records, invalid records, and failed pages. Console output will include the required checkpoints without printing full HTML.

## Verification

Automated tests will cover price normalization, relative-to-absolute URL conversion, missing descriptions, URL deduplication, malformed input, retry rules, and cache behavior. Final verification will run the tests, perform a clean live scrape, rerun from cache, and perform the deliberate broken-URL run. The checks must show three catalogue pages, 60 unique URLs, exactly 60 validated records after both normal runs, and one failed page while preserving all 60 valid records in failure mode.

## Submission boundary

The local folder will contain the complete runnable project, sample outputs, README, and meaningful stage-based Git history. Publishing or pushing to a public GitHub repository requires the user's separate authorization and is not part of this local implementation.
