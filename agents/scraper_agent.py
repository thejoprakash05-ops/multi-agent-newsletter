"""
Agent 1 — Scraper Agent
-----------------------
Uses Claude with tool_use to decide which sources to call and then
executes fetch_rss / scrape_website as tools in an agentic loop.

Flow:
  1. Orchestrator calls ScraperAgent.run()
  2. Claude receives a list of all sources and starts calling tools
  3. For every tool_use block returned, we execute the real scraper
     function and send the result back as tool_result
  4. Loop continues until Claude stops calling tools (stop_reason="end_turn")
  5. All collected articles are returned to the orchestrator
"""

import json
import logging
from typing import Any

import anthropic

from config import ANTHROPIC_API_KEY, RSS_FEEDS, WEBSITES
from scrapers import fetch_rss, scrape_website

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a web scraping agent. Your only job is to collect articles from news sources.

You have two tools:
  - fetch_rss_feed   : fetches articles from an RSS feed
  - scrape_website   : scrapes headlines from a website's h1/h2/h3 tags

Rules:
  1. Call every source in the list exactly once.
  2. You may call multiple tools per turn (batch them if you like).
  3. When every source has been fetched, reply with the plain text: "All sources fetched."
"""

_TOOLS = [
    {
        "name": "fetch_rss_feed",
        "description": "Fetch articles from an RSS feed URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url":  {"type": "string", "description": "RSS feed URL"},
                "name": {"type": "string", "description": "Human-readable source name"},
            },
            "required": ["url", "name"],
        },
    },
    {
        "name": "scrape_website",
        "description": "Scrape headline links from a website's h1/h2/h3 tags.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url":  {"type": "string", "description": "Website URL"},
                "name": {"type": "string", "description": "Human-readable source name"},
            },
            "required": ["url", "name"],
        },
    },
]


class ScraperAgent:
    def __init__(self) -> None:
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def run(self) -> list[dict[str, Any]]:
        sources_json = json.dumps({"rss_feeds": RSS_FEEDS, "websites": WEBSITES}, indent=2)
        user_msg = (
            "Fetch articles from every source listed below.\n\n"
            f"SOURCES:\n{sources_json}"
        )

        messages: list[dict] = [{"role": "user", "content": user_msg}]
        all_articles: list[dict[str, Any]] = []

        logger.info("ScraperAgent: starting agentic loop")

        # ── Agentic loop ────────────────────────────────────────────────
        while True:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                tools=_TOOLS,
                messages=messages,
            )

            # Gather every tool_use block in this response
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    articles = self._execute_tool(block.name, block.input)
                    all_articles.extend(articles)
                    logger.info(
                        "  [tool] %s('%s') → %d articles",
                        block.name, block.input.get("name", "?"), len(articles),
                    )
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     json.dumps({"articles_fetched": len(articles)}),
                    })

            # If Claude called tools, send results back and loop again
            if tool_results:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user",      "content": tool_results})

            # Claude finished (no more tool calls)
            if response.stop_reason == "end_turn":
                break

        logger.info("ScraperAgent: done. Total articles collected: %d", len(all_articles))
        return all_articles

    # ── Tool dispatcher ─────────────────────────────────────────────────
    def _execute_tool(self, name: str, inputs: dict) -> list[dict[str, Any]]:
        if name == "fetch_rss_feed":
            return fetch_rss(inputs["url"], inputs["name"])
        if name == "scrape_website":
            return scrape_website(inputs["url"], inputs["name"])
        logger.warning("ScraperAgent: unknown tool '%s'", name)
        return []
