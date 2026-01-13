"""Scraper pipelines (sitemap + dynamic)."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import islice
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple
import time

import requests

from .browser import BrowserConfig, BrowserSession
from .catalog import CatalogStore
from .downloader import ImageDownloader
from .navigation import Category
from .product_page import ProductPageParser
from .sitemap import SitemapEntry, SitemapScraper

LOGGER = logging.getLogger(__name__)


def harvest_from_sitemap(
    scraper: SitemapScraper,
    downloader: ImageDownloader,
    catalog: CatalogStore,
    limit: Optional[int] = None,
    skip_existing: bool = True,
    workers: int = 8,
    throttle_seconds: float = 0.0,
    max_retries: int = 2,
) -> int:
    """Download products using the store sitemap."""
    entries = scraper.iter_entries()
    if limit:
        entries = entries[:limit]

    processed = 0

    def _worker(entry: SitemapEntry):
        attempt = 0
        while True:
            if throttle_seconds > 0:
                time.sleep(throttle_seconds)
            try:
                return scraper.fetch_entry(entry)
            except Exception as exc:
                attempt += 1
                if attempt > max_retries:
                    raise
                sleep_for = min(2 ** attempt, 5)
                LOGGER.debug(
                    "Retrying %s (attempt %s/%s) after error: %s",
                    entry.product_url,
                    attempt,
                    max_retries,
                    exc,
                )
                time.sleep(sleep_for)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(_worker, entry): entry for entry in entries}
        for future in as_completed(future_map):
            entry = future_map[future]
            try:
                record = future.result()
            except Exception as exc:  # pragma: no cover - network variance
                LOGGER.warning("Failed to fetch %s: %s", entry.product_url, exc)
                continue
            if skip_existing and catalog.contains(record.product_id):
                continue
            image_path = downloader.download_primary(record)
            if not image_path:
                LOGGER.info(
                    "Skipping %s (%s) because no image could be downloaded",
                    record.product_id,
                    record.product_url,
                )
                continue
            catalog.upsert(record, image_path)
            processed += 1
    catalog.save()
    return processed


def harvest_from_dynamic(
    categories: Sequence[Category],
    downloader: ImageDownloader,
    catalog: CatalogStore,
    limit: Optional[int] = None,
    browser_config: Optional[BrowserConfig] = None,
    skip_existing: bool = True,
) -> int:
    """Experimental Playwright-based category crawl."""
    parser = ProductPageParser()
    session = requests.Session()
    visited: set[str] = set()
    processed = 0

    with BrowserSession(browser_config) as browser:
        page = browser.new_page()
        for category_path, url in _flatten_categories(categories):
            if limit and processed >= limit:
                break
            try:
                browser.navigate(page, url)
            except Exception as exc:  # pragma: no cover - automation variance
                LOGGER.warning("Unable to open %s: %s", url, exc)
                continue

            product_links = _extract_product_links(page)
            if not product_links:
                LOGGER.warning("No product links detected on %s", url)
                continue

            for link in product_links:
                clean_url = link.split("?")[0]
                if clean_url in visited:
                    continue
                visited.add(clean_url)
                try:
                    resp = session.get(clean_url, timeout=60)
                    resp.raise_for_status()
                    record = parser.parse(resp.text, url=clean_url)
                except Exception as exc:  # pragma: no cover
                    LOGGER.warning("Failed to parse %s: %s", clean_url, exc)
                    continue

                if skip_existing and catalog.contains(record.product_id):
                    continue
                image_path = downloader.download_primary(record)
                if not image_path:
                    LOGGER.info(
                        "Skipping %s (%s) because no image could be downloaded",
                        record.product_id,
                        record.product_url,
                    )
                    continue
                catalog.upsert(record, image_path)
                processed += 1
                if limit and processed >= limit:
                    break

    catalog.save()
    return processed


def _extract_product_links(page) -> List[str]:  # pragma: no cover - requires browser
    try:
        links = page.eval_on_selector_all(
            'a[href*="/product-page/"]',
            'els => Array.from(new Set(els.map(el => el.href)))'
        )
        return links or []
    except Exception as exc:
        LOGGER.warning("Could not evaluate product links: %s", exc)
        return []


def _flatten_categories(categories: Sequence[Category]) -> Iterator[Tuple[List[str], str]]:
    for category in categories:
        if not category.subcategories:
            yield ([category.name], category.url)
        else:
            for sub in category.subcategories:
                yield ([category.name, sub.name], sub.url)
