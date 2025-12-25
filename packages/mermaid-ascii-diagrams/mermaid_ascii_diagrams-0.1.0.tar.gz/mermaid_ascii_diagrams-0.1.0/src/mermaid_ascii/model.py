from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal

NodeId = str
NodeShape = Literal["box", "rounded", "diamond"]


@dataclass(frozen=True)
class Node:
    id: NodeId
    label: str
    shape: NodeShape = "box"


@dataclass(frozen=True)
class Edge:
    src: NodeId
    dst: NodeId


@dataclass
class Graph:
    nodes: Dict[NodeId, Node]
    edges: List[Edge]
    direction: str = "TB"  # TB, BT, LR, RL

    def outgoing(self) -> Dict[NodeId, List[NodeId]]:
        out: Dict[NodeId, List[NodeId]] = {nid: [] for nid in self.nodes}
        for e in self.edges:
            out.setdefault(e.src, []).append(e.dst)
            out.setdefault(e.dst, [])
        return out

    def incoming_counts(self) -> Dict[NodeId, int]:
        inc = {nid: 0 for nid in self.nodes}
        for e in self.edges:
            inc.setdefault(e.src, 0)
            inc[e.dst] = inc.get(e.dst, 0) + 1
        return inc
