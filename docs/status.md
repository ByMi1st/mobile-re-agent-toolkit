# v0.1.0 status

The release scope is exactly four commands: fingerprint, search-exports,
summarize-events and generate-java-hook. They have local unit tests and synthetic
fixtures. Installation and CLI examples are checked in an isolated environment.

A basic JSONL check is not a comprehensive runtime-event schema validator.
Text search is not semantic xref. A generated probe is not a running session.
Synthetic JavaScript tests are not real Android compatibility tests.

## Future, not shipped

- Generic Frida runner: explicit device/process selection, attach/spawn,
  message/binary transport, timeouts and cleanup.
- Native probe generator: selected module/function and bounded raw observations.

## Outside this repository

IDA/Unicorn integration, private xref JAR redistribution, packer recovery,
application-specific algorithms, interception bypasses, kernel/flash packages,
company tools and production data are excluded. External research projects are
not dependencies or verified integrations.

See release-checklist.md for publication verification. The existence of a CI
configuration or badge alone does not establish a passing remote run.
