# Verification record

## Host tests

2026-10-21: 22 unit/synthetic-JavaScript tests passed locally. These cover
runner lifecycle and failure paths with fakes, plus Java/native generated code
executed under a JavaScript harness. They do not prove real-provider behavior.

## Real-provider lanes

- Linux x64: CI runs the real native fixture with Frida 17.24.3. Check the
  native-integration job on the published commit for the actual outcome.
- macOS arm64: the existing Frida 16.7.19 environment failed to attach to the
  source-built local fixture within an 15-second deadline. Frida kill also
  timed out. Both failures were retained in JSONL; the exact owned fixture was
  subsequently terminated separately. Do not claim this version is supported.
- macOS arm64 with isolated Frida 17: investigation pending; not a passing result.
- Android and Windows: not tested; no compatibility claim.

The fixture compares independent C output against selected entry/return and
NUL/non-UTF8 binary snapshots. It also checks attach preservation, script-error
handling and termination of runner-owned spawns. This is not full API, ABI or
whole-program coverage. Public CI output contains synthetic data only.

## Static chain on a real sample

2026-10-21: the static chain ran on a local CTF training APK (`unlockme00.apk`,
SHA-256 `28373ebf…3e56` , 179,330 bytes, one `classes.dex`). Steps: `locate-dex`
found `com.ctf.unlockme.Utils` in `classes.dex`; `scope-apk` wrote a 39,648-byte
analysis APK; `decompile-class` (jadx 1.5.3 CLI) produced `Utils.java`;
`xref-method` on `Utils.check` with an operator-owned xref jar reported one caller,
`MainActivity$2.onClick`. Decompiling `MainActivity` independently shows the call
inside `onClick`. The sample's control flow is flattened, so decompiled code needs
manual review. Outputs stayed in a scratch directory and are not part of the repository.
