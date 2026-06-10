"""
Agent 3 — Orchestrator Agent
-----------------------------
A Claude agent that runs the full pipeline using tools.

Claude (not Python) decides to:
  1. Call run_scraper  → spins up ScraperAgent, collects raw articles
  2. Call run_ranker   → spins up RankerAgent, ranks the collected articles

All sequencing is driven by Claude's reasoning, not by Python control flow.
app.py just calls OrchestratorAgent().run() — one line.
"""

import json
import logging
from typing import Any

import anthropic

from config import ANTHROPIC_API_KEY
from agents.scraper_agent import ScraperAgent
from agents.ranker_agent import RankerAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a newsletter pipeline orchestrator agent.

Your job is to produce today's top headlines by running two sub-agents in order:

  Step 1 — call run_scraper : collects raw articles from all news sources.
  Step 2 — call run_ranker  : ranks the collected articles into top headlines.

Always run both steps in this exact order. After run_ranker completes, say "Pipeline complete."
"""

_TOOLS = [
    {
        "name": "run_scraper",
        "description": (
            "Run the Scraper Agent. It fetches articles from all configured RSS feeds "
            "and websites. Returns how many articles were collected. "
            "Must be called before run_ranker."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "run_ranker",
        "description": (
            "Run the Ranker Agent. It reads the articles collected by run_scraper and "
            "selects the top ranked headlines. Must be called after run_scraper."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


class OrchestratorAgent:
    def __init__(self) -> None:
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        # Shared state passed between sub-agents
        self._articles:  list[dict[str, Any]] = []
        self._headlines: list[dict[str, Any]] = []

    def run(self) -> list[dict[str, Any]]:
        messages: list[dict] = [
            {"role": "user", "content": "Run the full newsletter pipeline."}
        ]

        logger.info("OrchestratorAgent: starting")

        # ── Agentic loop ─────────────────────────────────────────────────
        while True:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                system=_SYSTEM_PROMPT,
                tools=_TOOLS,
                messages=messages,
            )

            logger.info("  [orchestrator] %s", response.content)

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = self._execute_tool(block.name)
                    logger.info("  [orchestrator] %s → %s", block.name, result)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     json.dumps(result),
                    })

            if tool_results:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user",      "content": tool_results})

            if response.stop_reason == "end_turn":
                break

        logger.info("OrchestratorAgent: done — %d headlines", len(self._headlines))
        return self._headlines

    # ── Tool dispatcher ──────────────────────────────────────────────────
    def _execute_tool(self, name: str) -> dict:
        if name == "run_scraper":
            self._articles = ScraperAgent().run()
            return {"status": "ok", "articles_collected": len(self._articles)}

        if name == "run_ranker":
            self._headlines = RankerAgent().run(self._articles)
            return {"status": "ok", "headlines_ranked": len(self._headlines)}

        logger.warning("OrchestratorAgent: unknown tool '%s'", name)
        return {"status": "error", "message": f"Unknown tool: {name}"}
