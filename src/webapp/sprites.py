"""Tiny pixel-art sprites for the dashboard: one worker + one desk/console
per agent role, rendered as inline SVG rects (crisp at any zoom, no image
assets to ship). Kept deliberately simple — a handful of colored blocks,
not real character art.
"""

from __future__ import annotations

import zlib

CELL = 4  # px per pixel

# 8 columns wide. 'C' is the role's shirt color, substituted per role;
# everything else is a fixed palette.
WORKER_GRID = [
    "..HHHH..",
    ".HHHHHH.",
    ".HSSSSH.",
    "..SSSS..",
    ".CCCCCC.",
    "CCCCCCCC",
    "CCCCCCCC",
    ".CC..CC.",
    ".CC..CC.",
    ".BB..BB.",
]

# Same person, but with a crown row on top — the manager, sitting above
# every other worker in the hierarchy.
MANAGER_GRID = [
    ".C.CC.C.",
    ".CCCCCC.",
    "..HHHH..",
    ".HHHHHH.",
    ".HSSSSH.",
    "..SSSS..",
    ".CCCCCC.",
    "CCCCCCCC",
    "CCCCCCCC",
    ".CC..CC.",
    ".CC..CC.",
    ".BB..BB.",
]

# 'G' is the console glow color (lit when the agent has fresh output).
DESK_GRID = [
    ".GGGGG..",
    ".GGGGG..",
    ".GGGGG..",
    "DDDDDDDD",
    "DDDDDDDD",
]

FIXED_COLORS = {
    "H": "#3a2a1a",  # hair
    "S": "#e0b088",  # skin
    "B": "#20233a",  # legs
    "D": "#5a3d23",  # desk wood
}

ROLE_COLORS = {
    "strategist": "#8a5cf6",
    "researcher": "#5cc8f6",
    "marketer": "#f65ca0",
    "ops": "#5cf68a",
}

# Any "hired" specialist role not in ROLE_COLORS above gets a consistent
# (but not hand-picked) color from this palette, keyed by its name.
SPECIALIST_PALETTE = ["#f6c85c", "#5cf6d8", "#c85cf6", "#f68a5c", "#5c8af6"]

MANAGER_COLOR = "#f5d523"
IDLE_GLOW = "#1c2038"


def role_color(role: str) -> str:
    """Deterministic across process restarts, unlike Python's randomized
    str hash() — a hired role should keep the same color every time."""
    if role in ROLE_COLORS:
        return ROLE_COLORS[role]
    idx = zlib.crc32(role.encode()) % len(SPECIALIST_PALETTE)
    return SPECIALIST_PALETTE[idx]


def _render_grid(grid: list[str], color_map: dict[str, str], cell: int = CELL) -> str:
    width = len(grid[0]) * cell
    height = len(grid) * cell
    rects = []
    for row_i, row in enumerate(grid):
        for col_i, char in enumerate(row):
            if char == ".":
                continue
            color = color_map.get(char)
            if not color:
                continue
            rects.append(
                f'<rect x="{col_i * cell}" y="{row_i * cell}" '
                f'width="{cell}" height="{cell}" fill="{color}"/>'
            )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'shape-rendering="crispEdges" xmlns="http://www.w3.org/2000/svg">'
        + "".join(rects)
        + "</svg>"
    )


def worker_svg(role: str) -> str:
    color_map = {**FIXED_COLORS, "C": role_color(role)}
    return _render_grid(WORKER_GRID, color_map)


def desk_svg(active: bool) -> str:
    color_map = {**FIXED_COLORS, "G": "#f5d523" if active else IDLE_GLOW}
    return _render_grid(DESK_GRID, color_map)


def manager_svg() -> str:
    color_map = {**FIXED_COLORS, "C": MANAGER_COLOR}
    return _render_grid(MANAGER_GRID, color_map)


def hq_console_svg(active: bool) -> str:
    color_map = {**FIXED_COLORS, "G": MANAGER_COLOR if active else IDLE_GLOW}
    return _render_grid(DESK_GRID, color_map, cell=CELL + 2)
