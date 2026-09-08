"""Flat JSON ledger per business: state/<business_id>_ledger.json.

This only records entries you (or an approved outbox item, manually) add —
it has no access to any real bank or payment account. It's bookkeeping
memory for the Finance agent, not a source of truth about real money.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_DIR = Path(__file__).resolve().parent.parent.parent / "state"


def _path(business_id: str) -> Path:
    return LEDGER_DIR / f"{business_id}_ledger.json"


def load(business_id: str) -> list[dict[str, Any]]:
    path = _path(business_id)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def add_entry(
    business_id: str,
    kind: str,  # "revenue" or "expense"
    amount: float,
    description: str,
    entry_date: str | None = None,
) -> dict[str, Any]:
    if kind not in ("revenue", "expense"):
        raise ValueError("kind must be 'revenue' or 'expense'")
    entries = load(business_id)
    entry = {
        "id": f"{business_id}-{len(entries) + 1}",
        "date": entry_date or date.today().isoformat(),
        "kind": kind,
        "amount": amount,
        "description": description,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    _path(business_id).write_text(json.dumps(entries, indent=2))
    return entry


def summary(business_id: str, month: str | None = None) -> dict[str, float]:
    """month as 'YYYY-MM'; defaults to the current month."""
    month = month or date.today().isoformat()[:7]
    entries = [e for e in load(business_id) if e["date"].startswith(month)]
    revenue = sum(e["amount"] for e in entries if e["kind"] == "revenue")
    expense = sum(e["amount"] for e in entries if e["kind"] == "expense")
    return {"month": month, "revenue": revenue, "expense": expense, "net": revenue - expense}
