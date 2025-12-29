"""
Collect text from up to N pages under a root URL (same host), limited by max depth,
and save results to a binary file (gzip-compressed pickle).

Usage:
  python3 -m bluer_agent.crawl.collect \
    --root https://badkoobeh.com/ \
    --page-count 25 \
    --max-depth 2 \
    --out site_text.pkl.gz
"""

from __future__ import annotations


import random
import re
import signal
import time
from collections import deque
from contextlib import suppress
from typing import Deque, Dict, Iterable, Optional, Set
from urllib.parse import urljoin, urldefrag, urlparse
import requests
from bs4 import BeautifulSoup

from bluer_options.logger.config import shorten_text

from bluer_agent.crawl.classes import CrawlItem, RetryPolicy
from bluer_agent.logger import logger


class SiteTextCollector:
    def __init__(
        self,
        root_url: str,
        *,
        user_agent: str = "Mozilla/5.0 (compatible; SiteTextCollector/1.1)",
        accept_language: str = "fa,en;q=0.8",
        retry: RetryPolicy = RetryPolicy(),
    ):
        self.root_url = self._normalize_root(root_url)
        self.retry = retry

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": accept_language,
            }
        )

        # Ctrl+C / SIGINT handling
        self._stop_requested: bool = False
        self._old_sigint_handler = None

    def _on_sigint(self, signum, frame) -> None:
        # First Ctrl+C: request a graceful stop
        if not self._stop_requested:
            self._stop_requested = True
            logger.warning(
                "Ctrl+C received: stopping after current step, will save partial results..."
            )
        else:
            # Second Ctrl+C: hard exit
            logger.warning("Ctrl+C received again: exiting immediately.")
            raise KeyboardInterrupt

    @staticmethod
    def _normalize_url(url: str) -> str:
        url, _ = urldefrag(url)  # remove #fragment
        return url.strip()

    @staticmethod
    def _url_key(url: str) -> str:
        """
        Canonical key used for de-duping.
        Treat https://badkoobeh.com and https://badkoobeh.com/ as identical.
        Only collapses the trailing slash for the *root path*.
        """
        url = SiteTextCollector._normalize_url(url)
        p = urlparse(url)

        # Only normalize the root path "/" (or empty) to no trailing slash.
        if p.scheme and p.netloc and (p.path in ("", "/")) and not p.query:
            return f"{p.scheme}://{p.netloc}"
        return url

    def _normalize_root(self, root_url: str) -> str:
        root = self._normalize_url(root_url)
        # Make urljoin predictable for relative paths:
        if not root.endswith("/"):
            root += "/"
        return root

    def _same_site(self, url: str) -> bool:
        u = urlparse(url)
        r = urlparse(self.root_url)
        if not (u.scheme and u.netloc):
            return False
        if u.scheme not in ("http", "https"):
            return False
        # strict match (scheme + host + optional port)
        return (u.scheme, u.netloc) == (r.scheme, r.netloc)

    @staticmethod
    def _is_probably_html(resp: requests.Response) -> bool:
        ctype = (resp.headers.get("Content-Type") or "").lower()
        return (
            "text/html" in ctype
            or "application/xhtml+xml" in ctype
            or ctype.startswith("text/")
        )

    def _fetch_with_retries(self, url: str) -> Optional[requests.Response]:
        for attempt in range(1, self.retry.max_retries + 1):
            if self._stop_requested:
                return None

            try:
                resp = self.session.get(
                    url,
                    timeout=self.retry.timeout_s,
                    allow_redirects=True,
                )
                # Retryable server / throttling responses
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(
                        f"Retryable HTTP {resp.status_code}", response=resp
                    )
                return resp
            except KeyboardInterrupt:
                # Respect immediate interrupts
                raise
            except Exception as e:
                logger.warning(e)

                if attempt == self.retry.max_retries:
                    break

                sleep_s = self.retry.backoff_base_s * (2 ** (attempt - 1))
                sleep_s += random.uniform(0, self.retry.backoff_jitter_s)
                time.sleep(sleep_s)

        return None

    @staticmethod
    def _extract_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        # Drop non-content / noisy areas
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
                "canvas",
                "iframe",
                "header",
                "footer",
                "nav",
            ]
        ):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.body or soup

        text = main.get_text(separator="\n", strip=True)

        # Normalize: remove empty lines and compress whitespace
        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]
        text = "\n".join(lines)
        text = re.sub(r"[ \t]{2,}", " ", text)

        return text.strip()

    def _extract_links(self, html: str, base_url: str) -> Iterable[str]:
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            if self._stop_requested:
                break

            href = (a.get("href") or "").strip()
            if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                continue

            abs_url = urljoin(base_url, href)
            abs_url = self._normalize_url(abs_url)

            if not self._same_site(abs_url):
                continue

            # Skip obvious non-page assets
            path = urlparse(abs_url).path.lower()
            if path.endswith(
                (
                    ".pdf",
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp",
                    ".gif",
                    ".zip",
                    ".rar",
                    ".mp3",
                    ".mp4",
                    ".avi",
                    ".mov",
                )
            ):
                continue

            yield abs_url

    def collect(self, *, page_count: int, max_depth: int) -> Dict[str, str]:
        # install SIGINT handler for graceful Ctrl+C
        self._stop_requested = False
        self._old_sigint_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._on_sigint)

        queue: Deque[CrawlItem] = deque([CrawlItem(self.root_url, 0)])
        visited: Set[str] = set()
        enqueued: Set[str] = {self._url_key(self.root_url)}  # de-dupe the queue
        results: Dict[str, str] = {}

        try:
            while queue and len(results) < page_count and not self._stop_requested:
                logger.info(
                    "fetched {} / {} page(s) - {} queued...".format(
                        len(results),
                        page_count,
                        len(queue),
                    )
                )

                item = queue.popleft()
                item_key = self._url_key(item.url)
                enqueued.discard(item_key)  # no longer in queue

                if item_key in visited:
                    continue
                visited.add(item_key)

                resp = self._fetch_with_retries(item.url)
                if self._stop_requested:
                    break
                if resp is None:
                    continue

                if not self._is_probably_html(resp):
                    continue

                # Helps Persian text when server mislabels encoding
                resp.encoding = resp.apparent_encoding or resp.encoding
                html = resp.text or ""

                text = self._extract_text(html)
                if text:
                    logger.info(
                        "📜 += {}: {}".format(
                            item.url,
                            shorten_text(text.replace("\n", " ")),
                        )
                    )
                    results[item_key] = text

                if item.depth < max_depth and not self._stop_requested:
                    for link in self._extract_links(html, base_url=item.url):
                        if self._stop_requested:
                            break
                        link_key = self._url_key(link)
                        if link_key not in visited and link_key not in enqueued:
                            logger.info(f"🔗 += {link}")
                            queue.append(CrawlItem(link, item.depth + 1))
                            enqueued.add(link_key)

                if self.retry.delay_between_requests_s > 0 and not self._stop_requested:
                    time.sleep(self.retry.delay_between_requests_s)

            return results

        finally:
            # restore original SIGINT handler + close HTTP session
            with suppress(Exception):
                signal.signal(signal.SIGINT, self._old_sigint_handler)
            with suppress(Exception):
                self.session.close()
