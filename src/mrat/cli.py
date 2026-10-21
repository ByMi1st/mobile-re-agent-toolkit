"""Command-line interface for Mobile RE Agent Toolkit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .binary_diff import diff_binary
from .decompile import decompile_class
from .ida import ida_run
from .xref import xref_method
from .dex import locate_dex, scope_apk
from .java_hook import generate_java_hook
from .model import JavaMethodSpec, ProbeContext
from .native_hook import NativeProbeSpec, generate_native_hook
from .runner import RunSpec, capture
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
    native = subparsers.add_parser("generate-native-hook", help="generate a bounded Native observation probe")
    native.add_argument("--module", required=True)
    target = native.add_mutually_exclusive_group(required=True)
    target.add_argument("--symbol")
    target.add_argument("--offset")
    native.add_argument("--arg-count", type=int, default=0)
    native.add_argument("--buffer-arg", type=int)
    native.add_argument("--buffer-size", type=int, default=0)
    native.add_argument("--max-calls", type=int, default=1000)
    native.add_argument("--backtrace", action="store_true")
    native.add_argument("--out", type=Path, required=True)
    locate = subparsers.add_parser("locate-dex", help="find DEX entries that define or mention a class or string")
    locate.add_argument("apk", type=Path)
    locate_query = locate.add_mutually_exclusive_group(required=True)
    locate_query.add_argument("--class", dest="class_name")
    locate_query.add_argument("--text")
    scope = subparsers.add_parser("scope-apk", help="write an analysis-only APK with selected root DEX files")
    scope.add_argument("apk", type=Path)
    scope.add_argument("--dex", action="append", required=True)
    scope.add_argument("--out", type=Path, required=True)
    decompile = subparsers.add_parser("decompile-class", help="decompile one class with the jadx CLI")
    decompile.add_argument("apk", type=Path)
    decompile.add_argument("class_name")
    decompile.add_argument("--out", type=Path, required=True)
    decompile.add_argument("--jadx")
    decompile.add_argument("--timeout", type=float, default=300.0)
    xref = subparsers.add_parser("xref-method", help="list static references to a method via a user-supplied jar")
    xref.add_argument("apk", type=Path)
    xref.add_argument("class_name")
    xref.add_argument("method_name")
    xref.add_argument("--jar", type=Path, required=True)
    xref.add_argument("--out", type=Path, required=True)
    xref.add_argument("--java")
    xref.add_argument("--heap", default="4g")
    xref.add_argument("--timeout", type=float, default=600.0)
    ida = subparsers.add_parser("ida-run", help="run an IDA headless batch script on a database")
    ida.add_argument("database", type=Path)
    ida.add_argument("--script", type=Path, required=True)
    ida.add_argument("--log", type=Path, required=True)
    ida.add_argument("--idat")
    ida.add_argument("--timeout", type=float, default=1800.0)
    diff = subparsers.add_parser("diff-binary", help="compare two binaries by hash and ELF section")
    diff.add_argument("old", type=Path)
    diff.add_argument("new", type=Path)
    run = subparsers.add_parser("run", help="capture one script with explicit target and transport")
    transport = run.add_mutually_exclusive_group(required=True)
    transport.add_argument("--local", action="store_true")
    transport.add_argument("--device-id")
    transport.add_argument("--remote")
    target = run.add_mutually_exclusive_group(required=True)
    target.add_argument("--pid", type=int)
    target.add_argument("--spawn", nargs="+")
    run.add_argument("--script", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--require-ready", action="store_true")
    run.add_argument("--duration", type=float, default=10)
    run.add_argument("--setup-timeout", type=float, default=15)
    run.add_argument("--max-events", type=int, default=10000)
    run.add_argument("--max-message-bytes", type=int, default=262144)
    run.add_argument("--max-binary-bytes", type=int, default=65536)
    return parser


def _run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "locate-dex":
        result = locate_dex(args.apk, class_name=args.class_name, text=args.text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "scope-apk":
        result = scope_apk(args.apk, args.out, args.dex)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "decompile-class":
        result = decompile_class(args.apk, args.class_name, args.out, jadx=args.jadx, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "xref-method":
        result = xref_method(args.apk, args.class_name, args.method_name, args.out, jar=args.jar,
                             java=args.java, heap=args.heap, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "ida-run":
        result = ida_run(args.database, args.script, args.log, idat=args.idat, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "diff-binary":
        result = diff_binary(args.old, args.new)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "run":
        spec = RunSpec(script=args.script, out=args.out, duration=args.duration,
            local=args.local, device_id=args.device_id, remote=args.remote,
            pid=args.pid, spawn=tuple(args.spawn or []), max_events=args.max_events,
            max_message_bytes=args.max_message_bytes, max_binary_bytes=args.max_binary_bytes,
            setup_timeout=args.setup_timeout, require_ready=args.require_ready)
        result = capture(spec)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['success'] else 1
    if args.command == "generate-native-hook":
        source = generate_native_hook(NativeProbeSpec(module=args.module,
            symbol=args.symbol, offset=None if args.offset is None else int(args.offset, 0),
            arg_count=args.arg_count,
            buffer_arg=args.buffer_arg, buffer_size=args.buffer_size,
            max_calls=args.max_calls, backtrace=args.backtrace))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(source, encoding="utf-8")
        print(args.out)
        return 0
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
        except (OSError, ValueError, RuntimeError) as error:
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
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

