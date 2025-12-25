from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .model import Edge, Graph, Node

_FLOWCHART_HEADER_RE = re.compile(r"^\s*(flowchart|graph)\s*(?P<dir>TB|BT|LR|RL)?\b", re.IGNORECASE)

_NODE_TOKEN_RE = re.compile(
    r"""
    ^\s*
    (?P<id>[A-Za-z0-9_]+)
    \s*
    (?:
        \[(?P<label_sq>[^\]]*)\] |
        \((?P<label_par>[^)]*)\) |
        \{(?P<label_cur>[^}]*)\}
    )?
    \s*$
    """,
    re.VERBOSE,
)

_ARROW_SPLIT_RE = re.compile(r"\s*(?:-->|---|==>)\s*")


def _parse_node_token(tok: str) -> Tuple[str, str, str]:
    """
    Returns (node_id, label, shape)

    shape:
      - "rounded" for A([Label]) stadium/terminator nodes
      - "diamond" for A{Label} decision nodes
      - "box" otherwise
    """
    tok = tok.strip()

    m = re.match(r"^\s*(?P<id>[A-Za-z0-9_]+)\s*\(\[(?P<label>[^\]]*)\]\)\s*$", tok)
    if m:
        nid = m.group("id")
        label = (m.group("label") or nid).strip()
        return nid, label, "rounded"

    m = _NODE_TOKEN_RE.match(tok)
    if not m:
        nid = re.sub(r"\W+", "_", tok.strip()) or "node"
        return nid, tok.strip() or nid, "box"

    nid = m.group("id")
    label_sq = m.group("label_sq")
    label_par = m.group("label_par")
    label_cur = m.group("label_cur")

    label = (label_sq or label_par or label_cur or nid).strip()
    shape = "diamond" if label_cur is not None else "box"
    return nid, label, shape


def parse_mermaid_flowchart(src: str) -> Graph:
    """
    Minimal Mermaid flowchart parser.
    """
    lines = src.splitlines()

    start_idx = 0
    direction = "TB"
    for i, line in enumerate(lines):
        m = _FLOWCHART_HEADER_RE.search(line)
        if m:
            start_idx = i + 1
            if m.group("dir"):
                direction = m.group("dir").upper()
            break

    nodes: Dict[str, Node] = {}
    edges: List[Edge] = []

    def ensure_node(tok: str) -> str:
        nid, label, shape = _parse_node_token(tok)
        if nid not in nodes:
            nodes[nid] = Node(id=nid, label=label, shape=shape)  # type: ignore[arg-type]
        else:
            existing = nodes[nid]
            upgraded = existing.shape
            if existing.shape == "box" and shape in ("rounded", "diamond"):
                upgraded = shape  # type: ignore[assignment]
            nodes[nid] = Node(id=nid, label=existing.label, shape=upgraded)  # type: ignore[arg-type]
        return nid

    for raw in lines[start_idx:]:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("%%"):
            continue
        lowered = line.lower()
        if lowered.startswith(("classdef", "class ", "style ", "linkstyle", "subgraph", "end", "direction")):
            continue

        line = re.sub(r"\|[^|]*\|", "", line)

        if not any(a in line for a in ("-->", "---", "==>")):
            continue

        parts = [p for p in _ARROW_SPLIT_RE.split(line) if p.strip()]
        if len(parts) < 2:
            continue

        ids = [ensure_node(p) for p in parts]
        for s, d in zip(ids, ids[1:]):
            edges.append(Edge(src=s, dst=d))

    return Graph(nodes=nodes, edges=edges, direction=direction)
