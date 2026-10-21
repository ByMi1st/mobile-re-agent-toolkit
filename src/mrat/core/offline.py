"""Local, bounded artifact operations. No target execution or uploads."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from pathlib import Path


def fingerprint(path: Path) -> dict:
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
    return {'name': path.name, 'size_bytes': size, 'sha256': digest.hexdigest()}


def search_exports(root: Path, query: str, limit: int = 30,
                   max_file_bytes: int = 2_000_000, max_scan_bytes: int = 50_000_000) -> dict:
    if not root.is_dir() or not query or limit < 1:
        raise ValueError('require directory, nonempty query and positive limit')
    matches, skipped = [], []
    scanned = examined = 0
    stopped = None
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in {'.c','.asm','.java','.smali','.txt','.md'}:
            continue
        size = path.stat().st_size
        relative = str(path.relative_to(root))
        if size > max_file_bytes:
            skipped.append({'path': relative, 'reason': 'file_byte_limit'})
            continue
        if scanned + size > max_scan_bytes:
            stopped = 'scan_byte_limit'
            break
        raw = path.read_bytes()
        scanned += len(raw)
        examined += 1
        for number, line in enumerate(raw.decode('utf-8', errors='replace').splitlines(), 1):
            if query.casefold() in line.casefold():
                matches.append({'path': relative, 'line': number, 'text': line[:1200],
                                'text_truncated': len(line) > 1200})
                if len(matches) >= limit:
                    stopped = 'match_limit'
                    break
        if stopped:
            break
    return {'schema_version': 1, 'operation': 'search_exports', 'query': query,
            'matches': matches, 'files_examined': examined, 'bytes_examined': scanned,
            'skipped': skipped, 'stopped_reason': stopped,
            'coverage': 'partial' if stopped or skipped else 'complete',
            'limitations': ['text matches are not semantic references or runtime calls',
                            'symlinks and unsupported extensions are excluded']}


def summarize_events(path: Path) -> dict:
    counts = Counter()
    errors = []
    total = 0
    with path.open(encoding='utf-8') as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            total += 1
            try:
                event = json.loads(line)
                if not isinstance(event, dict) or event.get('schema_version') != 1 or not isinstance(event.get('event'), str):
                    raise ValueError('expected schema_version=1 and string event')
                counts[event['event']] += 1
            except (ValueError, TypeError) as error:
                errors.append({'line': number, 'error': str(error)})
    return {'schema_version': 1, 'operation': 'summarize_events',
            'source': fingerprint(path), 'records': total,
            'event_counts': dict(sorted(counts.items())), 'invalid_records': errors,
            'valid': not errors,
            'limitations': ['valid JSONL does not establish truthful observations or capture completeness']}
