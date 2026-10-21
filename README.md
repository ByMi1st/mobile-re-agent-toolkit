# Mobile RE Agent Toolkit

[![Tests](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

English | [简体中文](README.zh-CN.md)

A small, terminal-first toolkit for authorized Android reverse-engineering work.
It is not an agent framework, decompiler, or large MCP tool catalog.

## v0.2.0: six commands

| Command | Purpose |
|---|---|
| `fingerprint` | Stream local file SHA-256 and size |
| `search-exports` | Bounded literal search with file/line evidence, not semantic xref |
| `summarize-events` | Basic JSONL envelope checks and event counts |
| `generate-java-hook` | Exact Java overload probe source generation |
| `generate-native-hook` | Module/symbol or offset probe, raw entry/return and bounded binary snapshots |
| `run` | Explicit local/device/remote Frida spawn or attach, messages and cleanup |

Offline commands need only Python. Runtime bindings are optional. No private
samples, production captures or credentials are bundled.

## Install and try

Requires Python 3.10+. From a repository checkout:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
mrat --help
mrat fingerprint examples/exports/0x1000.c
mrat search-exports examples/exports memcpy --limit 10
mrat summarize-events examples/events.jsonl
mrat generate-java-hook \
  --class 'example.Target' --method run \
  --overload java.lang.String --out /tmp/example-hook.js
```

For runtime capture, install `python -m pip install ".[runtime]"`.
See [runtime guide](docs/runtime.md) for actual effects, limits and the
source-built end-to-end verification example. No PyPI release is claimed. See [setup](docs/setup.md) for source-only usage,
exit codes and prerequisites for manually running a generated script.

## Generated events

Java invocation events include PID/TID, an invocation ID, method and overload,
arguments, return value, exception, stack and optional scene/request labels.
Labels are caller-supplied, not automatic causal attribution. Values use bounded
text previews, not lossless Java object or binary serialization. The duration
uses wall-clock milliseconds and is not a precision benchmark.

Logging failures do not replace the original method's return value or exception.
Instrumentation can still affect timing and behavior; an observation label is
not evidence that the process was untouched. Scripts require an available Frida
Java bridge. Real Android compatibility has not yet been verified.

## Scope

JADX, IDA, Unicorn and semantic-reference utilities remain external analyst
tools. This repository does not migrate or wrap all of them. It does not ship
certificate bypasses, kernel probes, flashing packages, company tools, RPC
servers or target-specific algorithms.

The generic runner and native probe generator are implemented in v0.2.0.
Platform compatibility is established only by the real verification results in
[verification](docs/verification.md); Android remains unverified. See [status](docs/status.md),
[architecture](docs/architecture.md), [roadmap](docs/roadmap.md) and the
[practical workflow (中文)](docs/workflow.zh-CN.md).

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Node.js is optional for running the synthetic JavaScript test. If absent, that
test explicitly skips; Python tests do not establish phone compatibility.

## License

Copyright 2026 Meb1us (GitHub: ByMi1st). Licensed under [Apache-2.0](LICENSE).
The standard license appendix is an application example; the project copyright
notice appears at the top of the license.
