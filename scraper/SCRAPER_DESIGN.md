# ES Houseware Scraper – Design Notes

## Goals

1. Download every publicly listed product image from `eshouseware.com` and store
   it under `scraper/data/product_images/`.
2. Produce a canonical manifest that links product IDs → product names → image
   paths so the Inventory app (or any downstream tooling) can ingest them.
3. Keep the existing backend/frontend untouched by isolating scraper logic in a
   dedicated workspace.
4. Skip any product that does not expose a downloadable hero image so downstream
   consumers only see records with complete assets.

## High-Level Flow

```mermaid
flowchart TD
  sitemap[Fetch store-products-sitemap.xml] --> urls[Extract product URLs]
  urls --> fetchHTML[Request product pages]
  fetchHTML --> parseJSON[Parse schema.org JSON]
  parseJSON --> record[Normalize ProductRecord]
  record --> image[Download image]
  image --> staticDir[(scraper/data/product_images)]
  record --> catalog[Write catalog.json]
  nav[Parse navigation menu] --> navCache[site_map.json]
  navCache --> dynamic[Playwright driver (optional)]
  dynamic -->|category URLs| urls
```

- **Navigation parser** – captures the mega-menu relationships for operator
  reference and powers the optional browser-based scraper.
- **Sitemap scraper** – main workhorse that enumerates every product from the
  Wix-generated sitemap and enriches it via the embedded Schema.org payload
  (records without hero images are skipped).
- **Dynamic scraper (experimental)** – uses Playwright to walk category pages.
  Some Wix storefronts refuse to render product cards to automated browsers;
  when that happens, the CLI logs the failure and falls back to the sitemap.

## Key Modules

| Module | Responsibility |
| --- | --- |
| `navigation.py` | Downloads and parses the homepage navigation tree, serializes to JSON. |
| `browser.py` | Safe Playwright context manager with retrying navigation helpers. |
| `product_page.py` | Parses a product page (raw HTML) into a `ProductRecord`. |
| `sitemap.py` | Loads/parses the store sitemap, yields URL + hero image pairs. |
| `downloader.py` | Streams images with checksum validation + skip-if-exists. |
| `catalog.py` | Validates and writes the manifest via Pydantic models. |
| `cli.py` | Typer-powered entry point (`nav`, `run`, `inspect`). |

## Data Contracts

### ProductRecord

```python
@dataclass
class ProductRecord:
    product_id: str
    name: str
    slug: str
    description: str
    sku: str | None
    product_url: str
    image_urls: list[str]
    categories: list[str]
```

### Catalog JSON (abridged)

```json
{
  "scraped_at": "2026-01-10T18:00:00Z",
  "source": "https://www.eshouseware.com/store-products-sitemap.xml",
  "product_count": 2800,
  "products": [
    {
      "product_id": "801361",
      "name": "KIWI PEELER#218 鋸口刨蔬果皮刀",
      "product_url": "https://www.eshouseware.com/product-page/801361-kiwi-peeler-218",
      "image": {
        "source_url": "https://static.wixstatic.com/.../file.jpg",
        "local_path": "scraper/data/product_images/801361_kiwi-peeler-218.jpg"
      }
    }
  ]
}
```

## Error Handling & Resilience

- **HTTP retries** – All network calls go through a shared `requests.Session`
  with configurable retry/backoff. Failures log warnings and continue.
- **Resume support** – The manifest is read on startup; any product ID already
  present is skipped so interrupted runs can resume quickly.
- **Download integrity** – Images are written to a temp file first, then moved
  into place only after the stream completes.

## Performance Considerations

- The sitemap is ~1 MB and currently advertises ~2.8k products. Downloading the
  500px hero image for every SKU takes ~15–20 minutes with a 150 ms delay
  between requests (~600 MB of data). This is acceptable for a batch job.
- `--limit` and `--skip-download` flags keep developer feedback loops short.

## Open Questions

1. **Multiple images per product** – currently we capture the primary hero image
   exposed via Schema.org; the downloader can be extended to fetch every entry
   in the `image` array if/when storage budgets allow.
2. **Dynamic scraping reliability** – Wix occasionally withholds product cards
   from automated browsers. If this mode becomes critical, we may need to proxy
   through a real browser profile or leverage the official Wix Stores APIs.
3. **Delta updates** – At the moment we re-scan the entire sitemap. We could
   cache ETags or compare `<lastmod>` timestamps to support incremental syncs.
