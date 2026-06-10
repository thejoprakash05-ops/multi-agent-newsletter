"""
Agent 2 — Ranker Agent
----------------------
Receives the raw articles list from the Scraper Agent (via the
orchestrator) and uses Claude to select and rank the top stories
per category (up to MAX_PER_CATEGORY each).

This agent makes a single Claude call — no tool loop needed, because
ranking is a pure reasoning task, not a multi-step action task.

Flow:
  1. Orchestrator calls RankerAgent.run(articles)
  2. Articles are formatted into a text block and sent to Claude
  3. Claude returns a ranked JSON array (up to MAX_PER_CATEGORY per category)
  4. The parsed list is returned to the orchestrator
"""

import json
import logging
from typing import Any

import anthropic

from config import ANTHROPIC_API_KEY, MAX_PER_CATEGORY

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert news curator. Analyse a list of article headlines and summaries, then select the most important stories.

Selection criteria:
- Breaking news and significant recent developments
- High-impact stories with broad relevance
- No duplicates: if multiple sources cover the same story, pick the best-worded version

Categories — assign exactly one label (case-sensitive) per story:
  Tech, Business, Investment, Gold, Health, Startups, Cricket, Tennis, EDA, Semiconductor, Other

Output rule: return up to {max_per_category} stories per category.
Rank stories 1-N globally by importance across all categories combined.

Return ONLY a valid JSON array — no markdown fences, no explanation — using this exact schema:
[
  {{
    "rank": 1,
    "title": "Concise, readable headline",
    "source": "Source name",
    "link": "URL",
    "category": "Tech",
    "why": "One sentence explaining why this story matters"
  }}
]"""


class RankerAgent:
    def __init__(self) -> None:
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def run(
        self,
        articles: list[dict[str, Any]],
        max_per_category: int = MAX_PER_CATEGORY,
    ) -> list[dict[str, Any]]:
        if not articles:
            logger.warning("RankerAgent: received 0 articles — nothing to rank")
            return []

        sample = articles[:500]

        articles_block = "\n\n".join(
            "SOURCE: {source}\nTITLE: {title}\nSUMMARY: {summary}\nURL: {link}".format(
                source=a["source"],
                title=a["title"],
                summary=(a.get("summary") or "")[:300],
                link=a.get("link", ""),
            )
            for a in sample
        )

        user_message = (
            f"Here are {len(sample)} articles gathered from newsletters and news sources.\n"
            f"Select up to {max_per_category} stories per category and rank them globally.\n\n"
            f"ARTICLES:\n{articles_block}\n\n"
            "Return ONLY the JSON array."
        )

        logger.info("RankerAgent: sending %d articles to Claude", len(sample))

        # ── Single Claude call (no tool loop) ────────────────────────────
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16384,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT.format(max_per_category=max_per_category),
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )

        raw = response.content[0].text.strip()

        if raw.startswith("```"):
            lines = raw.splitlines()
            start = 1 if lines[0].startswith("```") else 0
            end   = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            raw   = "\n".join(lines[start:end]).strip()

        try:
            headlines = json.loads(raw)
            logger.info("RankerAgent: returned %d headlines", len(headlines))
            return headlines
        except json.JSONDecodeError as e:
            logger.error("RankerAgent: Claude returned invalid JSON — %s", e)
            return []
