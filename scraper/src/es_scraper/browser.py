"""Playwright helpers."""
from __future__ import annotations

import contextlib
import logging
import time
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import Page, Playwright, TimeoutError as PlaywrightTimeoutError, sync_playwright

LOGGER = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    headless: bool = True
    slow_mo: Optional[int] = None
    timeout_ms: int = 60_000
    retries: int = 2
    wait_until: str = "networkidle"


class BrowserSession:
    """Context manager that exposes a single Playwright instance."""

    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._playwright: Optional[Playwright] = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "BrowserSession":
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
        )
        self._context = self._browser.new_context()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        with contextlib.suppress(Exception):
            if self._context:
                self._context.close()
        with contextlib.suppress(Exception):
            if self._browser:
                self._browser.close()
        with contextlib.suppress(Exception):
            if self._playwright:
                self._playwright.stop()

    def new_page(self) -> Page:
        if not self._context:
            raise RuntimeError("BrowserSession not started")
        page = self._context.new_page()
        page.set_default_timeout(self.config.timeout_ms)
        return page

    def navigate(self, page: Page, url: str) -> None:
        """Navigate with basic retry/backoff."""
        for attempt in range(1, self.config.retries + 2):
            try:
                LOGGER.debug("Navigating to %s (attempt %s)", url, attempt)
                page.goto(url, wait_until=self.config.wait_until, timeout=self.config.timeout_ms)
                return
            except PlaywrightTimeoutError as exc:  # pragma: no cover - network variance
                LOGGER.warning("Timeout visiting %s: %s", url, exc)
                if attempt > self.config.retries:
                    raise
                time.sleep(2 * attempt)
