# Roadmap

## Milestone 1: contracts and generation

- [x] Public scope and safety boundaries
- [x] Java method specification
- [x] Structured Java Hook generator
- [x] Deterministic unit tests
- [ ] JSON Schema for runtime events

## Milestone 2: runtime discovery

- [ ] Enumerate loaded classes and class loaders
- [ ] Search methods and overloads by keyword
- [ ] Locate live objects without retaining them indefinitely
- [ ] Emit structured discovery results

## Milestone 3: lifecycle runner

- [x] Explicit serial/package/process selection (serial or remote endpoint plus PID or spawn; package is a spawn argument)
- [x] Attach and suspended-spawn modes
- [x] JSONL message collection and timeout handling
- [ ] Detach, port-forward and temporary-file cleanup

## Milestone 4: native observation

- [ ] Module/export/address resolution with build identity checks (address and permission checks only; build hash not verified)
- [ ] Typed argument and return capture
- [x] Backtrace and bounded memory snapshots

## Milestone 5: controlled invocation

- [ ] Method allowlist and typed argument schema
- [ ] Loopback-only transport through ADB forwarding
- [ ] Random per-session token
- [ ] Rate limit, audit log and automatic shutdown

## Milestone 6: Agent integration

- [ ] Stable CLI JSON output
- [ ] Tool manifests for Agent runtimes
- [ ] Evidence correlation with scene/request IDs
- [ ] Evaluation corpus made only from synthetic and authorized samples


## 2026-10-21 scope correction

Development is terminal-first. Local export search, artifact fingerprinting and
JSONL summaries are implemented. Generic static-provider wrappers will be added
only after demonstrating a gap in existing CLI tools. See `status.md`; unchecked
items above are plans, not working capabilities.
