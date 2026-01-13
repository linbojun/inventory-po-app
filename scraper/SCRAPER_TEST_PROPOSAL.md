# Scraper Test Proposal

## Objectives

1. Ensure DOM parsers remain stable even if Wix tweaks class names.
2. Verify manifest generation + image downloader routines behave deterministically.
3. Keep the CLI smoke-tested without hitting the live site (fixtures + mocks).

## Proposed Coverage

| Test | Description | Type |
| --- | --- | --- |
| `test_navigation_parser.py` | Feed the saved homepage HTML and assert that all eight top-level categories + their subcategories are discovered. | Unit |
| `test_product_parser.py` | Use the sample product page fixture to ensure we extract `product_id`, `name`, `description`, primary image URL, and SKU. | Unit |
| `test_catalog_writer.py` | (Future) Validate that adding duplicate product IDs overwrites entries and that JSON serialization is stable. | Unit |
| `test_cli_smoke.py` | (Future) Invoke `python -m es_scraper.cli run --limit 2 --skip-download` with an injected sitemap fixture to confirm the CLI pipeline. | Integration |

## Out-of-Scope / Manual

- Full end-to-end runs (2.8k downloads) are performed manually because of the
  bandwidth/time cost.
- Playwright dynamic scraping relies on live pages; we guard it with feature
  flags and log warnings when the storefront blocks automation.
