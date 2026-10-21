# Architecture

## Implemented

`mrat.cli` parses commands. `mrat.offline` provides local file hashing, bounded
text search and basic JSONL summaries. `mrat.model` describes a selected Java
method and optional experiment labels. `mrat.java_hook` produces source code;
it never starts Frida or contacts a device.

Artifacts stay on disk. Offline commands print JSON rather than requiring a
resident server or exposing a large tool catalog to an agent. Generated probes
report structured messages through Frida's standard send mechanism.

## Evidence and experiment constraints

- Text matches, static references and runtime observations are different facts.
- A source method or an exported component does not establish runtime execution.
- Scene/request labels are supplied by the analyst, not inferred causality.
- Capture limits, skipped files and invalid records must stay visible.
- Reusing downstream outputs as generator inputs does not prove independent
  reconstruction; compare new inputs against separately obtained reference data.
- Successful HTTP transport does not establish a server's security decision.
- `natural` and `controlled` label experiment intent. Frida itself can change
  timing and memory; neither label guarantees an unmodified process.

## Future runner boundary

A later runner will own explicit target selection, script lifetime, message
persistence and cleanup. It must preserve externally launched targets, record
partial failures, and not silently install daemons or change device settings.
That runner and a later native probe generator are not implemented here.
