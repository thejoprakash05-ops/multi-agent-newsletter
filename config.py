import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

RSS_FEEDS = [
    {"name": "TechCrunch",   "url": "https://techcrunch.com/feed/"},
    {"name": "The Verge",    "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Hacker News",  "url": "https://news.ycombinator.com/rss"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "BBC News",     "url": "http://feeds.bbci.co.uk/news/rss.xml"},
    {"name": "Reuters",      "url": "https://feeds.reuters.com/reuters/topNews"},
]

WEBSITES = [
    {"name": "Hacker News",  "url": "https://news.ycombinator.com/"},
    {"name": "Product Hunt", "url": "https://www.producthunt.com/"},
]

REFRESH_TIMES   = ["09:00", "13:00", "18:00"]
TOP_N_HEADLINES = 10
DATA_FILE       = "data/headlines.json"
