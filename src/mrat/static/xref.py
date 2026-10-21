"""Run a user-supplied jadx cross-reference jar for one method, with recorded output."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from ..core.offline import fingerprint

CLASS_NAME = re.compile(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+')
METHOD_NAME = re.compile(r'[A-Za-z_$<][\w$<>]*')


def resolve_java(explicit: str | None) -> str:
    candidate = explicit or shutil.which('java')
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError('java runtime not found; install a JDK or pass --java PATH')
    return candidate


def resolve_jar(explicit: Path | None) -> Path:
    candidate = explicit or (Path(os.environ['MRAT_XREF_JAR']) if os.environ.get('MRAT_XREF_JAR') else None)
    if candidate is None or not candidate.is_file():
        raise RuntimeError('xref jar not found; pass --jar PATH or set MRAT_XREF_JAR to a jar you own')
    return candidate


def xref_method(apk: Path, class_name: str, method_name: str, out: Path, *, jar: Path | None = None,
                java: str | None = None, heap: str = '4g', timeout: float = 600.0) -> dict:
    if not CLASS_NAME.fullmatch(class_name):
        raise ValueError(f'class must be a dotted name: {class_name!r}')
    if not METHOD_NAME.fullmatch(method_name):
        raise ValueError(f'invalid method name: {method_name!r}')
    if not re.fullmatch(r'\d+[gGmM]', heap):
        raise ValueError('heap must look like 4g or 512m')
    if not 0 < timeout <= 7200:
        raise ValueError('timeout must be within (0, 7200] seconds')
    jar = resolve_jar(jar)
    if out.exists():
        raise FileExistsError(f'output already exists: {out}')
    executable = resolve_java(java)
    cache = tempfile.mkdtemp(prefix='mrat-xref-cache-')
    command = [executable, f'-Xmx{heap}', '-jar', str(jar), 'xrefs-to-method',
               '-d', str(apk), '-c', class_name, '-m', method_name]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                   env=dict(os.environ, XDG_CACHE_HOME=cache))
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f'xref timed out after {timeout:g} seconds') from error
    finally:
        shutil.rmtree(cache, ignore_errors=True)
    if completed.returncode != 0:
        tail = completed.stderr.strip()[-400:]
        raise RuntimeError(f'xref failed with exit {completed.returncode}: {tail}')
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8') as handle:
        handle.write(completed.stdout)
    return {
        'schema_version': 1,
        'operation': 'xref_method',
        'target': {'class': class_name, 'method': method_name},
        'java_path': executable,
        'jar': fingerprint(Path(jar)),
        'source': fingerprint(apk),
        'output': fingerprint(out),
        'limitations': [
            'results are produced by the external jar; this wrapper does not validate them',
            'a method reference is a static reference found by the jar, not a confirmed runtime call',
            'reflection, dynamic loading and interface dispatch may be missed',
        ],
    }


class XrefServer:
    def __init__(self, apk: Path, *, jar: Path | None = None, java: str | None = None,
                 heap: str = '4g') -> None:
        if not re.fullmatch(r'\d+[gGmM]', heap):
            raise ValueError('heap must look like 4g or 512m')
        self.jar = resolve_jar(jar)
        self.java = resolve_java(java)
        self._stderr = tempfile.TemporaryFile()
        self._cache = tempfile.mkdtemp(prefix='mrat-xref-cache-')
        self._process = subprocess.Popen(
            [self.java, f'-Xmx{heap}', '-jar', str(self.jar), 'serve', '-d', str(apk)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._stderr, text=True,
            encoding='utf-8', env=dict(os.environ, XDG_CACHE_HOME=self._cache))

    def query(self, argv: list[str], timeout: float = 600.0) -> dict:
        if self._process.poll() is not None:
            raise RuntimeError('xref server is not running')
        killer = threading.Timer(timeout, self._process.kill)
        killer.start()
        try:
            self._process.stdin.write(json.dumps({'argv': argv}) + '\n')
            self._process.stdin.flush()
            line = self._process.stdout.readline()
        finally:
            killer.cancel()
        if not line:
            raise RuntimeError(f'xref server stopped; {self._stderr_tail()}')
        return json.loads(line)

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.stdin.close()
            try:
                self._process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
        shutil.rmtree(self._cache, ignore_errors=True)
        self._stderr.close()

    def _stderr_tail(self) -> str:
        self._stderr.seek(0)
        return self._stderr.read().decode('utf-8', errors='replace').strip()[-400:]

    def __enter__(self) -> 'XrefServer':
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
