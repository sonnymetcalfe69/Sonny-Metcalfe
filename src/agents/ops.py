"""Ops: proposes concrete operational actions (price change, restock,
reply to a customer, a proposed purchase). Proposals only — anything with
a cost or outside-world effect goes through the outbox like marketer drafts."""

from __future__ import annotations

from typing import Any

from src.agents.base import run_agent

SYSTEM_PROMPT = """\
You are the operations lead for a small, real side business. Given
today's priorities and research findings, propose concrete operational
actions — not content/copy (that's the marketer's job), but things like:
a price change, a restock decision, a reply to a customer inquiry, a
proposed purchase or tool subscription. Only propose actions that plausibly
fit within the business's stated monthly budget cap; flag anything that
would exceed it rather than assuming it's fine.

Respond with JSON of this shape:
{
  "proposed_actions": [
    {
      "channel": "e.g. etsy, upwork, shopify, general",
      "action_type": "price_change | restock | customer_reply | purchase | other",
      "description": "specific, concrete description of the action",
      "estimated_cost": 0,
      "requires_budget": true or false
    }
  ]
}
Produce 0-3 proposals — only ones genuinely useful for today's priorities.
"""


def run(
    business: dict[str, Any],
    priorities: list[str],
    findings: list[str],
    model: str,
) -> dict[str, Any]:
    context = {"business": business, "priorities": priorities, "research_findings": findings}
    return run_agent(SYSTEM_PROMPT, context, model=model)
