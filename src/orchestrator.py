"""Runs one cycle (strategize -> research -> draft -> propose ops -> hired
specialists -> finance check) for one or more businesses, submits
outward-facing outputs to the outbox for approval, runs the portfolio-level
manager once across all of them, and writes a daily Markdown report."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from src.agents import finance, manager, marketer, ops, researcher, specialist, strategist
from src.tools import ideas, ledger, outbox
from src import state

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def run_cycle(business: dict[str, Any], model: str) -> dict[str, Any]:
    business_id = business["id"]
    history = state.recent_history(business_id)

    idea = ideas.next_pending(business_id)
    if idea:
        ideas.mark_status(business_id, idea["id"], "in_progress")
    active_idea_text = idea["text"] if idea else None

    strategy = strategist.run(business, history, model, active_idea=active_idea_text)
    priorities = strategy.get("priorities", [])

    research = researcher.run(business, priorities, model)
    findings = research.get("findings", [])

    marketing = marketer.run(business, priorities, findings, model, active_idea=active_idea_text)
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

    specialists: dict[str, Any] = {}
    for extra in business.get("extra_agents", []):
        role = extra.get("role", "specialist")
        focus = extra.get("focus", "")
        spec_result = specialist.run(business, role, focus, priorities, findings, model)
        outputs = spec_result.get("outputs", [])
        for output in outputs:
            item_id = outbox.submit(
                business_id,
                output.get("channel", "unknown"),
                output.get("action_type", "other"),
                {**output, "role": role},
            )
            outbox_ids.append(item_id)
        specialists[role] = {"active": bool(outputs), "focus": focus, "outputs": outputs}

    if idea:
        ideas.mark_status(business_id, idea["id"], "done")

    cycle_result = {
        "strategy": strategy,
        "research": research,
        "marketing": marketing,
        "operations": operations,
        "finance": finance_status,
        "outbox_ids": outbox_ids,
        "active_idea": {"id": idea["id"], "text": idea["text"]} if idea else None,
        "specialists": specialists,
    }
    state.record_cycle(business_id, cycle_result)
    return cycle_result


def _global_budget_status(businesses: list[dict[str, Any]], global_cap: float) -> dict[str, Any]:
    total_expense = sum(ledger.summary(b["id"])["expense"] for b in businesses)
    if global_cap and total_expense > global_cap:
        status = "over_budget"
    elif global_cap and total_expense > 0.8 * global_cap:
        status = "approaching_cap"
    else:
        status = "ok"
    return {
        "total_expense": total_expense,
        "global_monthly_budget_cap": global_cap,
        "status": status,
    }


def render_report(business: dict[str, Any], result: dict[str, Any]) -> str:
    lines = [f"## {business.get('name', business['id'])}", ""]

    active_idea = result.get("active_idea")
    if active_idea:
        lines.append(f"**This cycle expanded your idea:** _{active_idea['text']}_")
        lines.append("")

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
    n_specialist_outputs = sum(len(s["outputs"]) for s in result.get("specialists", {}).values())
    if n_drafts or n_ops or n_specialist_outputs:
        lines.append(
            f"**Pending your approval:** {n_drafts} content draft(s), "
            f"{n_ops} operational proposal(s), {n_specialist_outputs} specialist output(s) "
            "— run `python cli.py list-outbox`."
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


def render_overview(overview: dict[str, Any], global_budget: dict[str, Any]) -> str:
    lines = ["## Overview", ""]
    headline = overview.get("headline")
    if headline:
        lines.append(headline)
        lines.append("")
    focus_id = overview.get("focus_business_id")
    if focus_id:
        lines.append(f"**Focus today:** {focus_id} — {overview.get('focus_reason', '')}")
        lines.append("")
    notes = overview.get("notes", [])
    if notes:
        lines.append("**Portfolio notes:**")
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")

    cap = global_budget.get("global_monthly_budget_cap")
    lines.append(
        f"**Portfolio spend this month:** ${global_budget['total_expense']:.2f}"
        + (f" / ${cap:.2f} cap" if cap else "")
        + f" — status: **{global_budget['status']}**"
    )
    lines.append("")
    return "\n".join(lines)


def run_all(businesses: list[dict[str, Any]], model: str, global_budget_cap: float = 0) -> str:
    sections = [f"# Daily digest — {date.today().isoformat()}", ""]

    rooms_summary = []
    for business in businesses:
        result = run_cycle(business, model)
        sections.append(render_report(business, result))
        rooms_summary.append(
            {
                "id": business["id"],
                "name": business.get("name", business["id"]),
                "priorities": result["strategy"].get("priorities", []),
                "watch_items": result["strategy"].get("watch_items", []),
                "finance_status": result["finance"]["status"],
                "pending_count": len(result["outbox_ids"]),
            }
        )

    global_budget = _global_budget_status(businesses, global_budget_cap)
    overview = manager.run(rooms_summary, global_budget, model) if rooms_summary else {}
    state.record_cycle(state.OVERVIEW_ID, {"overview": overview, "global_budget": global_budget})
    sections.insert(2, render_overview(overview, global_budget))

    report = "\n".join(sections)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{date.today().isoformat()}.md"
    report_path.write_text(report)
    return str(report_path)
