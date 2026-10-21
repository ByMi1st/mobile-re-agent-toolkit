# Implementation status

v0.2.0 ships six commands: four offline/source-generation utilities plus
`generate-native-hook` and `run`. It includes binary Frida message persistence,
explicit target/transport selection, finite capture/cleanup, native module load
observation and bounded snapshots. See runtime.md for effects and limitations.

Host tests cover normal and failed setup, ownership-aware cleanup, binary
truncation, event/message limits, cancellation, required readiness, and synthetic
JS native/Java behavior. They do not establish real Frida compatibility.
Real-provider results and failures are recorded separately in verification.md.

IDA/Unicorn migration, private JAR redistribution, system tracing, interception
bypasses, RPC, automatic bridge installation, whole-process tracing and target
algorithms remain outside scope. Java runtime discovery is not implemented.
