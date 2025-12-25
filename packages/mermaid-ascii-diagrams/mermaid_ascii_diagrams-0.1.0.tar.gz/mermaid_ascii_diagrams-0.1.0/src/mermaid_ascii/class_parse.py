from __future__ import annotations

import re
from typing import Dict, List

from .model import Edge, Graph, Node

_CLASS_HEADER_RE = re.compile(r"^\s*classDiagram\b", re.IGNORECASE)
_REL_SIMPLE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*([.<\|\*o\-]{2,})\s*([A-Za-z0-9_]+)(?:\s*:\s*(.*))?\s*$")
_CLASS_DECL_RE = re.compile(r"^\s*class\s+(?P<name>[A-Za-z0-9_]+)(?:\s*\{)?\s*$", re.IGNORECASE)


def parse_mermaid_class(src: str) -> Graph:
    lines = src.splitlines()

    start_idx = None
    for i, line in enumerate(lines):
        if _CLASS_HEADER_RE.search(line):
            start_idx = i + 1
            break
    if start_idx is None:
        raise ValueError("Not a classDiagram")

    nodes: Dict[str, Node] = {}
    edges: List[Edge] = []

    def ensure(nid: str) -> None:
        if nid not in nodes:
            nodes[nid] = Node(id=nid, label=nid, shape="box")

    for raw in lines[start_idx:]:
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue

        m = _CLASS_DECL_RE.match(line)
        if m:
            ensure(m.group("name"))
            continue

        if line.startswith(("{", "}", "+", "-", "#")):
            continue

        rm = _REL_SIMPLE.match(line)
        if not rm:
            continue

        left, rel, right = rm.group(1), rm.group(2), rm.group(3)
        ensure(left)
        ensure(right)

        if ">" in rel and "<" not in rel:
            edges.append(Edge(src=left, dst=right))
        elif "<" in rel and ">" not in rel:
            edges.append(Edge(src=right, dst=left))
        else:
            edges.append(Edge(src=left, dst=right))

    return Graph(nodes=nodes, edges=edges, direction="TB")
