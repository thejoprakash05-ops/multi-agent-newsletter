"""
Sanity checks on config.py — catch typos and structural breaks before they
reach runtime.
"""
import config


def test_rss_feeds_have_name_and_url():
    for feed in config.RSS_FEEDS:
        assert "name" in feed, f"Missing 'name': {feed}"
        assert "url"  in feed, f"Missing 'url': {feed}"
        assert feed["name"], "Feed name must not be empty"
        assert feed["url"].startswith("http"), f"Bad URL in feed '{feed['name']}': {feed['url']}"


def test_websites_have_name_and_url():
    for site in config.WEBSITES:
        assert "name" in site
        assert "url"  in site
        assert site["url"].startswith("http")


def test_refresh_times_format():
    for t in config.REFRESH_TIMES:
        h, m = t.split(":")
        assert 0 <= int(h) <= 23, f"Bad hour in REFRESH_TIMES: {t}"
        assert 0 <= int(m) <= 59, f"Bad minute in REFRESH_TIMES: {t}"


def test_max_per_category_positive_int():
    assert isinstance(config.MAX_PER_CATEGORY, int)
    assert config.MAX_PER_CATEGORY > 0


def test_data_file_is_string():
    assert isinstance(config.DATA_FILE, str)
    assert config.DATA_FILE.endswith(".json")


def test_no_duplicate_feed_urls():
    urls = [f["url"] for f in config.RSS_FEEDS]
    assert len(urls) == len(set(urls)), "Duplicate RSS feed URL detected"
