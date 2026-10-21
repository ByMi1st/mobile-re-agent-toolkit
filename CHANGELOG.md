# Changelog

## Unreleased

- Added `locate-dex` to find root DEX entries that define or mention a class or string.
- Added `scope-apk` to write an analysis-only APK containing selected root DEX files.
- Added `decompile-class`, a timeout-bounded wrapper around the jadx CLI.
- Added `xref-method`, a wrapper for a user-supplied jadx xref jar; the jar is not bundled.
- Added `ida-run`, a headless IDA batch wrapper that records log and database hashes.

## 0.2.0 — 2026-10-21

- Added explicit-transport Frida runner with bounded messages/binary data.
- Added ownership-aware cleanup, deadlines and readiness checks.
- Added native export/offset probes and source-built real-provider fixture.
- Expanded failure, lifecycle and JavaScript behavior tests.


## 0.1.0 — 2026-10-21 (local, not published)

- Introduced exact-overload Java Hook generation.
- Added local artifact SHA-256, bounded text-export search and JSONL summaries.
- Added synthetic fixtures, workflow documentation and CI configuration.
- Verified Python installation in an isolated virtual environment.
- Added synthetic JS checks for return/exception preservation on logging failure.

No live-device compatibility or remote CI execution is claimed.
