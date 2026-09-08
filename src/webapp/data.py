"""View-model helpers for the dashboard: turns the on-disk state/outbox/
reports files into plain dicts the templates render. No business logic
lives here beyond shaping data — the pipeline itself is src/orchestrator.py."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src import state
from src.tools import ledger, outbox
from src.webapp import sprites

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"

STATUS_COLOR = {
    "ok": "green",
    "approaching_cap": "yellow",
    "over_budget": "red",
}

ROLE_LABELS = {
    "strategist": "Strategist",
    "researcher": "Researcher",
    "marketer": "Marketer",
    "ops": "Ops",
}

# Where in a cycle result to look to decide whether that role "did something"
# last cycle — used to light up (or dim) its console.
_ROLE_ACTIVITY_PATH = {
    "strategist": ("strategy", "priorities"),
    "researcher": ("research", "findings"),
    "marketer": ("marketing", "drafts"),
    "ops": ("operations", "proposed_actions"),
}


def build_stations(last_cycle: dict[str, Any]) -> list[dict[str, Any]]:
    stations = []
    for role, label in ROLE_LABELS.items():
        section, key = _ROLE_ACTIVITY_PATH[role]
        active = bool(last_cycle.get(section, {}).get(key))
        stations.append(
            {
                "role": role,
                "label": label,
                "active": active,
                "worker_svg": sprites.worker_svg(role),
                "desk_svg": sprites.desk_svg(active),
            }
        )
    return stations


def _finance_view(business_id: str, monthly_budget_cap: float) -> dict[str, Any]:
    summary = ledger.summary(business_id)
    cap = monthly_budget_cap or 0
    if cap and summary["expense"] > cap:
        status = "over_budget"
    elif cap and summary["expense"] > 0.8 * cap:
        status = "approaching_cap"
    else:
        status = "ok"
    pct = min(100, round((summary["expense"] / cap) * 100)) if cap else 0
    return {**summary, "monthly_budget_cap": cap, "status": status, "pct_of_cap": pct}


def station_overview(businesses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pending = outbox.list_pending()
    rooms = []
    for business in businesses:
        business_id = business["id"]
        biz_state = state.load(business_id)
        last_cycle = biz_state.get("last_cycle", {})
        finance = _finance_view(business_id, business.get("monthly_budget_cap", 0))
        room_pending = [p for p in pending if p["business_id"] == business_id]
        rooms.append(
            {
                "id": business_id,
                "name": business.get("name", business_id),
                "description": business.get("description", ""),
                "priorities": last_cycle.get("strategy", {}).get("priorities", []),
                "watch_items": last_cycle.get("strategy", {}).get("watch_items", []),
                "last_run_at": biz_state.get("last_cycle", {}).get("timestamp"),
                "finance": finance,
                "status_color": STATUS_COLOR.get(finance["status"], "gray"),
                "pending_count": len(room_pending),
                "has_run": bool(biz_state.get("history")),
                "stations": build_stations(last_cycle),
            }
        )
    return rooms


def business_detail(business: dict[str, Any]) -> dict[str, Any]:
    business_id = business["id"]
    biz_state = state.load(business_id)
    finance = _finance_view(business_id, business.get("monthly_budget_cap", 0))
    pending = [p for p in outbox.list_pending() if p["business_id"] == business_id]
    entries = list(reversed(ledger.load(business_id)))[:20]
    return {
        "business": business,
        "history": list(reversed(biz_state.get("history", [])))[:10],
        "finance": finance,
        "pending": pending,
        "ledger_entries": entries,
        "status_color": STATUS_COLOR.get(finance["status"], "gray"),
        "stations": build_stations(biz_state.get("last_cycle", {})),
    }


def all_pending_by_business(businesses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = {b["id"]: b.get("name", b["id"]) for b in businesses}
    items = outbox.list_pending()
    for item in items:
        item["business_name"] = names.get(item["business_id"], item["business_id"])
    return items


def list_reports() -> list[str]:
    if not REPORTS_DIR.exists():
        return []
    return sorted((p.name for p in REPORTS_DIR.glob("*.md")), reverse=True)


def read_report(filename: str) -> str | None:
    """Only ever reads a literal *.md filename directly inside reports/."""
    if "/" in filename or "\\" in filename or not filename.endswith(".md"):
        return None
    path = REPORTS_DIR / filename
    if path.resolve().parent != REPORTS_DIR.resolve() or not path.exists():
        return None
    return path.read_text()
