from __future__ import annotations

from typing import Dict, List, Set, Tuple

from .model import Graph
from .layout import Layout, compute_layout

_CONN_TO_CHAR: Dict[frozenset[str], str] = {
    frozenset(): " ",
    frozenset({"L"}): "─",
    frozenset({"R"}): "─",
    frozenset({"L", "R"}): "─",
    frozenset({"U"}): "│",
    frozenset({"D"}): "│",
    frozenset({"U", "D"}): "│",
    frozenset({"U", "R"}): "└",
    frozenset({"U", "L"}): "┘",
    frozenset({"D", "R"}): "┌",
    frozenset({"D", "L"}): "┐",
    frozenset({"L", "R", "U"}): "┴",
    frozenset({"L", "R", "D"}): "┬",
    frozenset({"U", "D", "R"}): "├",
    frozenset({"U", "D", "L"}): "┤",
    frozenset({"L", "R", "U", "D"}): "┼",
}

_ARROW_BY_DIR = {"R": "►", "L": "◄", "D": "▼", "U": "▲"}


def _add_conn(conn: List[List[Set[str]]], x: int, y: int, d: str) -> None:
    if 0 <= y < len(conn) and 0 <= x < len(conn[0]):
        conn[y][x].add(d)


def _connect(conn: List[List[Set[str]]], x1: int, y1: int, x2: int, y2: int) -> None:
    if x2 == x1 + 1 and y2 == y1:
        _add_conn(conn, x1, y1, "R")
        _add_conn(conn, x2, y2, "L")
    elif x2 == x1 - 1 and y2 == y1:
        _add_conn(conn, x1, y1, "L")
        _add_conn(conn, x2, y2, "R")
    elif y2 == y1 + 1 and x2 == x1:
        _add_conn(conn, x1, y1, "D")
        _add_conn(conn, x2, y2, "U")
    elif y2 == y1 - 1 and x2 == x1:
        _add_conn(conn, x1, y1, "U")
        _add_conn(conn, x2, y2, "D")
    else:
        raise ValueError("Points must be adjacent to connect")


def _draw_box(conn: List[List[Set[str]]], box) -> None:
    x0, y0, x1, y1 = box.left, box.top, box.right, box.bottom
    for x in range(x0, x1):
        _connect(conn, x, y0, x + 1, y0)
        _connect(conn, x, y1, x + 1, y1)
    for y in range(y0, y1):
        _connect(conn, x0, y, x0, y + 1)
        _connect(conn, x1, y, x1, y + 1)


def _draw_manhattan(conn: List[List[Set[str]]], points: List[Tuple[int, int]]) -> None:
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        x, y = x1, y1
        while (x, y) != (x2, y2):
            if x < x2:
                nx, ny = x + 1, y
            elif x > x2:
                nx, ny = x - 1, y
            elif y < y2:
                nx, ny = x, y + 1
            else:
                nx, ny = x, y - 1
            _connect(conn, x, y, nx, ny)
            x, y = nx, ny


def _route_edge(layout: Layout, src_id: str, dst_id: str) -> List[Tuple[int, int]]:
    s = layout.boxes[src_id]
    d = layout.boxes[dst_id]
    direction = layout.direction

    if direction in ("TB", "BT"):
        start = (s.cx, s.bottom + 1)
        end = (d.cx, d.top - 1)
        mid_y = (start[1] + end[1]) // 2
        if mid_y == start[1]:
            mid_y += 1
        if mid_y == end[1]:
            mid_y -= 1
        return [start, (start[0], mid_y), (end[0], mid_y), end]

    if direction in ("LR", "RL"):
        start = (s.right + 1, s.cy)
        end = (d.left - 1, d.cy)
        mid_x = (start[0] + end[0]) // 2
        if mid_x == start[0]:
            mid_x += 1
        if mid_x == end[0]:
            mid_x -= 1
        return [start, (mid_x, start[1]), (mid_x, end[1]), end]

    raise ValueError(f"Unsupported direction: {direction}")


def _overlay_rounded_box_corners(canvas: List[List[str]], conn: List[List[Set[str]]], box) -> None:
    corners = [
        (box.left, box.top, frozenset({"R", "D"}), "╭"),
        (box.right, box.top, frozenset({"L", "D"}), "╮"),
        (box.left, box.bottom, frozenset({"R", "U"}), "╰"),
        (box.right, box.bottom, frozenset({"L", "U"}), "╯"),
    ]
    for x, y, expected, glyph in corners:
        if 0 <= y < len(conn) and 0 <= x < len(conn[0]):
            if frozenset(conn[y][x]) == expected:
                canvas[y][x] = glyph


