"""Run an IDA headless batch script (idat) with an explicit database and log."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..core.offline import fingerprint


def resolve_idat(explicit: str | None) -> str:
    candidate = explicit or shutil.which('idat') or shutil.which('idat64')
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError('idat not found; install IDA Pro or pass --idat PATH')
    return candidate


def ida_run(database: Path, script: Path, log: Path, *, idat: str | None = None,
            timeout: float = 1800.0) -> dict:
    if script.suffix != '.py' or not script.is_file():
        raise ValueError('script must be an existing .py file')
    if not database.is_file():
        raise ValueError('database must be an existing IDA database file')
    if not 0 < timeout <= 86400:
        raise ValueError('timeout must be within (0, 86400] seconds')
    if log.exists():
        raise FileExistsError(f'log already exists: {log}')
    executable = resolve_idat(idat)
    before = fingerprint(database)
    log.parent.mkdir(parents=True, exist_ok=True)
    command = [executable, '-A', f'-S{script}', f'-L{log}', str(database)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f'idat timed out after {timeout:g} seconds; partial log: {log}') from error
    if completed.returncode != 0:
        tail = completed.stderr.strip()[-400:]
        raise RuntimeError(f'idat failed with exit {completed.returncode}: {tail}')
    if not log.is_file():
        raise RuntimeError('idat exited without writing the requested log')
    return {
        'schema_version': 1,
        'operation': 'ida_run',
        'idat_path': executable,
        'script': fingerprint(script),
        'database_before': before,
        'database_after': fingerprint(database),
        'log': fingerprint(log),
        'limitations': [
            'the script decides which files it writes; this wrapper records only the log and database hashes',
            'an unchanged database hash does not show the script produced no results',
            'IDA licensing and version compatibility are the operator responsibility',
        ],
    }
