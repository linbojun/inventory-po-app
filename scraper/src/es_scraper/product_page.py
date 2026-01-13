"""Product page parsing helpers."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)

PRODUCT_ID_RE = re.compile(r"#\s*([A-Za-z0-9\-]+)")
SLUG_RE = re.compile(r"product-page/([^/?#]+)")


@dataclass
class ProductRecord:
    product_id: str
    name: str
    slug: str
    description: str
    sku: Optional[str]
    product_url: str
    image_urls: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)


class ProductPageParser:
    """Parse eshouseware product pages using the JSON-LD payload."""

    def parse(self, html: str, url: str) -> ProductRecord:
        soup = BeautifulSoup(html, "html.parser")
        data = self._extract_schema_product(soup)
        if not data:
            raise ValueError("Product JSON-LD payload not found")

        name = data.get("name") or self._fallback_title(soup)
        product_id = self._extract_product_id(name, url)
        name = self._strip_product_id_prefix(name, product_id)
        slug = self._extract_slug(url)
        description = (data.get("description") or "").strip()
        sku = data.get("sku")
        image_urls = self._extract_images(data)

        return ProductRecord(
            product_id=product_id,
            name=name.strip(),
            slug=slug,
            description=description,
            sku=sku,
            product_url=url,
            image_urls=image_urls,
        )

    @staticmethod
    def _extract_schema_product(soup: BeautifulSoup) -> Optional[dict]:
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            payload = script.string
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                LOGGER.debug("Skipping unparsable JSON-LD block")
                continue
            if isinstance(data, list):
                for entry in data:
                    if ProductPageParser._is_product(entry):
                        return entry
            elif ProductPageParser._is_product(data):
                return data
        return None

    @staticmethod
    def _is_product(payload: dict) -> bool:
        type_value = payload.get("@type")
        if isinstance(type_value, list):
            return any(t.lower() == "product" for t in type_value)
        return isinstance(type_value, str) and type_value.lower() == "product"

    @staticmethod
    def _extract_product_id(name: str, url: str) -> str:
        match = PRODUCT_ID_RE.search(name)
        if match:
            return match.group(1)
        slug = ProductPageParser._extract_slug(url)
        if slug:
            return slug.split("-")[0].upper()
        raise ValueError("Unable to derive product_id")

    @staticmethod
    def _extract_slug(url: str) -> str:
        match = SLUG_RE.search(url)
        if match:
            return match.group(1)
        parsed = urlparse(url)
        return parsed.path.strip("/")

    @staticmethod
    def _extract_images(data: dict) -> List[str]:
        images = data.get("image")
        urls: List[str] = []
        if isinstance(images, list):
            for item in images:
                if isinstance(item, str):
                    urls.append(item)
                elif isinstance(item, dict) and item.get("contentUrl"):
                    urls.append(item["contentUrl"])
        elif isinstance(images, dict) and images.get("contentUrl"):
            urls.append(images["contentUrl"])
        elif isinstance(images, str):
            urls.append(images)
        return list(dict.fromkeys(urls))

    @staticmethod
    def _fallback_title(soup: BeautifulSoup) -> str:
        title = soup.find("title")
        if title and title.string:
            return title.string
        return ""

    @staticmethod
    def _strip_product_id_prefix(name: str, product_id: str) -> str:
        if not name:
            return ""
        pattern = re.compile(
            rf"^\s*#?\s*{re.escape(product_id)}\s*[-:–—]?\s*",
            flags=re.IGNORECASE,
        )
        return pattern.sub("", name, count=1)
