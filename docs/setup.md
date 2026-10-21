# Setup and reproducibility

Python 3.10+ is required. Offline commands use the Python standard library; runtime capture uses the optional Frida dependency.
Installing from source uses setuptools>=69 as a build dependency, so the first
installation may require network access or a prepopulated package cache.

```bash
git clone https://github.com/ByMi1st/mobile-re-agent-toolkit.git
cd mobile-re-agent-toolkit
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
mrat --help
```

To use the checkout without installation:

```bash
PYTHONPATH=src python3 -m mrat.cli --help
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The optional synthetic JavaScript test needs Node.js. CI explicitly installs it.
No Android SDK, IDA, Unicorn, Frida installation or phone is required to generate
source or run the offline commands.

To execute a generated probe manually, provide your own compatible Frida client,
device runtime and Java bridge. Frida versions/package modes differ in Java
bridge availability. This release does not install them, launch a server,
configure ADB or claim a tested Android/Frida version matrix.

## Limits and exit codes

Text search is case-insensitive literal matching. It supports .c, .asm, .java,
.smali, .txt and .md; excludes symlinks; defaults to a 2 MB per-file and 50 MB
aggregate read limit and 30 matching lines. Returned line previews are bounded.
Complete coverage refers only to selected readable text files within that scope.

Offline command outputs are JSON. Hook generation writes JavaScript and prints
the output filename. Offline commands exit 0 on success, 1 when invalid JSONL records are found, and
2 for invalid arguments, unreadable input or output failure. `run` exit codes are
described in runtime.md.
Hashing a file does not validate its provenance; basic event validation does
not establish capture completeness. Runtime effects and exit codes are described in runtime.md.

Use an explicit --out path for probe generation. Existing output files are
replaced. No command uploads data. Paths in JSON results may contain local
filenames: review results before sharing them publicly.

## Optional runtime

Install `python -m pip install ".[runtime]"` and read [runtime.md](runtime.md).
The runner never installs a device server or changes ADB forwarding.
