# Scraper Execution Plan (Snapshot)

- **Scope** – Pull every publicly visible product + image from
  `https://www.eshouseware.com` and store the assets locally.
- **Data sources** – Navigation menu (category lineage), store sitemap (product
  discovery), individual product pages (metadata), hero image URLs.
- **Environments** – Works with plain `requests` (default mode) or Playwright
  (dynamic mode) inside any Python 3.9+ virtual environment.
- **Rate limits** – Default delay of 0.15 s between requests (~20 products/min).
  Adjust via `--throttle` CLI flag if ES approves faster scraping.
- **Idempotency** – Catalog manifest deduplicates by `product_id`. Re-running the
  scraper skips completed entries unless `--force` is supplied.
- **Output** – `scraper/data/product_images/` holds binaries, while
  `scraper/data/catalog.json` keeps structured metadata for downstream
  consumers.
- **Quality gate** – Any product lacking a downloadable hero image is skipped,
  keeping the manifest aligned with assets available on disk.
- **Testing** – Offline fixtures ensure the parser keeps working even if the
  live site changes markup.
