#!/usr/bin/env python3
"""
Push scraped ES Houseware catalog rows into the production Inventory PO API.

Workflow (Option A from the README):
1. Read `scraper/data/catalog.json`.
2. Send POST /api/products for new SKUs (including the local hero image).
3. If a product already exists but lacks an image, upload the cached hero image
   via PUT /api/products/{id}.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import textwrap
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# Resolve repository root relative to this script (backend/scripts/.. -> backend -> repo root)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = REPO_ROOT / "scraper" / "data" / "catalog.json"
DEFAULT_LIMIT = 10
DEFAULT_TIMEOUT = (10, 60)  # connect, read


def _normalize_api_base(raw: str) -> str:
    base = raw.strip().rstrip("/")
    if not base:
        raise SystemExit(
            "Missing API base URL. Pass --api-base or set PROD_API_BASE / VITE_API_URL."
        )
    if not base.endswith("/api"):
        base = f"{base}/api"
    return base


def _load_catalog(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _clean_description(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = unescape(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    lines = [line.strip() for line in text.split("\n")]
    cleaned_lines = [line for line in lines if line]
    normalized = "\n".join(cleaned_lines).strip()
    return normalized or None


def _build_remarks(record: Dict[str, Any]) -> Optional[str]:
    parts = []
    description = _clean_description(record.get("description"))
    if description:
        parts.append(description)
    product_url = record.get("product_url")
    if product_url:
        parts.append(f"Source: {product_url}")
    if not parts:
        return None
    remarks = "\n\n".join(parts)
    # FastAPI normalizes blanks to None; keep length reasonable.
    if len(remarks) > 2000:
        remarks = remarks[:1997] + "..."
    return remarks


def _resolve_image_path(record: Dict[str, Any], repo_root: Path) -> Path:
    image_meta = record.get("image") or {}
    local_path = image_meta.get("local_path")
    if not local_path:
        raise RuntimeError(f"No local image path recorded for product {record.get('product_id')}")
    image_path = Path(local_path)
    if not image_path.is_absolute():
        image_path = (repo_root / image_path).resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    return image_path


def _guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        return mime
    return "application/octet-stream"


def _sorted_products(catalog: Dict[str, Any], limit: int) -> Dict[str, Dict[str, Any]]:
    products = catalog.get("products")
    if not isinstance(products, dict):
        raise SystemExit("catalog.json does not expose a top-level 'products' object.")
    ordered_ids = sorted(products.keys())
    slice_ids = ordered_ids[:limit]
    return {pid: products[pid] for pid in slice_ids}


def _fetch_existing_product(session: requests.Session, api_base: str, product_id: str) -> Optional[Dict[str, Any]]:
    resp = session.get(
        f"{api_base}/products",
        params={"search": product_id, "page_size": 1},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    payload = resp.json()
    for item in payload.get("items", []):
        if item.get("product_id") == product_id:
            return item
    return None


def _create_product(
    session: requests.Session,
    api_base: str,
    record: Dict[str, Any],
    image_path: Path,
) -> Dict[str, Any]:
    remarks = _build_remarks(record)
    data = {
        "product_id": record["product_id"],
        "name": record["name"],
        "price": str(record.get("price") or 0),
        "stock": "0",
        "order_qty": "0",
    }
    brand = (record.get("brand") or "").strip()
    if brand:
        data["brand"] = brand
    if remarks is not None:
        data["remarks"] = remarks

    with image_path.open("rb") as image_file:
        files = {
            "image": (
                image_path.name,
                image_file,
                _guess_mime(image_path),
            )
        }
        resp = session.post(
            f"{api_base}/products",
            data=data,
            files=files,
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()


def _update_product_image(
    session: requests.Session,
    api_base: str,
    product_id: int,
    image_path: Path,
) -> Dict[str, Any]:
    with image_path.open("rb") as image_file:
        files = {
            "image": (
                image_path.name,
                image_file,
                _guess_mime(image_path),
            )
        }
        resp = session.put(
            f"{api_base}/products/{product_id}",
            data={"force_new_image": "true"},
            files=files,
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()


@dataclass
class ImportStats:
    created: int = 0
    updated_images: int = 0
    skipped: int = 0
    failed: int = 0


def sync_products(api_base: str, catalog_path: Path, limit: int) -> ImportStats:
    catalog = _load_catalog(catalog_path)
    to_process = _sorted_products(catalog, limit)
    stats = ImportStats()
    session = requests.Session()
    session.headers.update({"User-Agent": "inventory-scraper-import/1.0"})

    for idx, (product_id, record) in enumerate(to_process.items(), start=1):
        print(f"[{idx}/{len(to_process)}] Syncing product {product_id} – {record.get('name')}")
        try:
            image_path = _resolve_image_path(record, REPO_ROOT)
            existing = _fetch_existing_product(session, api_base, product_id)
            if existing:
                if existing.get("image_url"):
                    stats.skipped += 1
                    print(f"  → Skipped (already exists with image: {existing['image_url']})")
                    continue
                updated = _update_product_image(session, api_base, existing["id"], image_path)
                stats.updated_images += 1
                print(f"  → Attached image to existing record (id={existing['id']})")
                print(f"    New image_url: {updated.get('image_url')}")
            else:
                created = _create_product(session, api_base, record, image_path)
                stats.created += 1
                print(f"  → Created new product (id={created.get('id')}) with image {created.get('image_url')}")
        except Exception as exc:
            stats.failed += 1
            print(f"  ! Failed to sync product {product_id}: {exc}")
    return stats


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import scraped ES Houseware catalog entries via the Inventory PO API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              # Import the first 10 products into production
              python backend/scripts/import_scraped_catalog.py \\
                  --api-base https://inventory-po-app.onrender.com/api

              # Dry run a smaller sample against staging
              python backend/scripts/import_scraped_catalog.py \\
                  --api-base https://inventory-po-staging.onrender.com/api \\
                  --limit 3
            """
        ),
    )
    parser.add_argument(
        "--api-base",
        dest="api_base",
        default=os.getenv("PROD_API_BASE") or os.getenv("VITE_API_URL"),
        help="Inventory PO API origin (with or without trailing /api). Defaults to PROD_API_BASE env.",
    )
    parser.add_argument(
        "--catalog",
        dest="catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help=f"Path to catalog.json (default: {DEFAULT_CATALOG})",
    )
    parser.add_argument(
        "--limit",
        dest="limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Number of products to import (default: {DEFAULT_LIMIT})",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    api_base = _normalize_api_base(args.api_base or "")
    catalog_path = args.catalog
    if not catalog_path.is_absolute():
        catalog_path = (REPO_ROOT / catalog_path).resolve()
    if not catalog_path.exists():
        raise SystemExit(f"Catalog file not found: {catalog_path}")
    stats = sync_products(api_base, catalog_path, args.limit)
    print(
        "\nSummary:"
        f"\n  Created: {stats.created}"
        f"\n  Updated images: {stats.updated_images}"
        f"\n  Skipped: {stats.skipped}"
        f"\n  Failed: {stats.failed}"
    )
    return 0 if stats.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

