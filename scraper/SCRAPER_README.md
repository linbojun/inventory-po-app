# ES Houseware Scraper

A standalone utility that harvests every ES Houseware product (ID, name, and
image) without touching the existing frontend/backend logic.

## Features

- Parses the public navigation menu to discover category → subcategory
  relationships (cached under `scraper/data/site_map.json`).
- Collects every product URL from the store sitemap and enriches it with live
  product metadata (via the embedded `application/ld+json` payload).
- Downloads primary product images into `scraper/data/product_images/` and keeps
  a normalized catalog manifest (`scraper/data/catalog.json`) with provenance +
  local paths. Products that lack a downloadable hero image are skipped to keep
  the dataset usable downstream.
- Optional (experimental) dynamic scraper that drives Playwright through each
  category page when a browser is required.

## Project Layout

```
scraper/
├── SCRAPER_README.md      # You are here
├── SCRAPER_DESIGN.md      # Architecture & data flow
├── SCRAPER_CHANGELOG.md   # Scraper-specific history
├── SCRAPER_TEST_PROPOSAL.md # Test intent beyond fixtures
├── SCRAPER_PLAN.md        # Crawl assumptions & guardrails
├── requirements.txt       # Runtime dependencies
├── pyproject.toml         # Package metadata
├── data/                  # Cached artifacts (site map, sitemap snapshots)
├── src/es_scraper/        # Python package (navigation, sitemap, CLI, etc.)
└── tests/                 # pytest-based regression suite
```

## Prerequisites

1. Python 3.9+
2. A virtual environment (recommended). From repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scraper/requirements.txt
playwright install  # one-time browser download
```

> If you prefer to reuse the existing `backend/venv`, simply activate it
> instead of creating a new environment.

## Usage

### 1. Build / refresh the navigation cache

```bash
python -m es_scraper.cli nav --output scraper/data/site_map.json --refresh
```

### 2. Run the scraper (sitemap mode)

```bash
python -m es_scraper.cli run \
  --mode sitemap \
  --sitemap-url https://www.eshouseware.com/store-products-sitemap.xml \
  --output scraper/data/product_images \
  --manifest scraper/data/catalog.json
```

Flags of interest:

- `--limit` – process only the first *N* products (useful for dry runs).
- `--skip-download` – populate the manifest without saving binaries (CI safe).
- `--resume` – reuse the manifest to skip already-downloaded items.

### 3. Experimental browser mode

```bash
python -m es_scraper.cli run --mode dynamic --limit 30
```

The dynamic path uses Playwright and the cached navigation tree to walk each
category page. Some Wix deployments refuse to render product cards when they
suspect automation; in that case, the command logs warnings and falls back to
the sitemap strategy.

## Outputs

- `scraper/data/product_images/<product_id>_<slug>.jpg` – local image copies
  (products without downloadable images are omitted).
- `scraper/data/catalog.json` – machine-friendly manifest of every
  scraped product (IDs, names, source URLs, and local file paths).

### Known alias URLs

A handful of sitemap entries reuse the same `product_id` (e.g., multiple `tea-set`
and `lucky-cat` landing pages) or omit downloadable images. The scraper keeps the
canonical record per product ID, so these aliases are intentionally skipped:

- `https://www.eshouseware.com/product-page/tea-set`
- `https://www.eshouseware.com/product-page/tea-set-1`
- `https://www.eshouseware.com/product-page/tea-set-2213`
- `https://www.eshouseware.com/product-page/lucky-cat-1`
- `https://www.eshouseware.com/product-page/802832-chopstick-rest-white-白瓷筷子架-強化瓷-36-pcs`
- `https://www.eshouseware.com/product-page/802833-spoon-chopstick-rest-white-3-5-白瓷湯匙筷子架-強化瓷-12-pcs`
- `https://www.eshouseware.com/product-page/802881-11-wate-rect-plate-white-波浪長方深盤`
- `https://www.eshouseware.com/product-page/800224-stainless-steel-glass-lid-cookware-lid-34-cm-13-39-不銹鋼和玻璃組合蓋`
- `https://www.eshouseware.com/product-page/mop-spare-part-refill-head-item-00805022head`
- `https://www.eshouseware.com/product-page/805012-european-style-dust-pan-gray-歐式畚箕`
- `https://www.eshouseware.com/product-page/ae-066-japanese-donburi-bowl-日本丼物碗-20-pcs`
- `https://www.eshouseware.com/product-page/dachu-beech-wood-chopsticks-10-pairs-天然櫸木筷`
- `https://www.eshouseware.com/product-page/802881-11-white-ceramic-wave-dinner-plate-白瓷盤`
- `https://www.eshouseware.com/product-page/821813-6-round-bowl-瓷碗-熊有成竹`
- `https://www.eshouseware.com/product-page/813100-es-s-s-peeler304-雅韵三角刨刀`
- `https://www.eshouseware.com/product-page/813101-es-s-s-peeler304-雅韵两用刨刀`
- `https://www.eshouseware.com/product-page/813102-es-s-s-peeler304-雅韵d型刨刀`
- `https://www.eshouseware.com/product-page/813103-es-s-s-peeler304-雅韵經典刨刀`
- `https://www.eshouseware.com/product-page/813104-es-s-s-peeler304-雅韵蔬菜刨刀`
- `https://www.eshouseware.com/product-page/813105-es-s-s-peeler-304-雅韵魚鱗刨刀`
- `https://www.eshouseware.com/product-page/j32455-455-japanese-sake-set-清酒杯組`
- `https://www.eshouseware.com/product-page/j32717-305-japanese-sake-set-清酒杯組`
- `https://www.eshouseware.com/product-page/j32629-305-japanese-sake-set-清酒杯組`
- `https://www.eshouseware.com/product-page/j32644-455-japanese-sake-set-清酒杯組`

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist` | Run `playwright install` inside the active venv. |
| `requests.exceptions.SSLError` | Re-run with `SSL_CERT_FILE` configured or pass `--insecure` (see CLI help). |
| Scraper stops mid-run | Re-run with `--resume` to pick up where it left off; already-downloaded items are skipped. |

## License / Scope

The scraper is part of the Inventory PO Web App repository and inherits the
same private/internal usage constraints. No external distribution is intended.
