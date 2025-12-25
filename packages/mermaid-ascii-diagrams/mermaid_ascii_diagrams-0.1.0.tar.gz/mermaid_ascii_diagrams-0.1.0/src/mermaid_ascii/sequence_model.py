from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

LineStyle = Literal["solid", "dotted"]
ArrowStyle = Literal["arrow", "noarrow"]


@dataclass(frozen=True)
class Participant:
    name: str
    label: str


@dataclass(frozen=True)
class Message:
    sender: str
    receiver: str
    text: str
    line_style: LineStyle = "solid"
    arrow: ArrowStyle = "arrow"
    activate_receiver: bool = False
    deactivate_receiver: bool = False


@dataclass(frozen=True)
class Activate:
    participant: str


@dataclass(frozen=True)
class Deactivate:
    participant: str


Event = Message | Activate | Deactivate


@dataclass
class SequenceDiagram:
    participants: List[Participant]
    events: List[Event]
