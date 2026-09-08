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


def test_build_stations_includes_hired_specialists():
    last_cycle = {
        "strategy": {"priorities": []},
        "research": {"findings": []},
        "marketing": {"drafts": []},
        "operations": {"proposed_actions": []},
        "specialists": {
            "seo_researcher": {"active": True, "outputs": [{"body": "x"}]},
            "video_editor": {"active": False, "outputs": []},
        },
    }
    stations = data.build_stations(last_cycle)
    assert len(stations) == 6  # 4 core + 2 hired
    by_role = {s["role"]: s for s in stations}
    assert by_role["seo_researcher"]["active"] is True
    assert by_role["seo_researcher"]["label"] == "Seo Researcher"
    assert by_role["video_editor"]["active"] is False


def test_role_color_is_stable_across_calls():
    assert sprites.role_color("seo_researcher") == sprites.role_color("seo_researcher")
    assert sprites.role_color("strategist") == sprites.ROLE_COLORS["strategist"]


def test_manager_svg_and_hq_console_svg():
    assert "<svg" in sprites.manager_svg()
    assert sprites.MANAGER_COLOR in sprites.hq_console_svg(active=True)
    assert sprites.IDLE_GLOW in sprites.hq_console_svg(active=False)
