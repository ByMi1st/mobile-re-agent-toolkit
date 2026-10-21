import contextlib
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from mrat.binary_diff import diff_binary, parse_elf_sections
from mrat.cli import main


def build_elf64(sections):
    strtab = bytearray(b'\0')
    name_offsets = []
    for name, _ in sections:
        name_offsets.append(len(strtab))
        strtab += name.encode() + b'\0'
    name_offsets.append(len(strtab))
    strtab += b'.shstrtab\0'
    contents = [data for _, data in sections] + [bytes(strtab)]
    body = b''.join(contents)
    shoff = 64 + len(body)
    table = bytearray(struct.pack('<IIQQQQIIQQ', *([0] * 10)))
    offset = 64
    for name_off, data in zip(name_offsets, contents):
        table += struct.pack('<IIQQQQIIQQ', name_off, 1, 0, 0, offset, len(data), 0, 0, 1, 0)
        offset += len(data)
    header = bytearray(64)
    header[0:4] = b'\x7fELF'
    header[4] = 2
    header[5] = 1
    header[6] = 1
    struct.pack_into('<Q', header, 0x28, shoff)
    struct.pack_into('<HHH', header, 0x3A, 64, len(contents) + 1, len(contents))
    return bytes(header) + body + bytes(table)


class BinaryDiffTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.old = self.root / 'old.so'
        self.old.write_bytes(build_elf64([('.text', b'AAAA'), ('.data', b'BBBB')]))

    def write(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return path

    def test_identical_files(self):
        same = self.write('same.so', self.old.read_bytes())
        result = diff_binary(self.old, same)
        self.assertTrue(result['identical'])
        self.assertEqual({r['status'] for r in result['sections']}, {'same'})

    def test_changed_added_and_removed_sections(self):
        new = self.write('new.so', build_elf64([('.text', b'AAAC'), ('.rodata', b'CCCC')]))
        result = diff_binary(self.old, new)
        self.assertFalse(result['identical'])
        statuses = {r['name']: r['status'] for r in result['sections']}
        self.assertEqual(statuses['.text'], 'changed')
        self.assertEqual(statuses['.data'], 'removed')
        self.assertEqual(statuses['.rodata'], 'added')
        self.assertEqual(statuses['.shstrtab'], 'changed')
        self.assertEqual(result['section_counts']['changed'], 2)

    def test_non_elf_uses_whole_file_hash(self):
        a = self.write('a.bin', b'plain bytes')
        b = self.write('b.bin', b'other bytes')
        result = diff_binary(a, b)
        self.assertEqual(result['format'], 'unknown')
        self.assertIsNone(result['sections'])
        self.assertFalse(result['identical'])

    def test_malformed_elf_is_rejected(self):
        truncated = self.write('bad.so', b'\x7fELF' + b'\0' * 20)
        with self.assertRaises(ValueError):
            parse_elf_sections(truncated.read_bytes())

    def test_section_exceeding_file_is_rejected(self):
        data = bytearray(self.old.read_bytes())
        shoff, = struct.unpack_from('<Q', data, 0x28)
        struct.pack_into('<Q', data, shoff + 2 * 64 + 0x20, len(data) * 4)
        with self.assertRaises(ValueError):
            parse_elf_sections(bytes(data))

    def test_cli_prints_json(self):
        new = self.write('cli.so', build_elf64([('.text', b'AAAA'), ('.data', b'BBBB')]))
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(['diff-binary', str(self.old), str(new)])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(buffer.getvalue())['identical'])


if __name__ == '__main__':
    unittest.main()
