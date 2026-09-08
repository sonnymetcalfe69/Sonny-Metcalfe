"""Runs one cycle (strategize -> research -> draft -> propose ops -> finance
check) for one or more businesses, submits outward-facing outputs to the
outbox for approval, and writes a daily Markdown report."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from src.agents import finance, marketer, ops, researcher, strategist
from src.tools import outbox
from src import state

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def run_cycle(business: dict[str, Any], model: str) -> dict[str, Any]:
    business_id = business["id"]
    history = state.recent_history(business_id)

    strategy = strategist.run(business, history, model)
    priorities = strategy.get("priorities", [])

    research = researcher.run(business, priorities, model)
    findings = research.get("findings", [])

    marketing = marketer.run(business, priorities, findings, model)
    operations = ops.run(business, priorities, findings, model)

    proposed_actions = operations.get("proposed_actions", [])
    finance_status = finance.run(business, proposed_actions)

    outbox_ids = []
    for draft in marketing.get("drafts", []):
        item_id = outbox.submit(business_id, draft.get("channel", "unknown"), draft.get("action_type", "other"), draft)
        outbox_ids.append(item_id)
    for action in proposed_actions:
        item_id = outbox.submit(business_id, action.get("channel", "unknown"), action.get("action_type", "other"), action)
        outbox_ids.append(item_id)

    cycle_result = {
        "strategy": strategy,
        "research": research,
        "marketing": marketing,
        "operations": operations,
        "finance": finance_status,
        "outbox_ids": outbox_ids,
    }
    state.record_cycle(business_id, cycle_result)
    return cycle_result


def render_report(business: dict[str, Any], result: dict[str, Any]) -> str:
    lines = [f"## {business.get('name', business['id'])}", ""]

    priorities = result["strategy"].get("priorities", [])
    lines.append("**Today's priorities:**")
    for p in priorities:
        lines.append(f"- {p}")
    lines.append("")

    watch_items = result["strategy"].get("watch_items", [])
    if watch_items:
        lines.append("**Watch items:**")
        for w in watch_items:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    findings = result["research"].get("findings", [])
    if findings:
        live = result["research"].get("live_data", False)
        label = "live search" if live else "model general knowledge, not live data"
        lines.append(f"**Research notes** ({label}):")
        for f in findings:
            lines.append(f"- {f}")
        lines.append("")

    n_drafts = len(result["marketing"].get("drafts", []))
    n_ops = len(result["operations"].get("proposed_actions", []))
    if n_drafts or n_ops:
        lines.append(
            f"**Pending your approval:** {n_drafts} content draft(s), "
            f"{n_ops} operational proposal(s) — run `python cli.py list-outbox`."
        )
        lines.append("")

    fin = result["finance"]
    lines.append(
        f"**Finance ({fin['month']}):** revenue ${fin['recorded_revenue']:.2f}, "
        f"expense ${fin['recorded_expense']:.2f}, net ${fin['recorded_net']:.2f}. "
        f"Status: **{fin['status']}**"
        + (f" (cap ${fin['monthly_budget_cap']:.2f})" if fin["monthly_budget_cap"] else "")
    )
    lines.append("")
    return "\n".join(lines)


def run_all(businesses: list[dict[str, Any]], model: str) -> str:
    sections = [f"# Daily digest — {date.today().isoformat()}", ""]
    for business in businesses:
        result = run_cycle(business, model)
        sections.append(render_report(business, result))

    report = "\n".join(sections)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{date.today().isoformat()}.md"
    report_path.write_text(report)
    return str(report_path)
