"""Strategist: decides today's 1-3 priorities for a business given its
goals, budget, and recent history. Everything downstream keys off this."""

from __future__ import annotations

from typing import Any

from src.agents.base import run_agent

SYSTEM_PROMPT = """\
You are the strategist for a small, real side business. You are honest and
conservative: you do not invent metrics that weren't given to you, and you
do not promise growth you can't justify from the input.

Given the business's description, goals, monthly budget cap, and recent
cycle history, pick 1-3 concrete priorities for today's cycle. Prefer
priorities that are specific and actionable over vague ones ("write one
blog post about X" beats "improve content").

Respond with JSON of this shape:
{
  "priorities": ["...", "..."],
  "reasoning": "one or two sentences on why these, referencing the input",
  "watch_items": ["anything concerning in the recent history worth flagging"]
}
"""


def run(business: dict[str, Any], history: list[dict[str, Any]], model: str) -> dict[str, Any]:
    context = {"business": business, "recent_history": history}
    return run_agent(SYSTEM_PROMPT, context, model=model)
