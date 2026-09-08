"""Finance: deterministic bookkeeping, not an LLM call.

Budget math should be exact, not something an LLM approximates. This reads
the ledger (state/<business_id>_ledger.json — entries you or an approved
outbox item add manually) plus this cycle's proposed spend from Ops, and
flags risk against the business's monthly_budget_cap.
"""

from __future__ import annotations

from typing import Any

from src.tools import ledger


def run(business: dict[str, Any], proposed_actions: list[dict[str, Any]]) -> dict[str, Any]:
    cap = business.get("monthly_budget_cap", 0)
    month_summary = ledger.summary(business["id"])
    proposed_spend = sum(
        a.get("estimated_cost", 0) for a in proposed_actions if a.get("requires_budget")
    )
    projected_expense = month_summary["expense"] + proposed_spend

    if cap and projected_expense > cap:
        status = "over_budget"
    elif cap and projected_expense > 0.8 * cap:
        status = "approaching_cap"
    else:
        status = "ok"

    return {
        "month": month_summary["month"],
        "recorded_revenue": month_summary["revenue"],
        "recorded_expense": month_summary["expense"],
        "recorded_net": month_summary["net"],
        "proposed_new_spend": proposed_spend,
        "projected_expense_if_approved": projected_expense,
        "monthly_budget_cap": cap,
        "status": status,
    }
