# Repository instructions

This is a terminal-first toolkit, not a new agent or a large MCP server.

- Inspect existing functionality before adding wrappers.
- Keep original artifacts on disk; return bounded snippets with file and line references.
- Do not confuse text search, static references and observed runtime calls.
- Report skipped files, truncation, unsupported operations and failed collection explicitly.
- Build generic tools with synthetic fixtures. Do not import private application artifacts.
- Preserve observed exceptions and return semantics in generated probes.
- Host tests do not establish real Android/Frida compatibility.
- Optional integrations must not install software or change global agent configuration implicitly.
- Use `PYTHONPATH=src python3 -m unittest discover -s tests -v` for local tests.
