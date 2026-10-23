"""Locate DEX entries in an APK that define or mention a class or string."""
from __future__ import annotations

import re
import struct
import zipfile
from contextlib import contextmanager
from pathlib import Path

from ..core.offline import fingerprint

ROOT_DEX = re.compile(r'classes\d*\.dex')
HEADER_SIZE = 0x70


def class_descriptor(name: str) -> str:
    if name.startswith('L') and name.endswith(';') and len(name) > 2:
        return name
    if not name or any(c in name for c in ' ;[/') or name.startswith('.') or name.endswith('.'):
        raise ValueError(f'invalid class name: {name!r}')
    return 'L' + name.replace('.', '/') + ';'


def _skip_uleb128(data: bytes, pos: int) -> int:
    for _ in range(5):
        if pos >= len(data):
            break
        byte = data[pos]
        pos += 1
        if not byte & 0x80:
            return pos
    raise ValueError('invalid string length')


def parse_dex(data: bytes) -> dict:
    if len(data) < HEADER_SIZE or data[:4] != b'dex\n' or data[7:8] != b'\0':
        raise ValueError('not a DEX file')
    try:
        string_count, string_off = struct.unpack_from('<II', data, 0x38)
        type_count, type_off = struct.unpack_from('<II', data, 0x40)
        class_count, class_off = struct.unpack_from('<II', data, 0x60)
        strings = []
        for index in range(string_count):
            (offset,) = struct.unpack_from('<I', data, string_off + 4 * index)
            start = _skip_uleb128(data, offset)
            end = data.index(b'\0', start)
            strings.append(data[start:end].decode('utf-8', errors='replace'))
        types = struct.unpack_from(f'<{type_count}I', data, type_off)
        defined = []
        for index in range(class_count):
            (class_idx,) = struct.unpack_from('<I', data, class_off + 32 * index)
            defined.append(strings[types[class_idx]])
    except (struct.error, IndexError, ValueError) as error:
        raise ValueError(f'malformed DEX: {error}') from error
    return {'strings': set(strings), 'defined': set(defined)}


@contextmanager
def _open_apk(path: Path):
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as error:
        raise ValueError(f'not a valid APK: {error}') from error
    with archive:
        yield archive


def _root_dex_names(archive: zipfile.ZipFile) -> list[str]:
    names = [info.filename for info in archive.infolist() if ROOT_DEX.fullmatch(info.filename)]
    if not names:
        raise ValueError('APK has no root classes*.dex entries')
    return names


def locate_dex(apk: Path, *, class_name: str | None = None, text: str | None = None,
               sample_limit: int = 20) -> dict:
    if (class_name is None) == (text is None):
        raise ValueError('select exactly one of class_name or text')
    if text is not None and not text:
        raise ValueError('text must not be empty')
    descriptor = class_descriptor(class_name) if class_name is not None else None
    results = []
    with _open_apk(apk) as archive:
        all_dex = [i.filename for i in archive.infolist() if i.filename.endswith('.dex')]
        skipped = [{'name': n, 'reason': 'not a root classes*.dex entry'}
                   for n in all_dex if not ROOT_DEX.fullmatch(n)]
        for name in _root_dex_names(archive):
            parsed = parse_dex(archive.read(name))
            entry = {'name': name, 'size': archive.getinfo(name).file_size}
            if descriptor is not None:
                entry['defines'] = descriptor in parsed['defined']
                entry['references'] = descriptor in parsed['strings']
            else:
                matches = sorted(s for s in parsed['strings'] if text in s)
                entry['matched_string_count'] = len(matches)
                entry['matched_string_samples'] = [m[:200] for m in matches[:sample_limit]]
            results.append(entry)
    return {
        'schema_version': 1,
        'operation': 'locate_dex',
        'source': fingerprint(apk),
        'query': {'class_descriptor': descriptor, 'text': text},
        'dex': results,
        'candidates': [r['name'] for r in results
                       if r.get('defines') or r.get('matched_string_count')],
        'inspected_dex': [r['name'] for r in results],
        'skipped_dex': skipped,
        'coverage': 'partial' if skipped else 'complete',
        'limitations': [
            'only root classes*.dex entries are inspected',
            'text matches are substring matches in the DEX string table, not code references',
            'references means the descriptor string appears in the DEX, not a call graph',
        ],
    }


def scope_apk(apk: Path, out: Path, dex_names: list[str]) -> dict:
    if not dex_names:
        raise ValueError('select at least one DEX entry')
    with _open_apk(apk) as source:
        available = {info.filename for info in source.infolist()}
        root = set(_root_dex_names(source))
        missing = [name for name in dex_names if name not in root]
        if missing:
            raise ValueError(f'not root DEX entries in APK: {missing}')
        keep = list(dict.fromkeys(dex_names))
        if 'AndroidManifest.xml' in available:
            keep.insert(0, 'AndroidManifest.xml')
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('xb') as handle, zipfile.ZipFile(handle, 'w', zipfile.ZIP_DEFLATED) as target:
            for name in keep:
                target.writestr(name, source.read(name))
        excluded = len(available) - len(keep)
    return {
        'schema_version': 1,
        'operation': 'scope_apk',
        'source': fingerprint(apk),
        'output': fingerprint(out),
        'included': keep,
        'excluded_entry_count': excluded,
        'limitations': [
            'scoped APK keeps selected DEX files and AndroidManifest.xml only',
            'resources, native libraries and signatures are excluded; not installable',
            'a scoped APK narrows analysis input; it does not prove absence of references elsewhere',
        ],
    }
