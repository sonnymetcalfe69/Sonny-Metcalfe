"""Researcher: gathers notes relevant to today's priorities.

Uses a real search tool when one is wired up in src/tools/web_research.py;
otherwise falls back to the model's own knowledge and clearly labels the
output as such rather than pretending it's live data.
"""

from __future__ import annotations

from typing import Any

from src.agents.base import run_agent
from src.tools import web_research

SYSTEM_PROMPT = """\
You are the researcher for a small, real side business. You will be given
today's priorities and, if available, live search results. If no live
search results are provided, answer from your general knowledge but you
MUST set "live_data" to false and keep claims conservative/general rather
than inventing specific current facts (prices, competitor names, exact
figures) you cannot know without a live search.

Respond with JSON of this shape:
{
  "live_data": true or false,
  "findings": ["short, specific, actionable notes"],
  "caveats": ["anything the strategist/marketer should be careful about given data freshness"]
}
"""


def run(
    business: dict[str, Any],
    priorities: list[str],
    model: str,
) -> dict[str, Any]:
    search_results = None
    if priorities:
        search_results = web_research.search(f"{business.get('name', '')}: {priorities[0]}")

    context = {
        "business": business,
        "priorities": priorities,
        "search_results": search_results,
    }
    return run_agent(SYSTEM_PROMPT, context, model=model)
