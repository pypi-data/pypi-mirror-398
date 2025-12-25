from __future__ import annotations

import re
from typing import Dict, List

from .model import Edge, Graph, Node

_STATE_HEADER_RE = re.compile(r"^\s*stateDiagram(?:-v2)?\b", re.IGNORECASE)
_TRANS_RE = re.compile(r"^\s*(?P<src>\[\*\]|[A-Za-z0-9_]+)\s*-->\s*(?P<dst>\[\*\]|[A-Za-z0-9_]+)(?:\s*:\s*(?P<label>.*))?\s*$")
_ALIAS_RE = re.compile(r'^\s*state\s+"(?P<label>[^"]+)"\s+as\s+(?P<id>[A-Za-z0-9_]+)\s*$', re.IGNORECASE)
_DECL_RE = re.compile(r"^\s*state\s+(?P<id>[A-Za-z0-9_]+)\s*$", re.IGNORECASE)


def parse_mermaid_state(src: str) -> Graph:
    lines = src.splitlines()

    start_idx = None
    for i, line in enumerate(lines):
        if _STATE_HEADER_RE.search(line):
            start_idx = i + 1
            break
    if start_idx is None:
        raise ValueError("Not a stateDiagram")

    nodes: Dict[str, Node] = {}
    edges: List[Edge] = []
    aliases: Dict[str, str] = {}

    def norm(tok: str) -> str:
        return "STAR" if tok == "[*]" else tok

    def ensure(nid: str, label: str | None = None) -> None:
        if nid not in nodes:
            nodes[nid] = Node(id=nid, label=label or nid, shape="box")

    for raw in lines[start_idx:]:
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue

        m = _ALIAS_RE.match(line)
        if m:
            sid = m.group("id")
            label = m.group("label").strip()
            aliases[sid] = label
            ensure(sid, label=label)
            continue

        m = _DECL_RE.match(line)
        if m:
            sid = m.group("id")
            ensure(sid, label=aliases.get(sid, sid))
            continue

        m = _TRANS_RE.match(line)
        if m:
            s = norm(m.group("src"))
            d = norm(m.group("dst"))

            ensure(s, label="[*]" if s == "STAR" else aliases.get(s, s))
            ensure(d, label="[*]" if d == "STAR" else aliases.get(d, d))

            edges.append(Edge(src=s, dst=d))
            continue

        continue

    return Graph(nodes=nodes, edges=edges, direction="TB")
