"""Compare two binaries by hash and, for ELF files, by section hash and size."""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from .offline import fingerprint

SHT_NOBITS = 8


def parse_elf_sections(data: bytes) -> list[dict]:
    if data[:4] != b'\x7fELF' or len(data) < 0x34:
        raise ValueError('not an ELF file')
    endian = '<' if data[5] == 1 else '>'
    try:
        if data[4] == 2:
            shoff, = struct.unpack_from(endian + 'Q', data, 0x28)
            shentsize, shnum, shstrndx = struct.unpack_from(endian + 'HHH', data, 0x3A)
            fmt = endian + 'IIQQQQIIQQ'
        elif data[4] == 1:
            shoff, = struct.unpack_from(endian + 'I', data, 0x20)
            shentsize, shnum, shstrndx = struct.unpack_from(endian + 'HHH', data, 0x2E)
            fmt = endian + 'IIIIIIIIII'
        else:
            raise ValueError('unknown ELF class')
        headers = []
        for index in range(shnum):
            fields = struct.unpack_from(fmt, data, shoff + index * shentsize)
            name, kind, _flags, _addr, offset, size = fields[:6]
            headers.append((name, kind, offset, size))
        _, _, strtab_off, strtab_size = headers[shstrndx]
        strtab = data[strtab_off:strtab_off + strtab_size]
    except (struct.error, IndexError) as error:
        raise ValueError(f'malformed ELF: {error}') from error
    sections = []
    for name, kind, offset, size in headers:
        end = strtab.find(b'\0', name)
        label = strtab[name:end].decode('utf-8', errors='replace') if end >= 0 and name < len(strtab) else ''
        if kind == SHT_NOBITS:
            digest = None
        else:
            if offset + size > len(data):
                raise ValueError(f'section {label or name} exceeds file size')
            digest = hashlib.sha256(data[offset:offset + size]).hexdigest()
        sections.append({'name': label, 'type': kind, 'size': size, 'sha256': digest})
    return sections


def diff_binary(old: Path, new: Path) -> dict:
    old_data = old.read_bytes()
    new_data = new.read_bytes()
    result = {
        'schema_version': 1,
        'operation': 'diff_binary',
        'old': fingerprint(old),
        'new': fingerprint(new),
        'identical': hashlib.sha256(old_data).digest() == hashlib.sha256(new_data).digest(),
        'format': 'elf' if old_data[:4] == b'\x7fELF' and new_data[:4] == b'\x7fELF' else 'unknown',
        'limitations': [
            'structural comparison only; a changed section does not explain what changed in behavior',
            'stripped names, relocated sections and compiler differences can create changes without logic changes',
            'only ELF section tables are parsed; other formats are reported by whole-file hash only',
        ],
    }
    if result['format'] != 'elf':
        result['sections'] = None
        return result
    old_sections = {s['name']: s for s in parse_elf_sections(old_data)}
    new_sections = {s['name']: s for s in parse_elf_sections(new_data)}
    rows = []
    for name in sorted(set(old_sections) | set(new_sections)):
        before, after = old_sections.get(name), new_sections.get(name)
        if before is None:
            status = 'added'
        elif after is None:
            status = 'removed'
        elif before['sha256'] == after['sha256'] and before['size'] == after['size']:
            status = 'same'
        else:
            status = 'changed'
        rows.append({'name': name, 'status': status,
                     'old_size': before and before['size'], 'new_size': after and after['size']})
    counts = {}
    for row in rows:
        counts[row['status']] = counts.get(row['status'], 0) + 1
    result['sections'] = rows
    result['section_counts'] = dict(sorted(counts.items()))
    return result
