"""Run jadx single-class decompilation with explicit paths, timeouts and records."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .offline import fingerprint

CLASS_NAME = re.compile(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+')


def resolve_jadx(explicit: str | None) -> str:
    candidate = explicit or shutil.which('jadx')
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError('jadx CLI not found; install it or pass --jadx PATH')
    return candidate


def decompile_class(apk: Path, class_name: str, out: Path, *, jadx: str | None = None,
                    timeout: float = 300.0) -> dict:
    if not CLASS_NAME.fullmatch(class_name):
        raise ValueError(f'class must be a dotted name: {class_name!r}')
    if not 0 < timeout <= 3600:
        raise ValueError('timeout must be within (0, 3600] seconds')
    if out.exists():
        raise FileExistsError(f'output already exists: {out}')
    executable = resolve_jadx(jadx)
    cache = tempfile.mkdtemp(prefix='mrat-jadx-cache-')
    out.parent.mkdir(parents=True, exist_ok=True)
    command = [executable, '--single-class', class_name, '--single-class-output', str(out),
               '--no-res', '--show-bad-code', str(apk)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                   env=dict(os.environ, JADX_CACHE_DIR=cache))
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f'jadx timed out after {timeout:g} seconds') from error
    finally:
        shutil.rmtree(cache, ignore_errors=True)
    if completed.returncode != 0 or not out.is_file():
        tail = completed.stderr.strip()[-400:]
        raise RuntimeError(f'jadx failed with exit {completed.returncode}: {tail}')
    return {
        'schema_version': 1,
        'operation': 'decompile_class',
        'class': class_name,
        'jadx_path': executable,
        'source': fingerprint(apk),
        'output': fingerprint(out),
        'limitations': [
            'output is decompiler output, not the original source',
            '--show-bad-code keeps incorrectly decompiled code; inspect it before relying on it',
            'resources are not decoded (--no-res)',
        ],
    }
