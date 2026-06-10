"""
Unit tests for scrapers.py — all network calls are mocked.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from scrapers import fetch_rss, scrape_website


# ── fetch_rss ─────────────────────────────────────────────────────────────────

def _make_entry(**kwargs):
    defaults = {"title": "Test Article", "summary": "A summary.", "link": "http://example.com/1", "published": ""}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults, get=lambda k, default="": defaults.get(k, default))


def _feedparser_result(entries):
    ns = SimpleNamespace(entries=entries)
    return ns


def test_fetch_rss_returns_articles():
    entry = MagicMock()
    entry.get = lambda k, default="": {"title": "Big News", "summary": "Details here.", "link": "http://x.com", "published": "Mon"}.get(k, default)

    with patch("scrapers.feedparser.parse") as mock_parse:
        mock_parse.return_value = SimpleNamespace(entries=[entry])
        result = fetch_rss("http://feed.example.com", "TestFeed")

    assert len(result) == 1
    assert result[0]["title"] == "Big News"
    assert result[0]["source"] == "TestFeed"
    assert result[0]["link"] == "http://x.com"


def test_fetch_rss_skips_entries_with_empty_title():
    empty_title = MagicMock()
    empty_title.get = lambda k, default="": {"title": "", "summary": "ok", "link": "http://x.com", "published": ""}.get(k, default)

    with patch("scrapers.feedparser.parse") as mock_parse:
        mock_parse.return_value = SimpleNamespace(entries=[empty_title])
        result = fetch_rss("http://feed.example.com", "TestFeed")

    assert result == []


def test_fetch_rss_respects_max_items():
    entries = []
    for i in range(30):
        e = MagicMock()
        e.get = lambda k, default="", i=i: {"title": f"Article {i}", "summary": "", "link": f"http://x.com/{i}", "published": ""}.get(k, default)
        entries.append(e)

    with patch("scrapers.feedparser.parse") as mock_parse:
        mock_parse.return_value = SimpleNamespace(entries=entries)
        result = fetch_rss("http://feed.example.com", "TestFeed", max_items=5)

    assert len(result) == 5


def test_fetch_rss_returns_empty_on_exception():
    with patch("scrapers.feedparser.parse", side_effect=Exception("network error")):
        result = fetch_rss("http://bad.example.com", "BadFeed")
    assert result == []


# ── scrape_website ────────────────────────────────────────────────────────────

_SAMPLE_HTML = """
<html><body>
  <h1><a href="/story/1">Short</a></h1>
  <h2><a href="/story/2">This is a long enough headline that should pass the filter</a></h2>
  <h3>No link but this headline is long enough to pass the length check here</h3>
  <h2><a href="http://external.com/article">External absolute link passes through unchanged</a></h2>
</body></html>
"""


def _mock_response(html=_SAMPLE_HTML, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.text = html
    resp.raise_for_status = MagicMock()
    return resp


def test_scrape_website_returns_articles():
    with patch("scrapers.requests.get", return_value=_mock_response()):
        result = scrape_website("http://example.com", "Example")
    assert len(result) >= 1
    for a in result:
        assert a["source"] == "Example"
        assert len(a["title"]) >= 25


def test_scrape_website_filters_short_headings():
    with patch("scrapers.requests.get", return_value=_mock_response()):
        result = scrape_website("http://example.com", "Example")
    titles = [a["title"] for a in result]
    assert "Short" not in titles


def test_scrape_website_joins_relative_urls():
    with patch("scrapers.requests.get", return_value=_mock_response()):
        result = scrape_website("http://example.com", "Example")
    for a in result:
        assert a["link"].startswith("http"), f"Relative URL not joined: {a['link']}"


def test_scrape_website_returns_empty_on_http_error():
    resp = MagicMock()
    resp.raise_for_status.side_effect = Exception("404")
    with patch("scrapers.requests.get", return_value=resp):
        result = scrape_website("http://example.com", "Example")
    assert result == []


def test_scrape_website_returns_empty_on_connection_error():
    with patch("scrapers.requests.get", side_effect=Exception("connection refused")):
        result = scrape_website("http://example.com", "Example")
    assert result == []


def test_scrape_website_respects_max_items():
    many_h2 = "".join(
        f'<h2><a href="/s/{i}">This is headline number {i} which is long enough</a></h2>'
        for i in range(30)
    )
    html = f"<html><body>{many_h2}</body></html>"
    with patch("scrapers.requests.get", return_value=_mock_response(html)):
        result = scrape_website("http://example.com", "Example", max_items=5)
    assert len(result) == 5
