# Roadmap

## v0.1.0

- File SHA-256 and size.
- Local text-export search with visible limits.
- JSONL envelope summaries.
- Exact-overload Java probe generation.
- Installation instructions, synthetic examples, tests and CI.

## Next: generic Frida Runner

Explicit target selection; attach/spawn/load/resume; text and binary messages;
timeouts, target exit, cancellation and cleanup. Add lifecycle tests first,
then real fixtures. Reuse independently distributable logic where appropriate.

## Later: native probe generation

Module/build identity, exact function selection, bounded argument/return memory
observations and backtraces. Require synthetic and real fixture verification.

No commitment to an agent platform, MCP server, RPC service, decompiler wrappers,
IDA/Unicorn migration or system tracing. Additions require a demonstrated use
case rather than copying all capabilities of a private workspace.
