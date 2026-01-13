"""Image download helpers."""
from __future__ import annotations

import hashlib
import logging
import re
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

from .product_page import ProductRecord

LOGGER = logging.getLogger(__name__)


_SLUG_RE = re.compile(r"[^a-zA-Z0-9]+")


def slugify(value: str) -> str:
    return _SLUG_RE.sub("-", value).strip("-").lower() or "item"


class ImageDownloader:
    def __init__(
        self,
        output_dir: Path,
        session: Optional[requests.Session] = None,
        skip_download: bool = False,
    ) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = session
        self.skip_download = skip_download

    def download_primary(self, record: ProductRecord) -> Optional[Path]:
        if not record.image_urls:
            LOGGER.warning("No image URLs found for %s", record.product_url)
            return None
        for image_url in record.image_urls:
            path = self._target_path(record, image_url)
            if path.exists():
                LOGGER.debug("Image already present: %s", path)
                return path
            if self.skip_download:
                LOGGER.info("skip-download enabled, not fetching %s", image_url)
                return path
            try:
                self._stream(image_url, path)
                return path
            except Exception as exc:  # pragma: no cover - network variance
                LOGGER.warning("Failed to download %s: %s", image_url, exc)
        return None

    def _target_path(self, record: ProductRecord, image_url: str) -> Path:
        parsed = urlparse(image_url)
        ext = Path(parsed.path).suffix or ".jpg"
        digest = hashlib.sha1(image_url.encode("utf-8")).hexdigest()[:8]
        filename = f"{record.product_id}_{slugify(record.slug)}_{digest}{ext}"
        return self.output_dir / filename

    def _stream(self, url: str, dst: Path) -> None:
        LOGGER.debug("Downloading %s -> %s", url, dst)
        client = self.session or requests
        response = client.get(url, stream=True, timeout=120)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    tmp.write(chunk)
            tmp_path = Path(tmp.name)
        tmp_path.replace(dst)