def _overlay_diamond(canvas: List[List[str]], box) -> None:
    x0, x1 = box.left, box.right
    y0, y1 = box.top, box.bottom
    if y1 - y0 < 2:
        return

    mid = y0 + (box.h // 2)

    for (x, y) in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        if 0 <= y < len(canvas) and 0 <= x < len(canvas[0]):
            canvas[y][x] = " "

    if 0 <= y0 < len(canvas):
        if 0 <= x0 + 1 < len(canvas[0]):
            canvas[y0][x0 + 1] = "╱"
        if 0 <= x1 - 1 < len(canvas[0]):
            canvas[y0][x1 - 1] = "╲"
        for x in range(x0 + 2, x1 - 1):
            canvas[y0][x] = "─"

    if 0 <= mid < len(canvas):
        canvas[mid][x0] = "│"
        canvas[mid][x1] = "│"

    if 0 <= y1 < len(canvas):
        if 0 <= x0 + 1 < len(canvas[0]):
            canvas[y1][x0 + 1] = "╲"
        if 0 <= x1 - 1 < len(canvas[0]):
            canvas[y1][x1 - 1] = "╱"
        for x in range(x0 + 2, x1 - 1):
            canvas[y1][x] = "─"


def _src_exit_and_step(layout: Layout, src_id: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    s = layout.boxes[src_id]
    d = layout.direction
    if d == "TB":
        return (s.cx, s.bottom), (s.cx, s.bottom + 1)
    if d == "BT":
        return (s.cx, s.top), (s.cx, s.top - 1)
    if d == "LR":
        return (s.right, s.cy), (s.right + 1, s.cy)
    if d == "RL":
        return (s.left, s.cy), (s.left - 1, s.cy)
    raise ValueError(f"Unsupported direction: {d}")


def _dst_outside_and_step(layout: Layout, dst_id: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    dbox = layout.boxes[dst_id]
    d = layout.direction
    if d == "TB":
        return (dbox.cx, dbox.top - 1), (dbox.cx, dbox.top)
    if d == "BT":
        return (dbox.cx, dbox.bottom + 1), (dbox.cx, dbox.bottom)
    if d == "LR":
        return (dbox.left - 1, dbox.cy), (dbox.left, dbox.cy)
    if d == "RL":
        return (dbox.right + 1, dbox.cy), (dbox.right, dbox.cy)
    raise ValueError(f"Unsupported direction: {d}")


def _dst_entry_and_arrow(layout: Layout, dst_id: str) -> Tuple[Tuple[int, int], str]:
    dbox = layout.boxes[dst_id]
    d = layout.direction
    if d == "TB":
        return (dbox.cx, dbox.top), "D"
    if d == "BT":
        return (dbox.cx, dbox.bottom), "U"
    if d == "LR":
        return (dbox.left, dbox.cy), "R"
    if d == "RL":
        return (dbox.right, dbox.cy), "L"
    raise ValueError(f"Unsupported direction: {d}")


def render_flowchart_ascii(
    g: Graph,
    *,
    min_box_width: int = 8,
    box_height: int = 3,
    hgap: int = 6,
    vgap: int = 4,
    padding: int = 2,
    arrowheads: bool = True,
) -> str:
    layout = compute_layout(
        g,
        min_box_width=min_box_width,
        box_height=box_height,
        hgap=hgap,
        vgap=vgap,
        padding=padding,
    )

    conn: List[List[Set[str]]] = [[set() for _ in range(layout.width)] for __ in range(layout.height)]

    for box in layout.boxes.values():
        _draw_box(conn, box)

    arrows: List[Tuple[int, int, str]] = []

    for e in g.edges:
        if e.src not in layout.boxes or e.dst not in layout.boxes:
            continue

        src_border, src_outside = _src_exit_and_step(layout, e.src)
        _connect(conn, src_border[0], src_border[1], src_outside[0], src_outside[1])

        dst_outside, dst_border = _dst_outside_and_step(layout, e.dst)
        _connect(conn, dst_outside[0], dst_outside[1], dst_border[0], dst_border[1])

        pts = _route_edge(layout, e.src, e.dst)
        _draw_manhattan(conn, pts)

        if arrowheads:
            (ax, ay), adir = _dst_entry_and_arrow(layout, e.dst)
            glyph = _ARROW_BY_DIR.get(adir)
            if glyph:
                arrows.append((ax, ay, glyph))

    canvas = [[" " for _ in range(layout.width)] for __ in range(layout.height)]
    for y in range(layout.height):
        for x in range(layout.width):
            canvas[y][x] = _CONN_TO_CHAR.get(frozenset(conn[y][x]), " ")

    for nid, box in layout.boxes.items():
        node = g.nodes.get(nid)
        if not node:
            continue
        if node.shape == "rounded":
            _overlay_rounded_box_corners(canvas, conn, box)
        elif node.shape == "diamond":
            _overlay_diamond(canvas, box)

    for box in layout.boxes.values():
        inner_w = box.w - 2
        label = box.label
        if len(label) > inner_w:
            label = label[: max(0, inner_w - 1)] + "…" if inner_w >= 1 else ""
        text_y = box.top + 1
        start_x = box.left + 1 + max(0, (inner_w - len(label)) // 2)
        for i, c in enumerate(label):
            x = start_x + i
            if box.left + 1 <= x <= box.right - 1 and 0 <= text_y < len(canvas):
                canvas[text_y][x] = c

    for x, y, glyph in arrows:
        if 0 <= y < len(canvas) and 0 <= x < len(canvas[0]):
            canvas[y][x] = glyph

    lines = ["".join(row).rstrip() for row in canvas]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)
