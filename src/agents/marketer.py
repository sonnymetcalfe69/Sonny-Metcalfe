"""Marketer: drafts the actual outward-facing content for today's
priorities (posts, outreach emails, listing copy, video scripts). Drafts
only — the orchestrator submits each one to the outbox for approval,
nothing is sent."""

from __future__ import annotations

from typing import Any

from src.agents.base import run_agent

BASE_SYSTEM_PROMPT = """\
You are the marketing/copywriter for a small, real side business. Given
today's priorities and research findings, draft the actual content needed.
Write real, usable drafts (not placeholders like "[insert benefit here]").
Keep tone appropriate to the business description. If research findings are
labeled as not live data, avoid stating specific facts/prices you can't
verify.

If "active_idea" is provided, that is the specific thing the owner wants
turned into a finished draft this cycle — address it directly and
concretely rather than something generic.
"""

# Extra instructions per business_type, appended to the base prompt. Each
# tells the marketer the exact shape expected for that kind of business, so
# a raw idea (or a goal) turns into something genuinely ready to review,
# not a vague summary.
BUSINESS_TYPE_GUIDANCE = {
    "faceless_youtube": """\
This is a faceless YouTube Shorts/video channel — no on-camera talent, so
everything must work as narration/text-on-screen over B-roll or stock
footage. For each draft, put a fully structured script in "body" with
these labeled sections:
  HOOK: (first 2 seconds, must earn the next 5 seconds)
  BEATS: (3-5 short numbered beats, each one screen/shot worth of narration)
  CTA: (one line, e.g. "follow for more")
  TITLE OPTIONS: (3 alternatives)
  HASHTAGS: (5-8, no # needed, comma separated)
  THUMBNAIL TEXT: (<=5 words, all caps, for a text overlay)
Set channel to "youtube" and action_type to "video_script".
""",
    "digital_products": """\
This is a digital products storefront (printables, templates, or similar
downloads on a platform like Etsy or Gumroad). For each draft, put in
"body" a fully structured listing with these labeled sections:
  CONCEPT: (one line describing the product)
  LISTING TITLE: (SEO-friendly, keyword-forward)
  LISTING DESCRIPTION: (3-4 sentences, benefit-focused)
  TAGS: (10-13 short search tags, comma separated)
  SUGGESTED PRICE: (a specific dollar amount with one line of reasoning)
Set channel to the storefront named in the business's channels (or
"digital_storefront" if unclear) and action_type to "listing".
""",
}

JSON_SHAPE = """\

Respond with JSON of this shape:
{
  "drafts": [
    {
      "channel": "...",
      "action_type": "...",
      "title": "short label for this draft",
      "body": "the full draft content, following the structure above if one was given"
    }
  ]
}
Produce 0-3 drafts — only ones genuinely useful for today's priorities. If
an active_idea was given, produce exactly one draft that fully realizes it.
"""


def run(
    business: dict[str, Any],
    priorities: list[str],
    findings: list[str],
    model: str,
    active_idea: str | None = None,
) -> dict[str, Any]:
    business_type = business.get("business_type", "generic")
    system_prompt = BASE_SYSTEM_PROMPT + BUSINESS_TYPE_GUIDANCE.get(business_type, "") + JSON_SHAPE
    context = {
        "business": business,
        "priorities": priorities,
        "research_findings": findings,
        "active_idea": active_idea,
    }
    return run_agent(system_prompt, context, model=model)
