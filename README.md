# Mobile RE Agent Toolkit

[![Tests](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

English | [简体中文](README.zh-CN.md)

Mobile RE Agent Toolkit (`mrat`) is a reverse-engineering toolchain for agents.
It gives an agent a small set of terminal commands with predictable output: every
result is JSON, every input file is hashed, and every answer says what it can and
cannot prove.

It does not replace jadx, IDA or Frida. It wraps them, so the agent calls them the
same way each time and the evidence stays on disk.

## How an agent uses it

Suppose you ask an agent: *"Find where this app builds the signature header, and
show me who calls that method."* A typical run looks like this:

1. `fingerprint` records the sample's SHA-256, so every later result is tied to it.
2. `locate-dex` finds the DEX file that defines the class.
3. `scope-apk` writes a smaller APK containing only that DEX, so jadx does not run out of memory.
4. `decompile-class` produces the readable source of the class.
5. `xref-method` lists the static callers, using the xref jar you provide.
6. A `generate-*-hook` command prepares a probe, and `run` observes the target on a device you name explicitly.

Each step writes its output to a file, and each result lists its own limits. The
agent can pick up where it stopped, and you can check every claim against the file.

## Commands

### Samples and baselines

| Command | What it does | What it does not prove |
|---|---|---|
| `fingerprint` | Hashes a file (SHA-256) and records its size. Run it first. | Where the sample came from |
| `diff-binary` | Compares two binaries by hash, and by section for ELF files. Useful after a version bump, before you rerun anything. | What a change does |

### Java / DEX

| Command | What it does | What it does not prove |
|---|---|---|
| `locate-dex` | Finds which root `classes*.dex` defines or mentions a class or a string. | That the code is called at runtime |
| `scope-apk` | Writes an analysis-only APK with the DEX files you choose. Fully indexing a large APK can exhaust memory, so narrow first. | Anything about DEX files you left out |
| `decompile-class` | Decompiles one class with the jadx CLI you point it at. Uses `--show-bad-code`, so check incorrect output before relying on it. | That the decompiled code is correct |
| `xref-method` | Lists static references to one method, using an xref jar you supply with `--jar`. | Reflection, dynamic dispatch or runtime calls |
| `search-exports` | Searches text exports from jadx or IDA and returns file and line. | Semantic references |

### Native

| Command | What it does | What it does not prove |
|---|---|---|
| `ida-run` | Runs an IDA headless batch script on a database, and records the log and the database hashes before and after. | The script's results, or anything IDA itself did |

### Dynamic (Frida)

| Command | What it does | What it does not prove |
|---|---|---|
| `generate-java-hook` | Generates a probe for one exact Java overload. | That the probe ran on a device |
| `generate-native-hook` | Generates a probe for an exported symbol or an offset. It records raw arguments, the return value and bounded buffer snapshots. | Argument types, or that the build matches |
| `run` | Runs a script against a target you name (a device, a remote endpoint or the local machine; attach by PID or spawn). It collects messages and cleans up. | What happened outside the capture window |

### Evidence

| Command | What it does | What it does not prove |
|---|---|---|
| `summarize-events` | Checks that a JSONL event file has the basic envelope and counts the events. | That the capture is complete or truthful |

Offline commands need only Python. Runtime bindings are optional.

## Install

Requires Python 3.10 or later. From a checkout:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
mrat --help
```

Try it on the bundled synthetic examples:

```bash
mrat fingerprint examples/exports/0x1000.c
mrat search-exports examples/exports memcpy --limit 10
mrat summarize-events examples/events.jsonl
mrat generate-java-hook \
  --class 'example.Target' --method run \
  --overload java.lang.String --out /tmp/example-hook.js
```

For runtime capture, also install `python -m pip install ".[runtime]"`. The
[runtime guide](docs/guides/runtime.md) lists the actual effects of each command, and
[setup](docs/guides/setup.md) covers exit codes and the prerequisites for running a
generated script by hand.

## Bring your own tools

This repository does not ship jadx, IDA, Frida, an xref jar, or any application
samples. You install or obtain them yourself, and you are responsible for their
licenses and versions. Pass their paths explicitly, for example `--jadx`, `--jar`,
`--idat` or `--java`. If you leave a flag out, the command looks for the tool on
your `PATH` and fails clearly when it is not there. The xref jar can also be set
once with the `MRAT_XREF_JAR` environment variable.

## What it can and cannot establish

- Static results are candidates until something else confirms them. The
  [workflow guide](docs/guides/workflow.zh-CN.md) describes the evidence grades
  (`confirmed_static`, `candidate`, `contradicted`) and how to use them.
- Generated Java probes report invocations with their arguments and return values
  as text previews. Logging failures do not change the original method's result, but
  instrumentation can still change timing and behavior.
- Android devices have not been tested. The native probe has been checked only against a
  source-built synthetic fixture, and the real jadx and IDA paths have not been run
  in CI. [Verification](docs/reference/verification.md) records what has actually run.

## Documentation

- [Workflow (中文)](docs/guides/workflow.zh-CN.md): the static analysis path, step by step, with pitfalls.
- [Runtime](docs/guides/runtime.md): capture, native probes, cleanup and limits.
- [Setup](docs/guides/setup.md): installation, exit codes and manual script execution.
- [Status](docs/reference/status.md): what is implemented, tested with stubs or synthetic data, or not built yet.
- [Architecture](docs/reference/architecture.md) and [roadmap](docs/reference/roadmap.md).

## Repository layout

```text
src/mrat/
  cli.py          command-line entry point
  core/           models and offline utilities: hashing, search, JSONL checks
  static/         DEX location, decompilation, xrefs, IDA runs, binary diff
  runtime/        probe generators and the Frida runner
docs/guides/      how-to guides: workflow, runtime, setup
docs/reference/   status, architecture, roadmap, verification, checklist
examples/         synthetic fixtures only
scripts/          real-provider verification scripts
tests/            unit and synthetic tests
```

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Node.js is optional. Without it, the synthetic JavaScript test is skipped. Passing
Python tests does not establish device compatibility. Contributions should stay
target-agnostic; see [CONTRIBUTING.md](CONTRIBUTING.md).

## Scope and responsibility

Use this toolkit only on software you own or are authorized to assess. The project
does not include certificate bypasses, kernel probes, flashing packages, company
tooling, RPC servers or target-specific algorithms, and it will not add them.

## License

Copyright 2026 Meb1us (GitHub: ByMi1st). Licensed under [Apache-2.0](LICENSE).
The standard license appendix is an application example; the project copyright
notice appears at the top of the license.
