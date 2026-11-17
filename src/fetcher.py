"""Polite HTTP fetcher with local disk caching, politeness delay, and retry logic."""

import hashlib
import logging
import re
import time
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests

from src.config import CACHE_DIR, POLITE_DELAY_SECONDS, REQUEST_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)


def url_to_cache_filename(url: str) -> str:
    """Generate a clean, filesystem-safe filename for a cached URL.
    
    Preserves readable paths like 'catalogue/page-1.html' -> 'catalogue-page-1.html'.
    """
    parsed = urlparse(url)
    clean_path = parsed.path.strip("/").replace("/", "-")
    if not clean_path:
        clean_path = "index.html"
    elif not clean_path.endswith(".html"):
        clean_path += ".html"
    
    # Sanitize special characters
    clean_path = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", clean_path)
    # Ensure reasonable filename length
    if len(clean_path) > 180:
        hash_suffix = hashlib.sha256(url.encode()).hexdigest()[:10]
        clean_path = clean_path[:170] + f"_{hash_suffix}.html"
    return clean_path


class FetchResult:
    """Result of a fetch operation."""
    def __init__(self, content: str, from_cache: bool, status_code: int, size_bytes: int, url: str):
        self.content = content
        self.from_cache = from_cache
        self.status_code = status_code
        self.size_bytes = size_bytes
        self.url = url


class PoliteFetcher:
    """HTTP fetcher implementing politeness, caching, and resilient retries."""

    def __init__(
        self,
        cache_dir: Path = CACHE_DIR,
        timeout: float = REQUEST_TIMEOUT,
        delay_seconds: float = POLITE_DELAY_SECONDS,
        user_agent: str = USER_AGENT,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.user_agent = user_agent
        self.last_request_time: float = 0.0

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

        # Observability counters
        self.pages_fetched = 0
        self.cache_hits = 0
        self.failed_pages = 0

    def get_cache_path(self, url: str) -> Path:
        """Return the cache file path for a given URL."""
        return self.cache_dir / url_to_cache_filename(url)

    def fetch(self, url: str, force_live: bool = False) -> Optional[FetchResult]:
        """Fetch URL content from cache or live network.
        
        Returns FetchResult on success, or None on failure.
        """
        cache_path = self.get_cache_path(url)

        # 1. Check cache first
        if not force_live and cache_path.exists():
            try:
                content = cache_path.read_text(encoding="utf-8")
                size_bytes = len(content.encode("utf-8"))
                self.cache_hits += 1
                print(f"[CACHE HIT] {cache_path} ({size_bytes} bytes)")
                return FetchResult(
                    content=content,
                    from_cache=True,
                    status_code=200,
                    size_bytes=size_bytes,
                    url=url,
                )
            except Exception as e:
                logger.warning(f"Error reading cache {cache_path}: {e}")

        # 2. Politeness rate limiting: enforce delay between live requests
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.delay_seconds:
            sleep_time = self.delay_seconds - elapsed
            time.sleep(sleep_time)

        # 3. Live request with retry for 5xx or timeouts (Milestone 5)
        # Note: 404 and 403 are terminal and must NOT be retried
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                self.last_request_time = time.time()
                response = self.session.get(url, timeout=self.timeout)

                # Check status code strictly
                if response.status_code == 200:
                    content = response.text
                    size_bytes = len(response.content)
                    self.pages_fetched += 1

                    # Save to cache
                    try:
                        cache_path.write_text(content, encoding="utf-8")
                    except Exception as e:
                        logger.warning(f"Could not write cache to {cache_path}: {e}")

                    print(f"[FETCH] {url} ({size_bytes} bytes)")
                    return FetchResult(
                        content=content,
                        from_cache=False,
                        status_code=200,
                        size_bytes=size_bytes,
                        url=url,
                    )

                # Non-200 responses
                logger.warning(f"Fetch failed with status {response.status_code} for {url}")
                if response.status_code in (403, 404):
                    # Do NOT retry 404 or 403
                    self.failed_pages += 1
                    return None

                # 5xx or other status: allow one retry
                if attempt < max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    wait_time = float(retry_after) if retry_after and retry_after.isdigit() else 1.0
                    time.sleep(wait_time)
                    continue

                self.failed_pages += 1
                return None

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logger.warning(f"Attempt {attempt} connection/timeout error for {url}: {e}")
                if attempt < max_attempts:
                    time.sleep(1.0)
                    continue
                self.failed_pages += 1
                return None
            except Exception as e:
                logger.error(f"Unexpected fetch error for {url}: {e}")
                self.failed_pages += 1
                return None

        self.failed_pages += 1
        return None
