import logging
from typing import Any
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsletterBot/1.0)"}


def fetch_rss(url: str, name: str, max_items: int = 20) -> list[dict[str, Any]]:
    articles = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_items]:
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            articles.append({
                "source":    name,
                "title":     title,
                "summary":   (entry.get("summary") or entry.get("description") or "").strip(),
                "link":      entry.get("link", ""),
                "published": entry.get("published", ""),
            })
    except Exception as e:
        logger.error("RSS fetch failed for %s (%s): %s", name, url, e)
    return articles


def scrape_website(url: str, name: str, max_items: int = 20) -> list[dict[str, Any]]:
    articles = []
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        seen: set[str] = set()
        for tag in soup.find_all(["h1", "h2", "h3"]):
            title = tag.get_text(strip=True)
            if len(title) < 25 or title in seen:
                continue
            seen.add(title)

            anchor = tag.find("a") or tag.find_parent("a")
            href = (anchor.get("href") or "") if anchor else ""
            if href and not href.startswith("http"):
                href = urljoin(url, href)

            articles.append({
                "source":    name,
                "title":     title,
                "summary":   "",
                "link":      href or url,
                "published": "",
            })
            if len(articles) >= max_items:
                break
    except Exception as e:
        logger.error("Scrape failed for %s (%s): %s", name, url, e)
    return articles
