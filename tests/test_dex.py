import contextlib
import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from mrat.cli import main
from mrat.dex import class_descriptor, locate_dex, scope_apk


def build_dex(classes=(), extra_strings=()):
    strings = sorted(set(classes) | set(extra_strings))
    position = {s: i for i, s in enumerate(strings)}
    string_off = 0x70
    type_off = string_off + 4 * len(strings)
    class_off = type_off + 4 * len(classes)
    data_off = class_off + 32 * len(classes)
    header = bytearray(0x70)
    header[0:8] = b'dex\n035\0'
    struct.pack_into('<II', header, 0x38, len(strings), string_off)
    struct.pack_into('<II', header, 0x40, len(classes), type_off)
    struct.pack_into('<II', header, 0x60, len(classes), class_off)
    string_ids = bytearray()
    data = bytearray()
    for s in strings:
        raw = s.encode('utf-8')
        string_ids += struct.pack('<I', data_off + len(data))
        data += bytes([len(raw)]) + raw + b'\0'
    types = b''.join(struct.pack('<I', position[c]) for c in classes)
    defs = b''.join(struct.pack('<8I', i, 0, 0, 0, 0, 0, 0, 0) for i in range(len(classes)))
    return bytes(header) + bytes(string_ids) + types + defs + bytes(data)


def write_apk(path, entries):
    with zipfile.ZipFile(path, 'w') as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


class ClassDescriptorTest(unittest.TestCase):
    def test_accepts_dotted_name_and_descriptor(self):
        self.assertEqual(class_descriptor('com.example.App'), 'Lcom/example/App;')
        self.assertEqual(class_descriptor('Lcom/example/App;'), 'Lcom/example/App;')

    def test_rejects_invalid_names(self):
        for bad in ('', 'com example', 'a;b'):
            with self.assertRaises(ValueError):
                class_descriptor(bad)


class LocateDexTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.apk = self.root / 'sample.apk'
        write_apk(self.apk, {
            'classes.dex': build_dex(classes=['Lcom/example/App;'], extra_strings=['hello']),
            'classes2.dex': build_dex(classes=['Lcom/example/Other;'],
                                      extra_strings=['Lcom/example/App;', 'hello world']),
            'assets/nested.dex': build_dex(classes=['Lx/Y;']),
            'res/readme.txt': b'not dex',
        })

    def test_defining_and_referencing_dex(self):
        result = locate_dex(self.apk, class_name='com.example.App')
        by_name = {d['name']: d for d in result['dex']}
        self.assertEqual(set(by_name), {'classes.dex', 'classes2.dex'})
        self.assertTrue(by_name['classes.dex']['defines'])
        self.assertFalse(by_name['classes2.dex']['defines'])
        self.assertTrue(by_name['classes2.dex']['references'])
        self.assertEqual(result['candidates'], ['classes.dex'])
        self.assertEqual(result['query']['class_descriptor'], 'Lcom/example/App;')

    def test_text_search_reports_matches(self):
        result = locate_dex(self.apk, text='hello')
        by_name = {d['name']: d for d in result['dex']}
        self.assertEqual(by_name['classes.dex']['matched_string_count'], 1)
        self.assertEqual(by_name['classes2.dex']['matched_string_samples'], ['hello world'])
        self.assertEqual(result['candidates'], ['classes.dex', 'classes2.dex'])

    def test_requires_exactly_one_query(self):
        with self.assertRaises(ValueError):
            locate_dex(self.apk)
        with self.assertRaises(ValueError):
            locate_dex(self.apk, class_name='a.B', text='x')

    def test_apk_without_root_dex_is_rejected(self):
        apk = self.root / 'nodex.apk'
        write_apk(apk, {'res/readme.txt': b'x'})
        with self.assertRaises(ValueError):
            locate_dex(apk, text='x')

    def test_malformed_dex_is_rejected(self):
        apk = self.root / 'bad.apk'
        write_apk(apk, {'classes.dex': b'junk'})
        with self.assertRaises(ValueError):
            locate_dex(apk, text='x')

    def test_non_zip_input_is_rejected(self):
        bad = self.root / 'bad.bin'
        bad.write_bytes(b'nope')
        with self.assertRaises(ValueError):
            locate_dex(bad, text='x')


class LocateCliTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.apk = Path(directory.name) / 'sample.apk'
        write_apk(self.apk, {'classes.dex': build_dex(classes=['Lcom/example/App;'])})

    def test_cli_prints_json_and_exits_zero(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(['locate-dex', str(self.apk), '--class', 'com.example.App'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())['candidates'], ['classes.dex'])

    def test_cli_query_flags_are_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(['locate-dex', str(self.apk), '--class', 'a.B', '--text', 'x'])


class ScopeApkTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.apk = self.root / 'sample.apk'
        write_apk(self.apk, {
            'AndroidManifest.xml': b'manifest',
            'classes.dex': build_dex(classes=['Lcom/example/App;']),
            'classes2.dex': build_dex(classes=['Lcom/example/Other;']),
            'res/readme.txt': b'resource',
        })

    def test_keeps_selected_dex_and_manifest_only(self):
        out = self.root / 'scoped.apk'
        result = scope_apk(self.apk, out, ['classes2.dex'])
        self.assertEqual(result['included'], ['AndroidManifest.xml', 'classes2.dex'])
        self.assertEqual(result['excluded_entry_count'], 2)
        with zipfile.ZipFile(out) as archive:
            self.assertEqual(sorted(archive.namelist()), ['AndroidManifest.xml', 'classes2.dex'])
            self.assertEqual(archive.read('classes2.dex'), build_dex(classes=['Lcom/example/Other;']))

    def test_refuses_to_overwrite_existing_output(self):
        out = self.root / 'scoped.apk'
        out.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            scope_apk(self.apk, out, ['classes.dex'])
        self.assertEqual(out.read_bytes(), b'keep')

    def test_rejects_unknown_or_non_root_entries(self):
        with self.assertRaises(ValueError):
            scope_apk(self.apk, self.root / 'a.apk', ['classes9.dex'])
        with self.assertRaises(ValueError):
            scope_apk(self.apk, self.root / 'b.apk', ['res/readme.txt'])
        with self.assertRaises(ValueError):
            scope_apk(self.apk, self.root / 'c.apk', [])

    def test_cli_writes_scoped_apk(self):
        out = self.root / 'cli.apk'
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(['scope-apk', str(self.apk), '--dex', 'classes.dex', '--out', str(out)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buffer.getvalue())['included'], ['AndroidManifest.xml', 'classes.dex'])
        self.assertTrue(out.is_file())
