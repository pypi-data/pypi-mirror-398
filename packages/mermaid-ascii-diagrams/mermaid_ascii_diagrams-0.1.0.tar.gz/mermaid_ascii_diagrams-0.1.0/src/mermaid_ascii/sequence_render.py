from __future__ import annotations

from typing import Dict, List, Tuple

from .sequence_model import Activate, Deactivate, Message, SequenceDiagram


def _make_canvas(w: int, h: int) -> List[List[str]]:
    return [[" " for _ in range(w)] for __ in range(h)]


def _put(canvas: List[List[str]], x: int, y: int, ch: str) -> None:
    if 0 <= y < len(canvas) and 0 <= x < len(canvas[0]):
        canvas[y][x] = ch


def _hline(canvas: List[List[str]], x1: int, x2: int, y: int, ch: str) -> None:
    if x2 < x1:
        x1, x2 = x2, x1
    for x in range(x1, x2 + 1):
        _put(canvas, x, y, ch)


def _box(canvas: List[List[str]], x: int, y: int, w: int, h: int) -> None:
    _put(canvas, x, y, "┌")
    _put(canvas, x + w - 1, y, "┐")
    _put(canvas, x, y + h - 1, "└")
    _put(canvas, x + w - 1, y + h - 1, "┘")
    for xx in range(x + 1, x + w - 1):
        _put(canvas, xx, y, "─")
        _put(canvas, xx, y + h - 1, "─")
    for yy in range(y + 1, y + h - 1):
        _put(canvas, x, yy, "│")
        _put(canvas, x + w - 1, yy, "│")


def _center_text(canvas: List[List[str]], x: int, y: int, w: int, text: str) -> None:
    inner = max(0, w - 2)
    if len(text) > inner and inner >= 1:
        text = text[: inner - 1] + "…"
    start = x + 1 + max(0, (inner - len(text)) // 2)
    for i, c in enumerate(text):
        _put(canvas, start + i, y, c)


def render_sequence_ascii(
    sd: SequenceDiagram,
    *,
    min_participant_width: int = 10,
    box_height: int = 3,
    hgap: int = 6,
    vgap: int = 2,
    padding: int = 2,
    show_message_text: bool = True,
) -> str:
    widths: Dict[str, int] = {}
    for p in sd.participants:
        needed = len(p.label) + 2
        widths[p.name] = max(min_participant_width, needed + 2)

    x = padding
    px: Dict[str, int] = {}
    pw: Dict[str, int] = {}
    centers: Dict[str, int] = {}
    for p in sd.participants:
        px[p.name] = x
        pw[p.name] = widths[p.name]
        centers[p.name] = x + widths[p.name] // 2
        x += widths[p.name] + hgap

    lifeline_xs = set(centers.values())

    total_w = x + padding
    lifeline_start_y = padding + box_height
    total_h = lifeline_start_y + (len(sd.events) * vgap) + padding + 1

    canvas = _make_canvas(total_w, total_h)

    y0 = padding
    for p in sd.participants:
        _box(canvas, px[p.name], y0, pw[p.name], box_height)
        _center_text(canvas, px[p.name], y0 + 1, pw[p.name], p.label)

    active_stack: Dict[str, List[int]] = {p.name: [] for p in sd.participants}
    intervals: Dict[str, List[Tuple[int, int]]] = {p.name: [] for p in sd.participants}

    def start_active(name: str, y: int) -> None:
        active_stack.setdefault(name, []).append(y)

    def end_active(name: str, y: int) -> None:
        st = active_stack.setdefault(name, [])
        if st:
            y0a = st.pop()
            intervals.setdefault(name, []).append((y0a, y))

    for i, ev in enumerate(sd.events):
        y = lifeline_start_y + i * vgap
        if isinstance(ev, Activate):
            start_active(ev.participant, y)
        elif isinstance(ev, Deactivate):
            end_active(ev.participant, y)
        elif isinstance(ev, Message):
            if ev.activate_receiver:
                start_active(ev.receiver, y)
            if ev.deactivate_receiver:
                end_active(ev.receiver, y)

    end_y = lifeline_start_y + max(0, (len(sd.events) - 1) * vgap) + vgap
    for name, st in active_stack.items():
        while st:
            y0a = st.pop()
            intervals[name].append((y0a, end_y))

    # lifelines continuous, activations overlay
    for p in sd.participants:
        cx = centers[p.name]
        for y in range(lifeline_start_y, total_h - padding):
            _put(canvas, cx, y, "┆")
        for a0, a1 in intervals[p.name]:
            for y in range(max(lifeline_start_y, a0), min(total_h - padding, a1 + 1)):
                _put(canvas, cx, y, "║")

    for i, ev in enumerate(sd.events):
        y = lifeline_start_y + i * vgap
        if not isinstance(ev, Message):
            continue

        sx = centers.get(ev.sender)
        rx = centers.get(ev.receiver)
        if sx is None or rx is None:
            continue

        line_ch = "─" if ev.line_style == "solid" else "┄"
        _hline(canvas, sx, rx, y, line_ch)

        if ev.arrow == "arrow":
            if rx > sx:
                _put(canvas, rx, y, "►")
            elif rx < sx:
                _put(canvas, rx, y, "◄")
            else:
                _put(canvas, rx, y, "●")

        if show_message_text and ev.text:
            mid = (sx + rx) // 2
            ty = y - 1
            if ty > y0 + box_height - 1:
                text = ev.text
                start = max(padding, mid - len(text) // 2)
                for j, c in enumerate(text):
                    tx = start + j
                    if tx not in lifeline_xs:
                        _put(canvas, tx, ty, c)

    lines = ["".join(row).rstrip() for row in canvas]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)
