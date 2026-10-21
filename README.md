# Mobile RE Agent Toolkit

Mobile RE Agent Toolkit (`mrat`) is a small, evidence-oriented toolkit for
authorized Android reverse engineering workflows.

It focuses on the repetitive layer between static findings and dynamic
experiments:

1. confirm that a class or method exists in the live process;
2. generate a consistent runtime probe instead of ad-hoc JavaScript;
3. emit structured events that can be correlated with a scene or request;
4. promote manually verified methods to a narrowly scoped invocation API.

The project does **not** bundle target-specific bypasses, device modifications,
application samples, captured credentials, or unrestricted remote invocation.

## Terminal-first scope

This is a small toolkit, not another agent framework or an always-loaded MCP
catalog. Existing decompilers produce local files; agents inspect bounded
results on demand. See [the practical workflow (中文)](docs/workflow.zh-CN.md).

```bash
PYTHONPATH=src python3 -m mrat.cli fingerprint examples/exports/0x1000.c
PYTHONPATH=src python3 -m mrat.cli search-exports examples/exports memcpy --limit 10
PYTHONPATH=src python3 -m mrat.cli summarize-events examples/events.jsonl
```

See [implementation status](docs/status.md) for what is and is not implemented.

## Current milestone

The first usable slice is a deterministic Java Hook generator. It creates a
Frida script that records:

- schema version and event type;
- invocation ID, timestamp, PID and TID;
- class, method and overload;
- arguments, return value, exception and Java stack;
- optional scene and request correlation IDs.

```bash
PYTHONPATH=src python3 -m mrat.cli generate-java-hook \
  --class 'okhttp3.Request$Builder' \
  --method addHeader \
  --overload java.lang.String java.lang.String \
  --out /tmp/add-header.js
```

Run the tests without installing the package:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

After `python3 -m pip install -e .`, the shorter `mrat ...` command is
available and `PYTHONPATH` is no longer needed.

## Design constraints

- Device serial, package and process must always be explicit.
- No automatic `setenforce 0`, root-module changes, proxy changes or unknown
  Frida deployment.
- Runtime invocation is allowlisted and disabled by default.
- Any future RPC service binds to loopback/ADB forwarding and requires a random
  session token.
- Natural observations and actively modified experiments use different event
  labels.
- Raw artifacts remain local unless the operator explicitly exports them.

See [docs/architecture.md](docs/architecture.md) and
[docs/roadmap.md](docs/roadmap.md).

## Scope and authorization

Use this toolkit only on applications, devices and systems that you own or are
explicitly authorized to assess.


## License

Copyright 2026 Meb1us (GitHub: ByMi1st). Licensed under the
[Apache License 2.0](LICENSE). The license appendix is the unmodified
standard application example, not the project copyright notice.
