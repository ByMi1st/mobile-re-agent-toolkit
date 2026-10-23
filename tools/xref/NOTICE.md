# Provenance and third-party notices for tools/xref

The source under `src/` is the author's own code (package `com.sop.jadxxrefs`).
The original source tree was lost, so these files were reconstructed by
decompiling the author's compiled jar. They were compiled and checked against
that jar's behavior; see docs/reference/verification.md.

The build depends on these third-party libraries, each under its own license:

| Dependency | Version | License |
|---|---|---|
| io.github.skylot:jadx-core | 1.5.3 | Apache-2.0 |
| io.github.skylot:jadx-dex-input | 1.5.3 | Apache-2.0 |
| commons-cli:commons-cli | 1.5.0 | Apache-2.0 |
| com.google.code.gson:gson | 2.10.1 | Apache-2.0 |

Transitive dependencies (for example Google Guava, Smali, and SLF4J) keep their
own licenses. Run `mvn -f tools/xref/pom.xml dependency:list` for the full set.
