import yaml

import dashboard
from src import state
from src.tools import ideas, ledger, outbox
from src.webapp import data as dashboard_data

BUSINESS = {
    "id": "biz1",
    "name": "Test Biz",
    "description": "A test business.",
    "monthly_budget_cap": 100,
}


def _patch_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(state, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path / "state")
    monkeypatch.setattr(outbox, "OUTBOX_DIR", tmp_path / "outbox")
    monkeypatch.setattr(outbox, "PENDING", tmp_path / "outbox" / "pending")
    monkeypatch.setattr(outbox, "APPROVED", tmp_path / "outbox" / "approved")
    monkeypatch.setattr(outbox, "REJECTED", tmp_path / "outbox" / "rejected")
    monkeypatch.setattr(dashboard_data, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(ideas, "IDEAS_DIR", tmp_path / "state")


def _write_businesses(tmp_path, businesses):
    (tmp_path / "businesses.yaml").write_text(yaml.safe_dump({"businesses": businesses}))


def test_setup_page_when_no_config(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    client = dashboard.app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"SETUP NEEDED" in resp.data


def test_station_view_with_no_cycle_run_yet(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    _write_businesses(tmp_path, [BUSINESS])

    client = dashboard.app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Test Biz" in resp.data
    assert b"No cycle run yet" in resp.data


def test_full_pipeline_view(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    _write_businesses(tmp_path, [BUSINESS])

    state.record_cycle(
        "biz1",
        {
            "strategy": {"priorities": ["Ship thing"], "watch_items": ["Traffic dipped"]},
            "research": {"live_data": False, "findings": ["General note"]},
        },
    )
    ledger.add_entry("biz1", "expense", 90.0, "ads")
    item_id = outbox.submit("biz1", "email", "email", {"body": "Hello there"})

    client = dashboard.app.test_client()

    resp = client.get("/")
    assert b"Ship thing" in resp.data
    assert b"1 pending approval" in resp.data
    assert b'status-light yellow' in resp.data  # 90/100 cap -> approaching_cap

    resp = client.get("/business/biz1")
    assert resp.status_code == 200
    assert b"Ship thing" in resp.data
    assert b"General note" in resp.data
    assert b"90.00" in resp.data

    resp = client.get("/outbox")
    assert b"Hello there" in resp.data

    resp = client.post(f"/outbox/{item_id}/approve", follow_redirects=True)
    assert resp.status_code == 200
    assert outbox.list_pending() == []


def test_station_shows_hq_panel_idle_before_any_run(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    _write_businesses(tmp_path, [BUSINESS])
    client = dashboard.app.test_client()
    resp = client.get("/")
    assert b"OVERVIEW" in resp.data
    assert b"HQ online" in resp.data


def test_station_shows_hq_panel_after_manager_cycle(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    _write_businesses(tmp_path, [BUSINESS])

    state.record_cycle(
        state.OVERVIEW_ID,
        {
            "overview": {
                "headline": "One business is stalled.",
                "focus_business_id": "biz1",
                "focus_reason": "no cycle run yet",
                "notes": ["keep an eye on spend"],
            },
            "global_budget": {"total_expense": 12.5, "global_monthly_budget_cap": 100, "status": "ok"},
        },
    )

    client = dashboard.app.test_client()
    resp = client.get("/")
    assert b"One business is stalled." in resp.data
    assert b"Test Biz" in resp.data  # focus_business_name resolved from id
    assert b"no cycle run yet" in resp.data
    assert b"keep an eye on spend" in resp.data


def test_add_idea_via_dashboard(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    _write_businesses(tmp_path, [BUSINESS])
    client = dashboard.app.test_client()

    resp = client.post("/business/biz1/ideas", data={"text": "a video about keyboard switches"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"a video about keyboard switches" in resp.data
    assert b"pending" in resp.data

    queued = ideas.list_ideas("biz1")
    assert len(queued) == 1
    assert queued[0]["text"] == "a video about keyboard switches"


def test_add_idea_ignores_blank_text(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    _write_businesses(tmp_path, [BUSINESS])
    client = dashboard.app.test_client()
    client.post("/business/biz1/ideas", data={"text": "   "}, follow_redirects=True)
    assert ideas.list_ideas("biz1") == []


def test_add_idea_404_for_unknown_business(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    _write_businesses(tmp_path, [BUSINESS])
    client = dashboard.app.test_client()
    resp = client.post("/business/does-not-exist/ideas", data={"text": "x"})
    assert resp.status_code == 404


def test_business_detail_404_for_unknown_id(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    _write_businesses(tmp_path, [BUSINESS])
    client = dashboard.app.test_client()
    resp = client.get("/business/does-not-exist")
    assert resp.status_code == 404


def test_reports_empty_and_read_report(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    _write_businesses(tmp_path, [BUSINESS])
    client = dashboard.app.test_client()

    resp = client.get("/reports")
    assert b"No reports yet" in resp.data

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "2026-09-08.md").write_text("# Daily digest\nhello")

    resp = client.get("/reports")
    assert b"2026-09-08.md" in resp.data

    resp = client.get("/reports/2026-09-08.md")
    assert b"hello" in resp.data

    # path traversal attempt must not escape reports/
    resp = client.get("/reports/..%2Fbusinesses.yaml")
    assert resp.status_code == 404
