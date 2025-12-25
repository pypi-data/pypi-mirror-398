from mermaid_ascii import parse_mermaid, render_ascii

def test_smoke_flowchart():
    d = parse_mermaid("flowchart TD\nA-->B")
    art = render_ascii(d)
    assert isinstance(art, str)
    assert art.strip() != ""
