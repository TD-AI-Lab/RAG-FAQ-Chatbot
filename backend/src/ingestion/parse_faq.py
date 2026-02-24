from __future__ import annotations

import json
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from src.domain.models import FAQItem
from src.ingestion.cleaners import sanitize_soup
from src.utils.hashing import sha256_text
from src.utils.text import collapse_whitespace


def _build_item(question: str, answer: str, url: str, section: str | None = None) -> FAQItem | None:
    q = collapse_whitespace(question)
    a = collapse_whitespace(answer)
    if not q or not a:
        return None
    if len(q) < 8 or len(q) > 240:
        return None
    if len(a) < 15:
        return None
    if q.lower() == a.lower():
        return None
    item_id = sha256_text(f"{q}|{a}|{url}")
    return FAQItem(
        id=item_id,
        question=q,
        answer=a,
        url=url,
        section=section,
        tags=[],
        last_seen_at=datetime.now(timezone.utc),
    )


def _extract_betterdocs_single(soup: BeautifulSoup, page_url: str) -> list[FAQItem]:
    items: list[FAQItem] = []
    if "/docs/" not in page_url.lower():
        return items
    title_node = (
        soup.select_one(".wp-block-post-title")
        or soup.select_one(".betterdocs-entry-title")
        or soup.select_one("h1")
        or soup.select_one("h2")
    )
    content_root = (
        soup.select_one(".betterdocs-entry-content .betterdocs-content")
        or soup.select_one(".betterdocs-entry-content")
        or soup.select_one("article")
    )
    if not title_node or not content_root:
        return items

    title = title_node.get_text(" ", strip=True)
    if not title:
        return items

    parts: list[str] = []
    for node in content_root.select("p, li, h3, h4"):
        text = collapse_whitespace(node.get_text(" ", strip=True))
        if not text:
            continue
        parts.append(text)

    answer = collapse_whitespace(" ".join(parts))
    maybe = _build_item(title, answer, page_url)
    if maybe:
        items.append(maybe)
    return items


def _extract_betterdocs_lists(soup: BeautifulSoup, page_url: str) -> list[FAQItem]:
    items: list[FAQItem] = []
    for article in soup.select("article"):
        section = None
        header = article.select_one(".betterdocs-entry-title, .betterdocs-category-title")
        if header:
            section = collapse_whitespace(header.get_text(" ", strip=True)) or None

        for link in article.select(".betterdocs-articles-list a[href]"):
            q = collapse_whitespace(link.get_text(" ", strip=True))
            if len(q) < 8:
                continue
            # Archive pages rarely have full answers; keep a neutral snippet.
            desc = article.select_one(".betterdocs-category-description")
            snippet = collapse_whitespace(desc.get_text(" ", strip=True)) if desc else ""
            answer = snippet or f"Consultez la documentation Workways: {q}"
            maybe = _build_item(q, answer, page_url, section=section)
            if maybe:
                items.append(maybe)
    return items


def _extract_json_ld_faq(soup: BeautifulSoup, base_url: str) -> list[FAQItem]:
    items: list[FAQItem] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.get_text(strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        blocks = data if isinstance(data, list) else [data]
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("@type") not in {"FAQPage", "WebPage"}:
                continue
            entities = block.get("mainEntity", [])
            for entity in entities:
                if not isinstance(entity, dict) or entity.get("@type") != "Question":
                    continue
                question = str(entity.get("name", ""))
                accepted = entity.get("acceptedAnswer", {})
                answer = ""
                if isinstance(accepted, dict):
                    answer = str(accepted.get("text", ""))
                maybe = _build_item(question, BeautifulSoup(answer, "html.parser").get_text(" "), base_url)
                if maybe:
                    items.append(maybe)
    return items


def _extract_dl_faq(soup: BeautifulSoup, page_url: str) -> list[FAQItem]:
    items: list[FAQItem] = []
    for dl in soup.find_all("dl"):
        dts = dl.find_all("dt")
        for dt in dts:
            dd = dt.find_next_sibling("dd")
            if not dd:
                continue
            maybe = _build_item(dt.get_text(" "), dd.get_text(" "), page_url)
            if maybe:
                items.append(maybe)
    return items


def _extract_heading_pairs(soup: BeautifulSoup, page_url: str) -> list[FAQItem]:
    items: list[FAQItem] = []
    faq_keywords = ("faq", "question", "accordion", "support", "help")
    containers = soup.find_all(
        lambda tag: tag.name in {"section", "div", "article"}
        and any(k in " ".join(tag.get("class", [])).lower() for k in faq_keywords)
    )
    if not containers:
        return []

    for container in containers:
        for heading in container.find_all(["h2", "h3", "h4", "button", "summary"]):
            question = heading.get_text(" ", strip=True)
            question_lower = question.lower()
            likely_question = question.endswith("?") or question_lower.startswith(("comment", "where", "how", "what", "pourquoi", "peut-on"))
            if len(question) < 8 or not likely_question:
                continue
            answer_parts: list[str] = []
            sibling = heading.find_next_sibling()
            guard = 0
            while sibling and guard < 5:
                guard += 1
                if sibling.name in {"h2", "h3", "h4", "button", "summary"}:
                    break
                text = sibling.get_text(" ", strip=True)
                if text:
                    answer_parts.append(text)
                sibling = sibling.find_next_sibling()
            if not answer_parts:
                continue
            answer = " ".join(answer_parts)
            if len(answer) < 20:
                continue
            maybe = _build_item(question, answer, page_url)
            if maybe:
                items.append(maybe)
    return items


def parse_faq_from_html(html: str, base_url: str) -> list[FAQItem]:
    soup = sanitize_soup(html)
    found: list[FAQItem] = []

    found.extend(_extract_betterdocs_single(soup, base_url))
    found.extend(_extract_json_ld_faq(soup, base_url))
    found.extend(_extract_dl_faq(soup, base_url))
    found.extend(_extract_heading_pairs(soup, base_url))

    unique: dict[str, FAQItem] = {}
    for item in found:
        key = sha256_text(f"{item.question}|{item.answer}")
        unique[key] = item

    return list(unique.values())
