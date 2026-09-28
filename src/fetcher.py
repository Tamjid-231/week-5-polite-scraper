"""Polite, cache-aware HTTP fetching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Callable

import requests


class FetchError(RuntimeError):
    """Raised when a page cannot be fetched safely."""


@dataclass
class FetchStats:
    pages_fetched: int = 0
    cache_hits: int = 0


class PoliteFetcher:
    def __init__(
        self,
        cache_dir: Path,
        user_agent: str,
        timeout_seconds: float = 10.0,
        delay_seconds: float = 0.5,
        *,
        session: requests.Session | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self.cache_dir = cache_dir
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.delay_seconds = delay_seconds
        self.session = session or requests.Session()
        self.sleep_fn = sleep_fn
        self.monotonic_fn = monotonic_fn
        self.stats = FetchStats()
        self._last_request_at: float | None = None

    def fetch(self, url: str, cache_key: str) -> str:
        cache_path = self._cache_path(cache_key)
        if cache_path.is_file() and cache_path.stat().st_size > 0:
            html = cache_path.read_text(encoding="utf-8")
            print(f"CACHE HIT {url} bytes={len(html.encode('utf-8'))}")
            self.stats.cache_hits += 1
            return html

        last_error = "unknown error"
        for attempt in range(2):
            self._wait_before_request()
            try:
                response = self.session.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout_seconds,
                )
            except requests.Timeout as exc:
                last_error = f"timeout: {exc}"
                if attempt == 0:
                    continue
                raise FetchError(f"Failed to fetch {url} after retry ({last_error})") from exc
            except requests.RequestException as exc:
                raise FetchError(f"Failed to fetch {url}: {exc}") from exc
            finally:
                self._last_request_at = self.monotonic_fn()

            status = response.status_code
            if status == 200:
                if not response.text:
                    raise FetchError(f"Empty response from {url}")
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(response.text, encoding="utf-8")
                self.stats.pages_fetched += 1
                print(f"FETCH {url} bytes={len(response.content)}")
                return response.text

            last_error = f"HTTP {status}"
            if 500 <= status <= 599 and attempt == 0:
                continue
            raise FetchError(f"Failed to fetch {url}: {last_error}")

        raise FetchError(f"Failed to fetch {url} after retry ({last_error})")

    def _wait_before_request(self) -> None:
        if self._last_request_at is None:
            return
        elapsed = self.monotonic_fn() - self._last_request_at
        remaining = self.delay_seconds - elapsed
        if remaining > 0:
            self.sleep_fn(remaining)

    def _cache_path(self, cache_key: str) -> Path:
        root = self.cache_dir.resolve()
        path = (root / cache_key).resolve()
        if path != root and root not in path.parents:
            raise ValueError("cache_key must stay inside the cache directory")
        return path
