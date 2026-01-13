"""Navigation parser for eshouseware.com."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.eshouseware.com/"


@dataclass
class Subcategory:
    name: str
    url: str


@dataclass
class Category:
    name: str
    url: str
    subcategories: List[Subcategory] = field(default_factory=list)


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def parse_navigation_html(html: str, base_url: str = BASE_URL) -> List[Category]:
    """Parse the rendered navigation menu into a structured list."""
    soup = BeautifulSoup(html, "html.parser")
    nav = soup.find("nav")
    if nav is None:
        raise ValueError("Navigation element not found in supplied HTML")

    ul = nav.find("ul")
    if ul is None:
        raise ValueError("Navigation list not found")

    categories: List[Category] = []
    for li in ul.find_all("li", recursive=False):
        anchors = [a for a in li.find_all("a") if a.get("href")]
        if not anchors:
            continue

        top_anchor = anchors[0]
        top_name = _normalize_text(top_anchor.get_text(strip=True))
        top_url = urljoin(base_url, top_anchor.get("href"))

        subcategories: List[Subcategory] = []
        seen: set[tuple[str, str]] = set()
        for sub_anchor in anchors[1:]:
            name = _normalize_text(sub_anchor.get_text(strip=True))
            href = sub_anchor.get("href")
            if not name or not href:
                continue
            key = (name, href)
            if key in seen or name == top_name:
                continue
            seen.add(key)
            subcategories.append(Subcategory(name=name, url=urljoin(base_url, href)))

        categories.append(Category(name=top_name, url=top_url, subcategories=subcategories))

    return categories


def fetch_navigation(base_url: str = BASE_URL, timeout: float = 30.0) -> List[Category]:
    """Download the homepage and parse its navigation menu."""
    LOGGER.info("Fetching navigation from %s", base_url)
    response = requests.get(base_url, timeout=timeout)
    response.raise_for_status()
    return parse_navigation_html(response.text, base_url=base_url)


def dump_site_map(categories: Iterable[Category], output_path: Path) -> None:
    """Serialize the navigation tree to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "name": cat.name,
            "url": cat.url,
            "subcategories": [asdict(sub) for sub in cat.subcategories],
        }
        for cat in categories
    ]
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    LOGGER.info("Navigation cached at %s", output_path)


def load_site_map(path: Path) -> List[Category]:
    """Load a previously cached navigation tree."""
    data = json.loads(path.read_text())
    categories = []
    for entry in data:
        subs = [Subcategory(**sub) for sub in entry.get("subcategories", [])]
        categories.append(Category(name=entry["name"], url=entry["url"], subcategories=subs))
    return categories


def ensure_site_map(path: Path, base_url: str = BASE_URL, refresh: bool = False) -> Path:
    """Create the navigation cache if missing (or when refresh=True)."""
    if not path.exists() or refresh:
        categories = fetch_navigation(base_url=base_url)
        dump_site_map(categories, path)
    return path
