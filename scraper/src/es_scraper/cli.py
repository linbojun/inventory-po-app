"""Typer-based CLI entry point."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import typer

from .browser import BrowserConfig
from .catalog import CatalogStore
from .downloader import ImageDownloader
from .navigation import BASE_URL, ensure_site_map, load_site_map
from .product_scraper import harvest_from_dynamic, harvest_from_sitemap
from .sitemap import DEFAULT_SITEMAP_URL, SitemapScraper

app = typer.Typer(help="ES Houseware scraper")


@app.callback()
def configure_logging(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


@app.command()
def nav(
    output: Path = typer.Option(Path("scraper/data/site_map.json"), help="Cache path for the site map"),
    refresh: bool = typer.Option(False, help="Force refresh even if cache exists"),
    base_url: str = typer.Option(BASE_URL, help="Base URL to fetch navigation from"),
) -> None:
    path = ensure_site_map(output, base_url=base_url, refresh=refresh)
    typer.echo(f"Navigation cached at {path}")


@app.command()
def run(
    mode: str = typer.Option("sitemap", help="sitemap|dynamic"),
    limit: Optional[int] = typer.Option(None, help="Process only the first N products"),
    sitemap_url: str = typer.Option(DEFAULT_SITEMAP_URL, help="Store sitemap URL"),
    nav_cache: Path = typer.Option(Path("scraper/data/site_map.json"), help="Cached navigation JSON"),
    output: Path = typer.Option(Path("scraper/data/product_images"), help="Image output directory"),
    manifest: Path = typer.Option(Path("scraper/data/catalog.json"), help="Catalog manifest path"),
    throttle: float = typer.Option(0.15, help="Seconds to wait between network calls"),
    skip_download: bool = typer.Option(False, help="Do not persist images (for dry runs)"),
    resume: bool = typer.Option(True, help="Skip products already present in the manifest"),
    refresh_nav: bool = typer.Option(False, help="Refresh navigation before running dynamic mode"),
    workers: int = typer.Option(8, help="Number of concurrent workers for sitemap mode"),
    retries: int = typer.Option(2, help="Retries per product when the site rate-limits us"),
) -> None:
    catalog = CatalogStore(path=manifest, source=sitemap_url)
    downloader = ImageDownloader(output_dir=output, skip_download=skip_download)

    if mode.lower() == "sitemap":
        scraper = SitemapScraper(
            sitemap_url=sitemap_url,
            cache_path=None,
        )
        processed = harvest_from_sitemap(
            scraper,
            downloader,
            catalog,
            limit=limit,
            skip_existing=resume,
            workers=workers,
            throttle_seconds=throttle,
            max_retries=retries,
        )
        typer.echo(f"Sitemap scraper finished, {processed} products processed")
        return

    if mode.lower() == "dynamic":
        ensure_site_map(nav_cache, refresh=refresh_nav)
        categories = load_site_map(nav_cache)
        browser_config = BrowserConfig(headless=True)
        processed = harvest_from_dynamic(
            categories,
            downloader,
            catalog,
            limit=limit,
            browser_config=browser_config,
            skip_existing=resume,
        )
        typer.echo(f"Dynamic scraper finished, {processed} products processed")
        return

    raise typer.BadParameter("mode must be either 'sitemap' or 'dynamic'")


@app.command("inspect-manifest")
def inspect_manifest(manifest: Path = typer.Argument(Path("scraper/data/catalog.json"))) -> None:
    if not manifest.exists():
        typer.echo(f"Manifest not found: {manifest}")
        raise typer.Exit(code=1)
    data = json.loads(manifest.read_text())
    typer.echo(f"Products: {len(data.get('products', {}))}")
    typer.echo(f"Scraped at: {data.get('scraped_at')}")


if __name__ == "__main__":
    app()
