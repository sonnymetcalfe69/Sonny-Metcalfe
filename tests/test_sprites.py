from src.webapp import data, sprites


def test_worker_svg_uses_role_color():
    svg = sprites.worker_svg("marketer")
    assert "<svg" in svg
    assert sprites.ROLE_COLORS["marketer"] in svg


def test_desk_svg_glow_differs_active_vs_idle():
    active_svg = sprites.desk_svg(active=True)
    idle_svg = sprites.desk_svg(active=False)
    assert active_svg != idle_svg
    assert "#f5d523" in active_svg
    assert sprites.IDLE_GLOW in idle_svg


def test_build_stations_marks_roles_active_from_last_cycle():
    last_cycle = {
        "strategy": {"priorities": ["do the thing"]},
        "research": {"findings": []},
        "marketing": {"drafts": [{"body": "x"}]},
        "operations": {"proposed_actions": []},
    }
    stations = data.build_stations(last_cycle)
    active_roles = {s["role"] for s in stations if s["active"]}
    assert active_roles == {"strategist", "marketer"}
    assert len(stations) == 4


def test_build_stations_all_idle_for_empty_cycle():
    stations = data.build_stations({})
    assert all(not s["active"] for s in stations)
