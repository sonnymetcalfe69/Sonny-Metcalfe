from src.agents import finance
from src.tools import ledger


def test_finance_status_ok_approaching_over(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path)
    business = {"id": "biz1", "monthly_budget_cap": 100}

    result = finance.run(business, proposed_actions=[])
    assert result["status"] == "ok"

    ledger.add_entry("biz1", "expense", 85.0, "ads")
    result = finance.run(business, proposed_actions=[])
    assert result["status"] == "approaching_cap"

    result = finance.run(
        business,
        proposed_actions=[{"estimated_cost": 20, "requires_budget": True}],
    )
    assert result["status"] == "over_budget"
    assert result["projected_expense_if_approved"] == 105.0


def test_finance_no_cap_never_flags(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path)
    business = {"id": "biz2", "monthly_budget_cap": 0}
    ledger.add_entry("biz2", "expense", 1000.0, "big spend")
    result = finance.run(business, proposed_actions=[])
    assert result["status"] == "ok"
