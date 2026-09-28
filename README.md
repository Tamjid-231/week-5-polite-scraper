# The Polite Scraper

This is my Week 5 backend assignment. It collects book information from the first three catalogue pages of Books to Scrape, checks the data, and saves the valid records as JSON.

## Target classification

- **Site:** [Books to Scrape](https://books.toscrape.com/)
- **Why this target:** ToScrape describes it as a fictional bookstore made for people to practise web scraping and test scraping tools.
- **Scope:** Only the first three catalogue pages, which contain 60 books.
- **Data collected:** title, product URL, price, availability, rating, description, source catalogue page, and fetch time.
- **Robots check:** On 28 September 2026 I requested `https://books.toscrape.com/robots.txt` once and received HTTP 404, so no robots file was found. A missing robots file is not permission; the site's own sandbox description is why this target is appropriate.

The small scope and practice-sandbox purpose make this an appropriate target for this assignment. I will not reuse this code on another site without checking its rules and terms first.

## Status

The scraper is being implemented stage by stage. Final setup, run instructions, schema, politeness rules, evidence, limitation, and ethics notes will be added after the verified run.

