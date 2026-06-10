"""
Unit tests for RankerAgent — Anthropic client is mocked throughout.

Key regressions guarded here:
  - REGRESSION: _SYSTEM_PROMPT.format() must not raise KeyError due to literal
    braces in the embedded JSON schema example (fixed by doubling {{ }}).
  - REGRESSION: ranker must use claude-sonnet-4-6 with max_tokens >= 8192 to
    avoid output truncation when ranking many articles across many categories.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import config


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_response(text, stop_reason="end_turn"):
    block = SimpleNamespace(type="text", text=text)
    return SimpleNamespace(content=[block], stop_reason=stop_reason)


def _sample_articles(n=5):
    return [
        {"source": f"Feed{i}", "title": f"Article {i}", "summary": "summary", "link": f"http://x.com/{i}"}
        for i in range(n)
    ]


def _mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = _make_response(response_text)
    return client


# ── Regression: prompt formatting ─────────────────────────────────────────────

def test_system_prompt_format_no_key_error():
    """_SYSTEM_PROMPT.format(max_per_category=N) must not raise KeyError.

    Regression: the JSON schema example in the prompt contained bare { } which
    Python's str.format() interpreted as placeholders. Fixed by doubling them.
    """
    from agents.ranker_agent import _SYSTEM_PROMPT
    try:
        result = _SYSTEM_PROMPT.format(max_per_category=12)
    except KeyError as e:
        pytest.fail(f"_SYSTEM_PROMPT.format() raised KeyError: {e}. "
                    "Ensure JSON braces in the prompt are escaped as {{{{ }}}}.")
    assert "12" in result


def test_system_prompt_contains_category_list():
    from agents.ranker_agent import _SYSTEM_PROMPT
    formatted = _SYSTEM_PROMPT.format(max_per_category=5)
    for cat in ("Tech", "Business", "Health", "Cricket"):
        assert cat in formatted


# ── Regression: model and token budget ────────────────────────────────────────

def test_ranker_uses_sonnet_model():
    """Ranker must use a model with >8192 output tokens to avoid truncation.

    Regression: original code used claude-haiku-4-5-20251001 (8192 token limit)
    which caused JSON to be cut off mid-output for large article sets.
    """
    headlines_json = json.dumps([
        {"rank": 1, "title": "T", "source": "S", "link": "http://x.com", "category": "Tech", "why": "w"}
    ])
    with patch("agents.ranker_agent.anthropic.Anthropic") as MockAnthropic:
        mock_client = _mock_client(headlines_json)
        MockAnthropic.return_value = mock_client

        from agents.ranker_agent import RankerAgent
        RankerAgent().run(_sample_articles())

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-6", (
        f"Expected claude-sonnet-4-6, got {call_kwargs['model']}. "
        "Haiku's 8192-token output limit causes JSON truncation."
    )
    assert call_kwargs["max_tokens"] >= 8192, (
        f"max_tokens={call_kwargs['max_tokens']} is too small to hold full ranked output."
    )


# ── Normal operation ──────────────────────────────────────────────────────────

def test_ranker_returns_headlines_list():
    headlines = [
        {"rank": 1, "title": "AI Breakthrough", "source": "TechCrunch",
         "link": "http://tc.com/1", "category": "Tech", "why": "Big deal."},
        {"rank": 2, "title": "Markets Rally", "source": "Reuters",
         "link": "http://r.com/2", "category": "Business", "why": "Stocks up."},
    ]
    with patch("agents.ranker_agent.anthropic.Anthropic") as MockAnthropic:
        MockAnthropic.return_value = _mock_client(json.dumps(headlines))
        from agents.ranker_agent import RankerAgent
        result = RankerAgent().run(_sample_articles())

    assert len(result) == 2
    assert result[0]["title"] == "AI Breakthrough"
    assert result[1]["category"] == "Business"


def test_ranker_strips_markdown_fences():
    headlines = [{"rank": 1, "title": "T", "source": "S", "link": "http://x.com",
                  "category": "Tech", "why": "w"}]
    fenced = f"```json\n{json.dumps(headlines)}\n```"

    with patch("agents.ranker_agent.anthropic.Anthropic") as MockAnthropic:
        MockAnthropic.return_value = _mock_client(fenced)
        from agents.ranker_agent import RankerAgent
        result = RankerAgent().run(_sample_articles())

    assert len(result) == 1
    assert result[0]["title"] == "T"


def test_ranker_returns_empty_on_invalid_json():
    with patch("agents.ranker_agent.anthropic.Anthropic") as MockAnthropic:
        MockAnthropic.return_value = _mock_client("this is not json {{{")
        from agents.ranker_agent import RankerAgent
        result = RankerAgent().run(_sample_articles())

    assert result == []


def test_ranker_returns_empty_when_no_articles():
    with patch("agents.ranker_agent.anthropic.Anthropic") as MockAnthropic:
        MockAnthropic.return_value = _mock_client("[]")
        from agents.ranker_agent import RankerAgent
        result = RankerAgent().run([])

    assert result == []
    MockAnthropic.return_value.messages.create.assert_not_called()


def test_ranker_caps_sample_at_500():
    """Ranker should not send more than 500 articles to avoid token overflow."""
    headlines_json = json.dumps([])
    with patch("agents.ranker_agent.anthropic.Anthropic") as MockAnthropic:
        mock_client = _mock_client(headlines_json)
        MockAnthropic.return_value = mock_client

        from agents.ranker_agent import RankerAgent
        RankerAgent().run(_sample_articles(600))

    call_kwargs = mock_client.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    article_count = int(user_content.split(" articles")[0].split()[-1])
    assert article_count <= 500
