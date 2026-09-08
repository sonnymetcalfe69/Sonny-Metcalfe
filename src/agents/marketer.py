"""Marketer: drafts the actual outward-facing content for today's
priorities (posts, outreach emails, listing copy). Drafts only — the
orchestrator submits each one to the outbox for approval, nothing is sent."""

from __future__ import annotations

from typing import Any

from src.agents.base import run_agent

SYSTEM_PROMPT = """\
You are the marketing/copywriter for a small, real side business. Given
today's priorities and research findings, draft the actual content needed
— e.g. a social post, an outreach email, updated listing copy. Write real,
usable drafts (not placeholders like "[insert benefit here]"). Keep tone
appropriate to the business description. If research findings are labeled
as not live data, avoid stating specific facts/prices you can't verify.

Respond with JSON of this shape:
{
  "drafts": [
    {
      "channel": "e.g. instagram, email, etsy, blog",
      "action_type": "post | email | listing_update | other",
      "title": "short label for this draft",
      "body": "the full draft content"
    }
  ]
}
Produce 0-3 drafts — only ones genuinely useful for today's priorities.
"""


def run(
    business: dict[str, Any],
    priorities: list[str],
    findings: list[str],
    model: str,
) -> dict[str, Any]:
    context = {"business": business, "priorities": priorities, "research_findings": findings}
    return run_agent(SYSTEM_PROMPT, context, model=model)
