from __future__ import annotations

import re
from typing import Dict

from .sequence_model import Activate, Deactivate, Message, Participant, SequenceDiagram

_SEQ_HEADER_RE = re.compile(r"^\s*sequenceDiagram\b", re.IGNORECASE)
_PARTICIPANT_RE = re.compile(r"^\s*participant\s+(?P<name>[A-Za-z0-9_]+)(?:\s+as\s+(?P<label>.+))?\s*$", re.IGNORECASE)
_ACTIVATE_RE = re.compile(r"^\s*activate\s+(?P<name>[A-Za-z0-9_]+)\s*$", re.IGNORECASE)
_DEACTIVATE_RE = re.compile(r"^\s*deactivate\s+(?P<name>[A-Za-z0-9_]+)\s*$", re.IGNORECASE)

_MSG_RE = re.compile(
    r"""
    ^\s*
    (?P<sender>[A-Za-z0-9_]+)
    \s*
    (?P<arrow>-->>|->>|-->|->|--)
    \s*
    (?P<recvflag>[+\-]?)
    (?P<receiver>[A-Za-z0-9_]+)
    \s*
    (?:
        :\s*(?P<text>.*)
    )?
    \s*$
    """,
    re.VERBOSE,
)


def parse_mermaid_sequence(src: str) -> SequenceDiagram:
    lines = src.splitlines()

    start_idx = None
    for i, line in enumerate(lines):
        if _SEQ_HEADER_RE.search(line):
            start_idx = i + 1
            break
    if start_idx is None:
        raise ValueError("Not a sequenceDiagram")

    participants: Dict[str, Participant] = {}
    events = []

    def ensure_participant(name: str) -> None:
        if name not in participants:
            participants[name] = Participant(name=name, label=name)

    for raw in lines[start_idx:]:
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue

        m = _PARTICIPANT_RE.match(line)
        if m:
            name = m.group("name")
            label = (m.group("label") or name).strip()
            participants[name] = Participant(name=name, label=label)
            continue

        m = _ACTIVATE_RE.match(line)
        if m:
            name = m.group("name")
            ensure_participant(name)
            events.append(Activate(participant=name))
            continue

        m = _DEACTIVATE_RE.match(line)
        if m:
            name = m.group("name")
            ensure_participant(name)
            events.append(Deactivate(participant=name))
            continue

        m = _MSG_RE.match(line)
        if m:
            sender = m.group("sender")
            receiver = m.group("receiver")
            ensure_participant(sender)
            ensure_participant(receiver)

            arrow_tok = m.group("arrow")
            recvflag = m.group("recvflag") or ""
            text = (m.group("text") or "").strip()

            line_style = "dotted" if arrow_tok.startswith("--") else "solid"
            arrow = "noarrow" if arrow_tok == "--" else "arrow"

            events.append(
                Message(
                    sender=sender,
                    receiver=receiver,
                    text=text,
                    line_style=line_style,
                    arrow=arrow,
                    activate_receiver=(recvflag == "+"),
                    deactivate_receiver=(recvflag == "-"),
                )
            )
            continue

        continue

    return SequenceDiagram(participants=list(participants.values()), events=events)
