# Mobile RE Agent Toolkit

[![Tests](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/ByMi1st/mobile-re-agent-toolkit/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

English | [简体中文](README.zh-CN.md)

Mobile RE Agent Toolkit (`mrat`) is a small command-line toolchain for Android
reverse engineering, designed to be driven by an agent. Each command produces
JSON output, records the hash of its inputs, and states what its result does
not establish.

The toolkit does not replace jadx, IDA or Frida. It wraps them so that every
call is reproducible and every result is saved as a file the agent, or a
person, can check.

## What it is for

Typical work on an authorized sample looks like this:

1. `fingerprint` records the sample's SHA-256. Later results refer to that hash.
2. `locate-dex` finds the DEX file that defines a class or contains a string.
3. `scope-apk` writes a smaller analysis APK with only the DEX files you chose.
4. `decompile-class` produces readable source for one class with the jadx CLI.
5. `xref-method` or `xref-serve` lists static callers, using an xref tool you build from this repository or supply yourself.
6. `generate-java-hook` or `generate-native-hook` prepares a probe, and `run` observes a target you name explicitly.

Every step writes its output to disk. A result lists its own limits, so an
agent can resume from a file and a reviewer can verify each claim.

## Commands

### Samples and baselines

| Command | What it does | What it does not establish |
|---|---|---|
| `fingerprint` | Computes the SHA-256 and size of a file. | Where the file came from |
| `diff-binary` | Compares two binaries by hash, and by section for ELF files. | What a change does |

### DEX and Java

| Command | What it does | What it does not establish |
|---|---|---|
| `locate-dex` | Finds root `classes*.dex` entries that define or mention a class or string. | Runtime use of the code |
| `scope-apk` | Writes an analysis-only APK with selected DEX files. | Anything about DEX files left out |
| `decompile-class` | Decompiles one class with a jadx CLI you specify. Uses `--show-bad-code`. | That the output is correct |
| `xref-method` | Lists static references to one method using an xref jar. | Reflection, dynamic dispatch or runtime calls |
| `xref-serve` | Keeps one xref process loaded for an APK and answers JSON lines on stdin. | The same as `xref-method` |
| `search-exports` | Searches text exports from jadx or IDA, returning file and line. | Semantic references |

### Native

| Command | What it does | What it does not establish |
|---|---|---|
| `ida-run` | Runs an IDA headless batch script and records the log and database hashes before and after. | The script's results |

### Dynamic (Frida)

| Command | What it does | What it does not establish |
|---|---|---|
| `generate-java-hook` | Generates a probe for one exact Java overload. | That the probe ran on a device |
| `generate-native-hook` | Generates a probe for an exported symbol or an offset, recording raw arguments, return value and bounded buffer snapshots. | Argument types, or that the build matches |
| `run` | Runs a script against a target you name (local, device or remote; attach by PID or spawn), collects messages and cleans up. | What happened outside the capture window |

### Evidence

| Command | What it does | What it does not establish |
|---|---|---|
| `summarize-events` | Checks the basic envelope of a JSONL event file and counts events. | That a capture is complete or accurate |

Offline commands need only Python. Runtime and Java tooling are optional.

## Quick start

Requires Python 3.10 or later.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
mrat --help
```

Try the bundled synthetic examples:

```bash
mrat fingerprint examples/exports/0x1000.c
mrat search-exports examples/exports memcpy --limit 10
mrat summarize-events examples/events.jsonl
mrat generate-java-hook --class 'example.Target' --method run \
  --overload java.lang.String --out /tmp/example-hook.js
```

Runtime capture needs the optional bindings: `python -m pip install ".[runtime]"`.
See [docs/guides/runtime.md](docs/guides/runtime.md) for the effects of each runtime
command and [docs/guides/setup.md](docs/guides/setup.md) for exit codes.

## Bring your own tools

The repository does not ship jadx, IDA, Frida, or any application sample. You
install these yourself and are responsible for their licenses and versions. Pass
paths explicitly with `--jadx`, `--idat`, `--java` or `--jar`. If a flag is omitted,
the command looks for the tool on `PATH` and fails with a clear message when it is
missing.

### The xref tool

`tools/xref` contains the source of the xref command-line tool used by
`xref-method` and `xref-serve`. Build it with Maven (JDK 11 or later):

```bash
mvn -f tools/xref/pom.xml package
export MRAT_XREF_JAR="$PWD/tools/xref/target/jadx-xrefs-cli.jar"
```

The build pins jadx 1.5.3. Lazy loading is the default for speed; set
`XREF_FULL_INDEX=1` to decompile every class first, which is slower and gives the
most complete index. `inspect-class` always uses the full index.

## Evidence and limits

- Static results are candidates until other evidence supports them. The
  [workflow guide](docs/guides/workflow.zh-CN.md) describes evidence grades
  (`confirmed_static`, `candidate`, `contradicted`).
- Generated Java probes record arguments and return values as text previews.
  Logging failures do not change the original method's result, but
  instrumentation can still change timing and behavior.
- Native probes were exercised against a source-built synthetic fixture. Android
  devices have not been tested.
- The static chain has been run once on a public CTF training APK. See
  [verification](docs/reference/verification.md) for exactly what ran.

## Design principles

- Explicit inputs: devices, processes, tool paths and output files are always named.
- No silent side effects: the toolkit does not install daemons, change ADB
  forwarding, or modify device or system settings.
- Output is never overwritten by default.
- Every result states its limits.
- Contributions stay target-agnostic and use synthetic fixtures; see
  [CONTRIBUTING.md](CONTRIBUTING.md).

## Repository layout

```text
src/mrat/
  cli.py          command-line entry point
  core/           models and offline utilities: hashing, search, JSONL checks
  static/         DEX location, decompilation, xrefs, IDA runs, binary diff
  runtime/        probe generators and the Frida runner
tools/xref/       source of the xref tool (Maven)
docs/guides/      how-to guides: workflow, runtime, setup
docs/reference/   status, architecture, roadmap, verification, release checklist
examples/         synthetic fixtures only
scripts/          real-provider verification scripts
tests/            unit and synthetic tests
```

## Status

See [docs/reference/status.md](docs/reference/status.md) for what is implemented,
what has been verified only with stubs or synthetic data, and what is not built.
Java runtime discovery and native build-identity verification are not implemented.

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Node.js is optional; without it the synthetic JavaScript test is skipped. Passing
Python tests does not establish device compatibility.

## Scope

Use this toolkit only on software you own or are authorized to assess. The
project does not include certificate bypasses, kernel probes, flashing packages,
company tooling, RPC servers or target-specific algorithms.

## Documentation

- [Workflow (中文)](docs/guides/workflow.zh-CN.md): the static analysis path step by step.
- [Runtime](docs/guides/runtime.md): capture, native probes, cleanup and limits.
- [Setup](docs/guides/setup.md): installation, exit codes and manual script execution.
- [Status](docs/reference/status.md), [architecture](docs/reference/architecture.md), [roadmap](docs/reference/roadmap.md).

## License

Copyright 2026 Meb1us (GitHub: ByMi1st). Licensed under [Apache-2.0](LICENSE).
