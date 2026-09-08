from src.orchestrator import _global_budget_status, render_overview, render_report
from src.tools import ledger


def test_global_budget_status_thresholds(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path)
    businesses = [{"id": "a"}, {"id": "b"}]

    assert _global_budget_status(businesses, 100)["status"] == "ok"

    ledger.add_entry("a", "expense", 85.0, "ads")
    assert _global_budget_status(businesses, 100)["status"] == "approaching_cap"

    ledger.add_entry("b", "expense", 20.0, "ads")
    result = _global_budget_status(businesses, 100)
    assert result["status"] == "over_budget"
    assert result["total_expense"] == 105.0


def test_global_budget_status_no_cap_never_flags(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path)
    ledger.add_entry("a", "expense", 9999.0, "big spend")
    result = _global_budget_status([{"id": "a"}], 0)
    assert result["status"] == "ok"


def _finance_stub(status="ok", cap=0.0):
    return {
        "month": "2026-09",
        "recorded_revenue": 0.0,
        "recorded_expense": 0.0,
        "recorded_net": 0.0,
        "monthly_budget_cap": cap,
        "status": status,
    }


def test_render_report_includes_active_idea():
    result = {
        "strategy": {"priorities": ["ship it"], "watch_items": []},
        "research": {"findings": []},
        "marketing": {"drafts": []},
        "operations": {"proposed_actions": []},
        "specialists": {},
        "finance": _finance_stub(),
        "active_idea": {"id": "abc123", "text": "a video about keyboard switches"},
    }
    report = render_report({"id": "biz1", "name": "Biz One"}, result)
    assert "a video about keyboard switches" in report
    assert "ship it" in report


def test_render_report_counts_specialist_outputs():
    result = {
        "strategy": {"priorities": [], "watch_items": []},
        "research": {"findings": []},
        "marketing": {"drafts": []},
        "operations": {"proposed_actions": []},
        "specialists": {"seo_researcher": {"active": True, "outputs": [{"body": "x"}, {"body": "y"}]}},
        "finance": _finance_stub(),
        "active_idea": None,
    }
    report = render_report({"id": "biz1", "name": "Biz One"}, result)
    assert "2 specialist output(s)" in report


def test_render_overview_with_focus():
    overview = {
        "headline": "Everything is mostly fine.",
        "focus_business_id": "biz1",
        "focus_reason": "revenue dropped",
        "notes": ["watch business 2"],
    }
    global_budget = {"total_expense": 42.5, "global_monthly_budget_cap": 100, "status": "ok"}
    report = render_overview(overview, global_budget)
    assert "Everything is mostly fine." in report
    assert "biz1" in report
    assert "revenue dropped" in report
    assert "42.50" in report
