# Scraper Changelog

## [0.1.5] - 2026-01-10

### Fixed
**Why**: Catalog consumers expect the `name` field to be human-friendly. Prefixing
it with `#<product_id>` made downstream displays redundant and forced extra
string trimming.

**What**:
- Parser now strips the product ID prefix before emitting each `ProductRecord`.
- Updated the regression test to assert the cleaned behavior.
- Regenerated `scraper/data/catalog.json` so existing manifests mirror the new
  format.

**Benefits**:
- Cleaner catalog entries and UI labels (product ID remains available via its
  dedicated field).
- No more post-processing needed when importing the dataset elsewhere.

## [0.1.4] - 2026-01-10

### Changed
**Why**: Catalog rows without images forced consumers to special-case empty
assets, defeating the goal of mirroring the storefront’s visuals.

**What**:
- The sitemap and dynamic pipelines now skip any product whose image download
  fails (no URLs, missing binaries, 404s, etc.).
- Documentation (SCRAPER_README, DESIGN, PLAN, root README, project changelog)
  highlights that image-less entries are intentionally omitted.

**Benefits**:
- Keeps disk usage limited to actionable products.
- Guarantees every manifest entry references a real file under
  `scraper/data/product_images/`.

## [0.1.3] - 2026-01-10

### Changed
**Why**: Separating binary blobs from other cached artifacts (site map, manifest)
inside the `scraper/data/` tree keeps clean-room runs simple (delete one folder,
re-run) and gives downstream tooling a predictable path.

**What**:
- Default image output now points to `scraper/data/product_images/`.
- Documentation (SCRAPER_README, DESIGN, PLAN, root README) and the project
  changelog highlight the new directory layout so future scripts rely on the
  same structure.
- Noted the change here for visibility.

## [0.1.2] - 2026-01-10

### Changed
**Why**: Keep all scraper outputs co-located under `scraper/data/` so the workspace is self-contained and does not depend on the backend's `static` tree.

**What**:
- Pointed the CLI defaults (`--output`, `--manifest`, and `inspect-manifest`) to `scraper/data/`.
- Updated every scraper doc (README, DESIGN, PLAN) to describe the new storage location for images and the catalog manifest.

## [0.1.1] - 2026-01-10

### Changed
- Prefixed every Markdown artifact (README, DESIGN, CHANGELOG, PLAN,
  TEST_PROPOSAL) with `SCRAPER_` to make them easier to distinguish from
  similarly named files in the root project and updated internal references
  accordingly.

## [0.1.0] - 2026-01-10

### Added
- Initial navigation parser (`navigation.py`) that captures the ES Houseware mega
  menu and caches it under `scraper/data/site_map.json`.
- Sitemap-driven product harvester that parses every product page's JSON-LD,
  downloads hero images to `scraper/data/`, and emits a normalized
  catalog manifest.
- Experimental Playwright driver for categories + pagination.
- Typer-based CLI (`python -m es_scraper.cli`) with `nav`, `run`, and
  `inspect-manifest` commands.
- pytest fixtures for the homepage/menu and representative product page markup.
