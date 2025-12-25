from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .model import Graph


@dataclass(frozen=True)
class Box:
    node_id: str
    label: str
    x: int
    y: int
    w: int
    h: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.w - 1

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.h - 1

    @property
    def cx(self) -> int:
        return self.x + self.w // 2

    @property
    def cy(self) -> int:
        return self.y + self.h // 2


@dataclass
class Layout:
    boxes: Dict[str, Box]
    width: int
    height: int
    ranks: List[List[str]]
    direction: str


def _topo_ranks(g: Graph) -> List[List[str]]:
    out = g.outgoing()
    inc = g.incoming_counts()

    ready = [nid for nid, deg in inc.items() if deg == 0]
    ready.sort()
    ranks: List[List[str]] = []
    placed = set()

    while ready:
        current = ready
        ranks.append(current)
        ready = []
        for nid in current:
            placed.add(nid)
            for nxt in out.get(nid, []):
                inc[nxt] -= 1
                if inc[nxt] == 0:
                    ready.append(nxt)
        ready.sort()

    remaining = [nid for nid in g.nodes.keys() if nid not in placed]
    remaining.sort()
    if remaining:
        ranks.append(remaining)

    if g.direction.upper() in ("BT", "RL"):
        ranks = list(reversed(ranks))

    return ranks


def compute_layout(
    g: Graph,
    *,
    min_box_width: int = 8,
    box_height: int = 3,
    hgap: int = 6,
    vgap: int = 4,
    padding: int = 2,
) -> Layout:
    ranks = _topo_ranks(g)
    direction = g.direction.upper()

    def box_w(label: str) -> int:
        needed = len(label) + 2
        return max(min_box_width, needed + 2)

    widths: Dict[str, int] = {nid: box_w(g.nodes[nid].label) for nid in g.nodes}
    boxes: Dict[str, Box] = {}

    if direction in ("TB", "BT"):
        row_widths: List[int] = []
        for row in ranks:
            if not row:
                row_widths.append(0)
                continue
            total = sum(widths[nid] for nid in row) + hgap * (len(row) - 1)
            row_widths.append(total)
        max_row_w = max(row_widths) if row_widths else 0

        y = padding
        for row, row_w in zip(ranks, row_widths):
            x = padding + max(0, (max_row_w - row_w) // 2)
            for nid in row:
                w = widths[nid]
                boxes[nid] = Box(nid, g.nodes[nid].label, x, y, w, box_height)
                x += w + hgap
            y += box_height + vgap

        content_w = max_row_w
        content_h = (len(ranks) * box_height) + max(0, (len(ranks) - 1) * vgap)
        return Layout(boxes, content_w + padding * 2, content_h + padding * 2, ranks, direction)

    if direction in ("LR", "RL"):
        col_heights: List[int] = []
        col_widths: List[int] = []
        for col in ranks:
            if not col:
                col_heights.append(0)
                col_widths.append(0)
                continue
            h = (len(col) * box_height) + vgap * (len(col) - 1)
            w = max(widths[nid] for nid in col)
            col_heights.append(h)
            col_widths.append(w)

        max_col_h = max(col_heights) if col_heights else 0

        x = padding
        for col, col_h, col_w in zip(ranks, col_heights, col_widths):
            y = padding + max(0, (max_col_h - col_h) // 2)
            for nid in col:
                w = widths[nid]
                boxes[nid] = Box(nid, g.nodes[nid].label, x, y, w, box_height)
                y += box_height + vgap
            x += col_w + hgap

        content_w = sum(col_widths) + (hgap * max(0, len(col_widths) - 1))
        content_h = max_col_h
        return Layout(boxes, content_w + padding * 2, content_h + padding * 2, ranks, direction)

    raise ValueError(f"Unsupported direction: {direction}")
