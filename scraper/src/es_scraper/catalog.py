"""Catalog manifest helpers."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field

from .product_page import ProductRecord

LOGGER = logging.getLogger(__name__)


class ImageInfo(BaseModel):
    source_url: str
    local_path: Optional[str] = None


class CatalogEntry(BaseModel):
    product_id: str
    name: str
    slug: str
    product_url: str
    description: str = ""
    sku: Optional[str] = None
    image: ImageInfo


class CatalogDocument(BaseModel):
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str
    product_count: int
    products: Dict[str, CatalogEntry]


@dataclass
class CatalogStore:
    path: Path
    source: str

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._doc = CatalogDocument(**raw)
        else:
            self._doc = CatalogDocument(source=self.source, product_count=0, products={})

    def contains(self, product_id: str) -> bool:
        return product_id in self._doc.products

    def upsert(self, record: ProductRecord, image_path: Optional[Path]) -> CatalogEntry:
        entry = CatalogEntry(
            product_id=record.product_id,
            name=record.name,
            slug=record.slug,
            product_url=record.product_url,
            description=record.description,
            sku=record.sku,
            image=ImageInfo(
                source_url=record.image_urls[0] if record.image_urls else "",
                local_path=image_path.as_posix() if image_path else None,
            ),
        )
        self._doc.products[record.product_id] = entry
        self._doc.product_count = len(self._doc.products)
        return entry

    def save(self) -> None:
        payload = self._doc.model_dump(mode="json", by_alias=True)
        payload["products"] = {
            product_id: entry.model_dump(mode="json", by_alias=True)
            for product_id, entry in sorted(self._doc.products.items())
        }
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        LOGGER.info("Catalog saved to %s (%s products)", self.path, self._doc.product_count)
