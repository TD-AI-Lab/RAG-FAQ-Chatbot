from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.errors import IngestionError
from src.ingestion.parse_faq import parse_faq_from_html
from src.utils.hashing import sha256_text
from src.utils.io import write_json

logger = logging.getLogger(__name__)


@retry(wait=wait_exponential(multiplier=0.5, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
def _fetch_html(client: httpx.Client, url: str) -> str:
    resp = client.get(url)
    resp.raise_for_status()
    return resp.text


def _candidate_links(html: str, current_url: str) -> list[str]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    current_host = urlparse(current_url).netloc

    for a in soup.select("a[href]"):
        href = a.get("href", "")
        absolute = urljoin(current_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc != current_host:
            continue
        lowered = absolute.lower()
        if any(token in lowered for token in ["faq", "support", "help", "knowledge", "page/"]):
            links.append(absolute.split("#")[0])

    next_rel = soup.select_one('a[rel="next"]')
    if next_rel and next_rel.get("href"):
        links.append(urljoin(current_url, next_rel.get("href")))

    return list(dict.fromkeys(links))


def run_ingestion() -> list[dict]:
    settings = get_settings()
    base_url = settings.faq_source_url
    timeout = settings.request_timeout_seconds

    raw_dir = settings.backend_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    visited: set[str] = set()
    queue: deque[str] = deque([base_url])
    html_by_url: dict[str, str] = {}
    max_pages = max(5, settings.ingest_max_pages)

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        while queue and len(visited) < max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)
            try:
                html = _fetch_html(client, url)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to fetch %s: %s", url, exc)
                continue

            html_by_url[url] = html
            filename = raw_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{sha256_text(url)[:12]}.html"
            filename.write_text(html, encoding="utf-8")

            for link in _candidate_links(html, url):
                if link not in visited:
                    queue.append(link)

    if not html_by_url:
        raise IngestionError("No HTML retrieved from source. Site may be JS-only or blocked.")

    all_items = []
    for url, html in html_by_url.items():
        all_items.extend(parse_faq_from_html(html, url))

    dedup: dict[str, dict] = {}
    for item in all_items:
        key = sha256_text(f"{item.question}|{item.answer}")
        dedup[key] = item.model_dump(mode="json")

    items = list(dedup.values())
    if len(items) < 5:
        logger.warning("Low FAQ count detected: %s", len(items))
    if len(items) == 0:
        raise IngestionError("0 FAQ items parsed. Existing processed file preserved.")

    output_file: Path = settings.processed_faq_file
    write_json(output_file, items)
    logger.info("Ingestion complete. %s FAQ items saved to %s", len(items), output_file)
    return items


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion()
