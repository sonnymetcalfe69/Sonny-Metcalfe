"""Manager: the one agent above every business's pipeline. Runs once per
`run_all` cycle (not per business) after every business has run, looks at
the whole portfolio at once, and decides what deserves your attention
first. It never re-decides a business's own priorities — that's the
strategist's job — it only triages across businesses.

Budget math is deterministic (computed by the orchestrator from the
ledgers, same as src/agents/finance.py), the manager only writes the
narrative around it.
"""

from __future__ import annotations

from typing import Any

from src.agents.base import run_agent

SYSTEM_PROMPT = """\
You are the overview manager for a small portfolio of side businesses run
by one person with limited time. You will be given a snapshot of every
business's latest cycle (priorities, finance status, pending approvals,
watch items) and the portfolio's total spend against a global budget cap
(already computed — do not recompute or contradict it).

Decide which single business most deserves the owner's attention today,
and say why in one sentence a busy person can act on immediately. Surface
anything portfolio-wide worth flagging (e.g. two businesses both stalled,
or spend concentrated in one place).

Respond with JSON of this shape:
{
  "headline": "one sentence on the portfolio's overall state today",
  "focus_business_id": "the business id most deserving attention, or null if everything looks fine",
  "focus_reason": "one concrete sentence on why that business, or empty string if focus_business_id is null",
  "notes": ["any other portfolio-wide observations worth flagging"]
}
"""


def run(
    rooms_summary: list[dict[str, Any]],
    global_budget: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    context = {"businesses": rooms_summary, "global_budget": global_budget}
    return run_agent(SYSTEM_PROMPT, context, model=model)
