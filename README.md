# The Polite Scraper

This is my Week 5 backend assignment. It collects book information from the first three catalogue pages of Books to Scrape, checks the data, and saves the valid records as JSON.

## Target classification

- **Site:** [Books to Scrape](https://books.toscrape.com/)
- **Why this target:** ToScrape describes it as a fictional bookstore made for people to practise web scraping and test scraping tools.
- **Scope:** Only the first three catalogue pages, which contain 60 books.
- **Data collected:** title, product URL, price, availability, rating, description, source catalogue page, and fetch time.
- **Robots check:** On 28 September 2026 I requested `https://books.toscrape.com/robots.txt` once and received HTTP 404, so no robots file was found. A missing robots file is not permission; the site's own sandbox description is why this target is appropriate.

The small scope and practice-sandbox purpose make this an appropriate target for this assignment. I will not reuse this code on another site without checking its rules and terms first.

## Requirements

- Python 3.10 or newer
- Internet access for the first run

## Setup and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.main
```

The first run downloads and caches the pages. Later runs read the saved HTML and do not request the same pages again. The generated files are:

- `output/books.json` - validated book records
- `output/errors.json` - records that failed validation, with reasons
- `output/run-report.json` - counts and timing for the run

To repeat my broken-page check, run:

```powershell
python -m src.main --test-broken-url
```

## Record schema

| Field | Type | Notes |
| --- | --- | --- |
| `title` | string | Required |
| `product_url` | HTTPS URL | Canonical identity for deduplication |
| `price_text` | string | Original value, for example `£51.77` |
| `price_gbp` | number | Normalized GBP price |
| `availability_text` | string | Original availability text |
| `rating_text` | string | One, Two, Three, Four, or Five |
| `description` | string or null | Some pages do not have one |
| `source_page` | HTTPS URL | Catalogue page where I found the book |
| `fetched_at` | UTC date-time | Provenance timestamp |

Pydantic checks every record before it reaches `books.json`. Invalid records go to `errors.json` instead.

## Politeness rules I used

- An honest `FlyRankInternship-A9/1.0 (student assignment)` user-agent on every real request.
- A 10-second timeout so a request cannot hang forever.
- HTTP status checking before any HTML is parsed.
- At least 500 ms between real requests.
- One retry only for a timeout or 5xx server error.
- No retries for 403 or 404 responses.
- A local cache so development and reruns do not keep contacting the site.
- Each page is handled separately, so one failure does not stop the full run.

## Verified result

I ran the scraper once from the network, once again from the cache, and once with one fake book URL. The clean run fetched 3 catalogue pages and 60 detail pages. The cached run still produced exactly 60 unique records. The failure test kept all 60 good records and reported the fake page instead of crashing.

This is the real `run-report.json` from the failure test:

```json
{
  "start_time": "2026-10-03T18:25:43.571002Z",
  "duration_seconds": 1.56,
  "catalogue_pages": 3,
  "discovered": 60,
  "unique_urls": 60,
  "detail_pages": 60,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failed_page_urls": [
    "https://books.toscrape.com/catalogue/this-page-does-not-exist/index.html"
  ]
}
```

## Why I did not use a browser

The book data is already present in the HTML returned by the server. A browser automation tool would add more time and memory without giving this scraper any extra data.

## Honest limitation

The selectors are written for the current Books to Scrape HTML structure. If that practice site changes its class names or layout, the parser may need to be updated.

## Ethics note

If a site has an official API, I would use that first. I would not use scraping to bypass a login, paywall, access block, or the site's stated rules. I would also collect only the fields needed for the task.

## Tests

Install the development requirements and run:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

