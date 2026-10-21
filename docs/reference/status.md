# Implementation status

Unreleased commands (after v0.2.0): `locate-dex`, `scope-apk`, `decompile-class`,
`xref-method`, `ida-run`, `diff-binary`. v0.2.0 shipped `fingerprint`,
`search-exports`, `summarize-events`, `generate-java-hook`, `generate-native-hook`
and `run`.

## Implemented and host-tested

- File SHA-256 and size; ELF section comparison for two binaries.
- Bounded literal search over local text exports.
- Root DEX location by class descriptor or string table; analysis-only APK scoping.
- jadx single-class decompilation wrapper and xref-jar wrapper; both require the
  operator to supply the tool. Tests use stub executables.
- Headless IDA batch wrapper; tests use a stub executable.
- JSONL envelope validation and event counts.
- Exact-overload Java probe generation; generic Frida runner; bounded native
  Interceptor probe generation.

## Verified only with stubs or synthetic data

- jadx and xref: the full static chain ran once on a real CTF training APK
  (see [verification](verification.md)). The test suite still uses stubs; the real
  check runs only when MRAT_TEST_APK and MRAT_TEST_CLASS are set, because the
  synthetic DEX in the tests is rejected by jadx.
- IDA: not available in this environment; `ida-run` has no real-IDA test.
- Frida: real-provider lanes are recorded in [verification](verification.md); Android devices are not tested.

## Not implemented

- Java runtime discovery (classes, class loaders, overloads).
- Native build identity verification.
- Semantic cross-reference adapter for ASC or other tools.
- System tracing, interception bypasses, RPC, automatic bridge installation.

## Outside this repository

Private application analysis scripts, target-specific algorithms, company
tooling, captured traffic and device profiles.
