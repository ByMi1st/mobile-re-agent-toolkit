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

## Rebuilt xref tool

2026-10-21: the xref source in `tools/xref` was built with Maven (jadx 1.5.1 pinned).
On the same scoped APK, the rebuilt jar and the original jar produced identical
stdout and exit codes for `xrefs-to-method`, `xrefs-to-class`, `search-classes` and
`inspect-class`. The `-d` argument accepts an APK file, as the recovered source
shows (`JadxLoader.findInputFile`).

## Xref tool performance

2026-10-21, 10-core macOS. Times are wall-clock for one `xrefs-to-class` query.

| APK | Original jar (full preload) | Lazy (default) | Full (`XREF_FULL_INDEX=1`) |
|---|---|---|---|
| drillbeam.apk, 10 MB | 7.6 s | 1.7 s | 8.0 s |
| xiaoyuankousuan.apk, 88 MB | 56.7 s | 6.7 s | not measured |

Output was byte-identical between the original and lazy modes on three queries.
The lazy mode is not proven complete in general, so use `XREF_FULL_INDEX=1` when a
missing caller would matter.

## Xref server mode

2026-10-21. `mrat xref-serve` loads the APK once and answers JSON requests line by
line. On drillbeam.apk, three `xrefs-to-class` queries took 1.74 s in one process,
against 5.12 s for three separate runs. Responses matched the one-shot output.

Pinning jadx to 1.5.1 gave different decompiled text from the original jar, which
bundles 1.5.3. The pin is now 1.5.3. After that, all four subcommands matched the
original jar byte for byte in both lazy and full modes, except `inspect-class`, which
now always uses the full index because lazy loading changed its method list. The
test suite covers the server with a stub process.

