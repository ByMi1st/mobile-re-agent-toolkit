# Release verification

Repository: https://github.com/ByMi1st/mobile-re-agent-toolkit

v0.2.0 includes six CLI commands, optional Frida bindings and a synthetic native
end-to-end fixture. No IDA/Unicorn/private tool migration is planned.

Before calling a release verified, check:

- Unit/synthetic JS tests, isolated install and six CLI command entry points.
- Real native fixture under the claimed host/Frida combination.
- Script errors, setup failure, message limits, binary preservation and cleanup.
- Published tree matches the tested local tree.
- GitHub Actions results for that exact commit, not just workflow presence.
- No private paths, captures, credentials, binaries or build products tracked.

See verification.md for passing/failing/unverified platform distinctions.
