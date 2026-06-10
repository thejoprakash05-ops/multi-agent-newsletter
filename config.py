import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

RSS_FEEDS = [
    # ── Tech ──────────────────────────────────────────────────────────────
    {"name": "TechCrunch",           "url": "https://techcrunch.com/feed/"},
    {"name": "The Verge",            "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Hacker News",          "url": "https://news.ycombinator.com/rss"},
    {"name": "Ars Technica",         "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Wired",                "url": "https://www.wired.com/feed/rss"},

    # ── Startups ───────────────────────────────────────────────────────────
    {"name": "TechCrunch Startups",  "url": "https://techcrunch.com/category/startups/feed/"},
    {"name": "VentureBeat",          "url": "https://venturebeat.com/feed/"},
    {"name": "Crunchbase News",      "url": "https://news.crunchbase.com/feed/"},

    # ── Business ───────────────────────────────────────────────────────────
    {"name": "Reuters Business",     "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "CNBC Top News",        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"name": "MarketWatch",          "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
    {"name": "BBC Business",         "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},

    # ── Investment ─────────────────────────────────────────────────────────
    {"name": "Yahoo Finance",        "url": "https://finance.yahoo.com/rss/topstories"},
    {"name": "Seeking Alpha",        "url": "https://seekingalpha.com/feed.xml"},
    {"name": "Motley Fool",          "url": "https://www.fool.com/feeds/index.aspx"},

    # ── Gold ───────────────────────────────────────────────────────────────
    {"name": "Kitco Gold News",      "url": "https://www.kitco.com/rss/KitcoNews.xml"},
    {"name": "BullionVault",         "url": "https://www.bullionvault.com/gold-news/rss.xml"},
    {"name": "Gold Price News",      "url": "https://goldprice.org/gold-news-rss.xml"},

    # ── Health ─────────────────────────────────────────────────────────────
    {"name": "Medical News Today",   "url": "https://www.medicalnewstoday.com/rss"},
    {"name": "WebMD Health News",    "url": "https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC"},
    {"name": "NHS News",             "url": "https://www.nhs.uk/news/feed.xml"},
    {"name": "BBC Health",           "url": "https://feeds.bbci.co.uk/news/health/rss.xml"},

    # ── Cricket ────────────────────────────────────────────────────────────
    {"name": "ESPNcricinfo",         "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml"},
    {"name": "BBC Sport Cricket",    "url": "https://feeds.bbci.co.uk/sport/cricket/rss.xml"},
    {"name": "Cricbuzz",             "url": "https://www.cricbuzz.com/rss-feeds/cricket-news"},

    # ── Tennis ─────────────────────────────────────────────────────────────
    {"name": "BBC Sport Tennis",     "url": "https://feeds.bbci.co.uk/sport/tennis/rss.xml"},
    {"name": "Tennis World USA",     "url": "https://www.tennisworldusa.org/rss/news.rss"},
    {"name": "Tennis Now",           "url": "https://www.tennisnow.com/rss.aspx"},

    # ── EDA ────────────────────────────────────────────────────────────────
    {"name": "EE Times",             "url": "https://www.eetimes.com/feed/"},
    {"name": "EDN Network",          "url": "https://www.edn.com/feed/"},
    {"name": "Electronic Design",    "url": "https://www.electronicdesign.com/rss"},

    # ── Semiconductor ──────────────────────────────────────────────────────
    {"name": "Semiconductor Eng.",   "url": "https://semiengineering.com/feed/"},
    {"name": "IEEE Spectrum",        "url": "https://spectrum.ieee.org/rss"},
    {"name": "Tom's Hardware",       "url": "https://www.tomshardware.com/feeds/all"},
    {"name": "AnySilicon",           "url": "https://anysilicon.com/feed/"},

    # ── General ────────────────────────────────────────────────────────────
    {"name": "BBC News",             "url": "http://feeds.bbci.co.uk/news/rss.xml"},
    {"name": "Reuters Top News",     "url": "https://feeds.reuters.com/reuters/topNews"},
]

WEBSITES = [
    {"name": "Hacker News",  "url": "https://news.ycombinator.com/"},
    {"name": "Product Hunt", "url": "https://www.producthunt.com/"},
]

REFRESH_TIMES    = ["09:00", "13:00", "18:00"]
MAX_PER_CATEGORY = 12   # stories shown per tab; ranker targets this many per category
DATA_FILE        = "data/headlines.json"
