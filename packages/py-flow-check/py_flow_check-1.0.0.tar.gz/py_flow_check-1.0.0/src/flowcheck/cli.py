from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze


def main() -> None:
    parser = argparse.ArgumentParser(prog="flowcheck", description="Detect logical flow bugs in Python code")
    parser.add_argument("path", nargs="?", help="Python file to analyze. If omitted, reads from stdin.")
    parser.add_argument("--json", action="store_true", help="Output issues as JSON")
    args = parser.parse_args()

    if args.path:
        code = Path(args.path).read_text(encoding="utf-8")
    else:
        code = sys.stdin.read()

    issues = analyze(code)

    if args.json:
        payload = [
            {
                "code": i.code,
                "message": i.message,
                "line": i.line,
                "col": i.col,
                "reason": i.reason,
            }
            for i in issues
        ]
        print(json.dumps(payload, indent=2))
        raise SystemExit(1 if issues else 0)

    if not issues:
        print("No flow issues found.")
        raise SystemExit(0)

    for i in issues:
        print(i.format())
        print()

    raise SystemExit(1)
