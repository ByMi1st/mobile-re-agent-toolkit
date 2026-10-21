# Runtime tools

Install optional bindings using `python -m pip install '.[runtime]'`.
No daemon, bridge, ADB forwarding or device configuration is installed automatically.

## Generate and capture

```bash
mrat generate-native-hook --module libexample.so --symbol example_add \
  --arg-count 3 --buffer-arg 2 --buffer-size 4 --max-calls 100 \
  --out /tmp/native-probe.js
mrat run --device-id SERIAL --pid PID --script /tmp/native-probe.js \
  --duration 10 --require-ready --out /tmp/unique-capture.jsonl
```

Replace SERIAL and PID. Transport must be exactly one of `--local`,
`--device-id ID`, or `--remote HOST:PORT`. Target must be `--pid PID` or
`--spawn EXECUTABLE_OR_PACKAGE [ARGS...]`. The caller supplies a compatible
Frida runtime and, for Java, a Java bridge.

Spawned targets are terminated at teardown, including setup failure. Existing
attached processes are never killed or resumed. Cleanup errors are recorded,
not hidden. Setup and individual cleanup operations have cancellable deadlines.
SIGINT/SIGTERM request cleanup; abrupt host death cannot guarantee cleanup.
No output overwrite is allowed. `--require-ready` requires an explicit
`probe_ready` event rather than treating script load as proof of installation.

Native probes capture raw general-purpose ABI slots, a raw return and its signed
low-32-bit interpretation. This is not automatic ABI/type reconstruction.
Optional fixed-size memory reads (up to 4096 bytes) preserve binary data and
read errors. Module load observation and selected call limits are explicit.
Address membership/execution permission is checked; module cryptographic build
identity is not verified. Never reuse offsets across builds without checking.

JSONL envelopes preserve script hash, session/PID, host monotonic timestamps,
raw Frida messages, binary Base64/hash/truncation and completion statistics.
Defaults: 10000 messages, 256 KiB JSON/message, 64 KiB retained binary/message.
Producer loss remains unknown. Read the final coverage field even after exit 0.
Arbitrary caller scripts can mutate targets; unload is not rollback.

## Exit codes

`run` exits 0 when the capture window ends normally or the target exits on its
own, 1 when the capture failed, was limited or was cancelled, and 2 for invalid
input, missing dependencies or file errors. Offline commands exit 0 on success,
1 when invalid JSONL records are found, and 2 for invalid arguments or unreadable
files. Read the final `coverage` field, not only the exit code.

## Real fixture

```bash
PYTHONPATH=src python examples/native/verify_real.py
```

On Linux/macOS with a C compiler and working Frida, this compiles only the
synthetic C fixture. It checks spawn, attach preservation, script errors,
entry/return values, NUL/non-UTF8 binary snapshots, independent fixture output
and owned-spawn cleanup. No phone is accessed. Failures are not replaced by mocks.
See [verification](verification.md) and [full Chinese guide](runtime.zh-CN.md).
