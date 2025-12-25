from .parse import parse_mermaid_flowchart
from .render import render_flowchart_ascii

from .sequence_parse import parse_mermaid_sequence
from .sequence_render import render_sequence_ascii

from .class_parse import parse_mermaid_class
from .state_parse import parse_mermaid_state


def parse_mermaid(src: str):
    s = src.lstrip()
    low = s.lower()

    if low.startswith(("flowchart", "graph")):
        return parse_mermaid_flowchart(src)
    if low.startswith("sequencediagram"):
        return parse_mermaid_sequence(src)
    if low.startswith("classdiagram"):
        return parse_mermaid_class(src)
    if low.startswith("statediagram"):
        return parse_mermaid_state(src)

    return parse_mermaid_flowchart(src)


def render_ascii(diagram) -> str:
    if hasattr(diagram, "direction") and hasattr(diagram, "edges"):
        return render_flowchart_ascii(diagram)
    if hasattr(diagram, "events") and hasattr(diagram, "participants"):
        return render_sequence_ascii(diagram)
    raise TypeError(f"Unsupported diagram type: {type(diagram)}")


__all__ = [
    "parse_mermaid_flowchart",
    "render_flowchart_ascii",
    "parse_mermaid_sequence",
    "render_sequence_ascii",
    "parse_mermaid_class",
    "parse_mermaid_state",
    "parse_mermaid",
    "render_ascii",
]
