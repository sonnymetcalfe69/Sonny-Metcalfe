"""A generic, hire-able agent role. Businesses can list extra_agents in
config (role + focus); each gets one of these, scoped tightly to its focus
so it doesn't just duplicate what the marketer/ops leads already do.

This is the "hire more agents" mechanism: add an entry to a business's
extra_agents in config/businesses.yaml (or via `python cli.py hire`) and
the next cycle it runs, gets its own station in the room, and its outputs
land in the outbox like any other agent's."""

from __future__ import annotations

from typing import Any

from src.agents.base import run_agent

SYSTEM_PROMPT_TEMPLATE = """\
You are the {role} for a small, real side business, hired specifically for
this focus: {focus}

Given today's priorities and research findings, produce 0-2 concrete,
useful outputs squarely within your focus area. Do not duplicate generic
marketing copy or generic operational proposals — another agent already
handles those. If nothing in your focus area is actionable this cycle,
return an empty list rather than stretching to justify your existence.

Respond with JSON of this shape:
{{
  "outputs": [
    {{
      "channel": "...",
      "action_type": "...",
      "title": "short label",
      "body": "the full output content"
    }}
  ]
}}
"""


def run(
    business: dict[str, Any],
    role: str,
    focus: str,
    priorities: list[str],
    findings: list[str],
    model: str,
) -> dict[str, Any]:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(role=role, focus=focus)
    context = {"business": business, "priorities": priorities, "research_findings": findings}
    return run_agent(system_prompt, context, model=model)
