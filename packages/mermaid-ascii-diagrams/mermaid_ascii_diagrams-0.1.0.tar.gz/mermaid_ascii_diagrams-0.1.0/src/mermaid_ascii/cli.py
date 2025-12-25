from __future__ import annotations

import argparse
import sys
import re
from pathlib import Path
from typing import List, Optional

from . import parse_mermaid, render_ascii

FENCE_RE = re.compile(
    r"""(?P<fence>```+)\s*mermaid\s*\n(?P<code>.*?)\n(?P=fence)\s*""",
    re.IGNORECASE | re.DOTALL,
)


def extract_mermaid_blocks(markdown: str) -> List[str]:
    return [m.group("code").strip("\n") for m in FENCE_RE.finditer(markdown)]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="mermaid-ascii", description="Render Mermaid diagrams in Markdown to ASCII/Unicode art.")
    parser.add_argument("path", help="Markdown file path, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Write output to file instead of stdout")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--first", action="store_true", help="Render only the first Mermaid block")
    g.add_argument("--index", type=int, help="Render only the Mermaid block at this index (0-based)")
    parser.add_argument("--markdown", action="store_true", help="Wrap each rendered diagram in a ```text fenced block")
    args = parser.parse_args(argv)

    if args.path == "-":
        md = sys.stdin.read()
    else:
        md = Path(args.path).read_text(encoding="utf-8")

    blocks = extract_mermaid_blocks(md)
    if not blocks:
        msg = "No ```mermaid fenced blocks found.\n"
        if args.output:
            Path(args.output).write_text(msg, encoding="utf-8")
        else:
            sys.stdout.write(msg)
        return 1

    if args.first:
        blocks = blocks[:1]
    elif args.index is not None:
        if args.index < 0 or args.index >= len(blocks):
            msg = f"Index {args.index} out of range (found {len(blocks)} Mermaid blocks).\n"
            if args.output:
                Path(args.output).write_text(msg, encoding="utf-8")
            else:
                sys.stdout.write(msg)
            return 1
        blocks = [blocks[args.index]]

    rendered = []
    for b in blocks:
        diagram = parse_mermaid(b)
        art = render_ascii(diagram)
        rendered.append(f"```text\n{art}\n```" if args.markdown else art)

    divider = "\n\n" + ("-" * 20) + "\n\n"
    final = divider.join(rendered) + "\n"

    if args.output:
        Path(args.output).write_text(final, encoding="utf-8")
    else:
        sys.stdout.write(final)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
