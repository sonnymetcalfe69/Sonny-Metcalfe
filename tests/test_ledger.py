from src.tools import ledger


def test_add_entry_and_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path)

    ledger.add_entry("biz1", "revenue", 100.0, "sale", entry_date="2026-09-01")
    ledger.add_entry("biz1", "expense", 30.0, "ads", entry_date="2026-09-02")
    ledger.add_entry("biz1", "expense", 5.0, "ads last month", entry_date="2026-08-15")

    summary = ledger.summary("biz1", month="2026-09")
    assert summary["revenue"] == 100.0
    assert summary["expense"] == 30.0
    assert summary["net"] == 70.0


def test_add_entry_rejects_bad_kind(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path)
    try:
        ledger.add_entry("biz1", "profit", 1.0, "bad")
        assert False, "expected ValueError"
    except ValueError:
        pass
