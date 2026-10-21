"""Command-line interface for Mobile RE Agent Toolkit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .java_hook import generate_java_hook
from .model import JavaMethodSpec, ProbeContext
from .offline import fingerprint, search_exports, summarize_events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mrat")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser(
        "generate-java-hook", help="generate a structured Frida Java probe"
    )
    generate.add_argument("--class", dest="class_name", required=True)
    generate.add_argument("--method", dest="method_name", required=True)
    generate.add_argument("--overload", nargs="*", default=[])
    generate.add_argument("--scene-id")
    generate.add_argument("--request-id")
    generate.add_argument(
        "--mode", choices=("natural", "controlled"), default="natural"
    )
    generate.add_argument("--no-stack", action="store_true")
    generate.add_argument("--out", type=Path, required=True)
    search = subparsers.add_parser("search-exports", help="search local IDA/JADX text exports")
    search.add_argument("root", type=Path)
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=30)
    register = subparsers.add_parser("fingerprint", help="hash a local artifact")
    register.add_argument("path", type=Path)
    events = subparsers.add_parser("summarize-events", help="check JSONL envelopes")
    events.add_argument("path", type=Path)
    return parser


def _run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {"search-exports", "fingerprint", "summarize-events"}:
        try:
            if args.command == "search-exports":
                result = search_exports(args.root, args.query, args.limit)
            elif args.command == "fingerprint":
                result = fingerprint(args.path)
            else:
                result = summarize_events(args.path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("valid", True) else 1
        except (OSError, ValueError) as error:
            print(json.dumps({"error": str(error)}, ensure_ascii=False))
            return 2
    if args.command == "generate-java-hook":
        source = generate_java_hook(
            JavaMethodSpec(
                class_name=args.class_name,
                method_name=args.method_name,
                overload=tuple(args.overload),
            ),
            ProbeContext(
                scene_id=args.scene_id,
                request_id=args.request_id,
                observation_mode=args.mode,
            ),
            include_stack=not args.no_stack,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(source, encoding="utf-8")
        print(args.out)
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    try:
        return _run(argv)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

