"""
Agent 2 — Ranker Agent
----------------------
Receives the raw articles list from the Scraper Agent (via the
orchestrator) and uses Claude to select and rank the top N headlines.

This agent makes a single Claude call — no tool loop needed, because
ranking is a pure reasoning task, not a multi-step action task.

Flow:
  1. Orchestrator calls RankerAgent.run(articles)
  2. Articles are formatted into a text block and sent to Claude
  3. Claude returns a ranked JSON array
  4. The parsed list is returned to the orchestrator
"""

import json
import logging
from typing import Any

import anthropic

from config import ANTHROPIC_API_KEY, TOP_N_HEADLINES

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert news curator. Analyse a list of article headlines and summaries, then select and rank the most important and interesting stories.

Selection criteria:
- Breaking news and significant recent developments
- High-impact stories with broad relevance
- Diverse topics across Tech, Business, World, Science, Health, Politics
- If multiple sources cover the same story, pick the best-worded version (no duplicates)

Return ONLY a valid JSON array — no markdown fences, no explanation — using this exact schema:
[
  {
    "rank": 1,
    "title": "Concise, readable headline",
    "source": "Source name",
    "link": "URL",
    "category": "Tech|Business|World|Science|Health|Politics|Other",
    "why": "One sentence explaining why this story matters"
  }
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
        top_n: int = TOP_N_HEADLINES,
    ) -> list[dict[str, Any]]:
        if not articles:
            logger.warning("RankerAgent: received 0 articles — nothing to rank")
            return []

        # Cap at 100 to stay within token budget
        sample = articles[:100]

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
            f"Select and rank the top {top_n} most important stories.\n\n"
            f"ARTICLES:\n{articles_block}\n\n"
            "Return ONLY the JSON array."
        )

        logger.info("RankerAgent: sending %d articles to Claude for ranking", len(sample))

        # ── Single Claude call (no tool loop) ───────────────────────────
        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # prompt caching
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )

        raw = response.content[0].text.strip()

        # Strip markdown fences if Claude wrapped the JSON
        if raw.startswith("```"):
            lines = raw.splitlines()
            start = 1 if lines[0].startswith("```") else 0
            end   = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            raw   = "\n".join(lines[start:end]).strip()

        try:
            headlines = json.loads(raw)
            logger.info("RankerAgent: selected %d headlines", len(headlines))
            return headlines[:top_n]
        except json.JSONDecodeError as e:
            logger.error("RankerAgent: Claude returned invalid JSON — %s", e)
            return []
