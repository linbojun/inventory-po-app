"""Store sitemap helpers."""
from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional

import requests

from .product_page import ProductPageParser, ProductRecord

LOGGER = logging.getLogger(__name__)
SITEMAP_NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}
DEFAULT_SITEMAP_URL = "https://www.eshouseware.com/store-products-sitemap.xml"


@dataclass
class SitemapEntry:
    product_url: str
    image_url: Optional[str]
    lastmod: Optional[str]


class SitemapClient:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def download(self, url: str, timeout: float = 60.0) -> str:
        LOGGER.info("Downloading sitemap: %s", url)
        resp = self.session.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text


class SitemapScraper:
    def __init__(
        self,
        sitemap_url: str = DEFAULT_SITEMAP_URL,
        session: Optional[requests.Session] = None,
        throttle_seconds: float = 0.15,
        cache_path: Optional[Path] = None,
    ) -> None:
        self.sitemap_url = sitemap_url
        self.session = session or requests.Session()
        self.client = SitemapClient(self.session)
        self.parser = ProductPageParser()
        self.throttle_seconds = throttle_seconds
        self.cache_path = cache_path

    def _load_sitemap_xml(self) -> str:
        if self.cache_path and self.cache_path.exists():
            LOGGER.info("Using cached sitemap %s", self.cache_path)
            return self.cache_path.read_text()
        xml_text = self.client.download(self.sitemap_url)
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(xml_text)
        return xml_text

    def iter_entries(self) -> List[SitemapEntry]:
        xml_text = self._load_sitemap_xml()
        root = ET.fromstring(xml_text)
        entries: List[SitemapEntry] = []
        for node in root.findall("sm:url", SITEMAP_NS):
            loc = node.findtext("sm:loc", namespaces=SITEMAP_NS)
            img = node.find("image:image/image:loc", SITEMAP_NS)
            lastmod = node.findtext("sm:lastmod", namespaces=SITEMAP_NS)
            if loc:
                entries.append(
                    SitemapEntry(
                        product_url=loc.strip(),
                        image_url=img.text.strip() if img is not None and img.text else None,
                        lastmod=lastmod.strip() if lastmod else None,
                    )
                )
        LOGGER.info("Parsed %s product URLs from sitemap", len(entries))
        return entries

    def iter_products(self, limit: Optional[int] = None) -> Iterator[ProductRecord]:
        entries = self.iter_entries()
        count = 0
        for entry in entries:
            if limit and count >= limit:
                break
            try:
                record = self._fetch_product(entry)
            except Exception as exc:  # pragma: no cover - network issues
                LOGGER.warning("Failed to fetch %s: %s", entry.product_url, exc)
                continue
            count += 1
            yield record
            time.sleep(self.throttle_seconds)

    def _fetch_product(self, entry: SitemapEntry) -> ProductRecord:
        resp = requests.get(entry.product_url, timeout=60)
        resp.raise_for_status()
        record = self.parser.parse(resp.text, url=entry.product_url)
        if entry.image_url and entry.image_url not in record.image_urls:
            record.image_urls.append(entry.image_url)
        return record

    def fetch_entry(self, entry: SitemapEntry) -> ProductRecord:
        return self._fetch_product(entry)
