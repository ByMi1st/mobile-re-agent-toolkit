import contextlib
import io
import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from mrat.cli import main
from mrat.xref import xref_method


def write_java_stub(directory, record, *, exit_code=0, sleep=0):
    stub = Path(directory) / 'java-stub'
    stub.write_text(f"""#!/bin/sh
printf '%s\\n' "$@" > '{record}'
printf 'XDG_CACHE_HOME=%s\\n' "$XDG_CACHE_HOME" >> '{record}'
[ {sleep} -gt 0 ] && sleep {sleep}
if [ {exit_code} -ne 0 ]; then echo 'synthetic xref failure' >&2; exit {exit_code}; fi
echo 'com.example.Caller.run -> com.example.App.target'
exit 0
""", encoding='utf-8')
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    return stub


class XrefMethodTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.apk = self.root / 'sample.apk'
        with zipfile.ZipFile(self.apk, 'w') as archive:
            archive.writestr('classes.dex', b'placeholder')
        self.jar = self.root / 'xref.jar'
        self.jar.write_bytes(b'not a real jar; the stub executable never reads it')
        self.record = self.root / 'record.txt'

    def test_passes_arguments_and_records_output(self):
        stub = write_java_stub(self.root, self.record)
        out = self.root / 'xref.txt'
        result = xref_method(self.apk, 'com.example.App', 'target', out, jar=self.jar, java=str(stub))
        args = self.record.read_text(encoding='utf-8').splitlines()
        self.assertEqual(args[:9], ['-Xmx4g', '-jar', str(self.jar), 'xrefs-to-method', '-d',
                                    str(self.apk), '-c', 'com.example.App', '-m'])
        self.assertEqual(args[9], 'target')
        cache_line = next(line for line in args if line.startswith('XDG_CACHE_HOME='))
        self.assertFalse(Path(cache_line.split('=', 1)[1]).exists())
        self.assertIn('com.example.Caller', out.read_text(encoding='utf-8'))
        self.assertEqual(result['target'], {'class': 'com.example.App', 'method': 'target'})
        self.assertTrue(result['limitations'])

    def test_nonzero_exit_reports_stderr(self):
        stub = write_java_stub(self.root, self.record, exit_code=5)
        with self.assertRaises(RuntimeError) as caught:
            xref_method(self.apk, 'com.example.App', 'target', self.root / 'x.txt', jar=self.jar, java=str(stub))
        self.assertIn('exit 5', str(caught.exception))
        self.assertIn('synthetic xref failure', str(caught.exception))

    def test_timeout_is_reported(self):
        stub = write_java_stub(self.root, self.record, sleep=5)
        with self.assertRaises(RuntimeError) as caught:
            xref_method(self.apk, 'com.example.App', 'target', self.root / 'x.txt', jar=self.jar,
                        java=str(stub), timeout=0.5)
        self.assertIn('timed out', str(caught.exception))

    def test_missing_jar_and_java_are_reported(self):
        with self.assertRaises(RuntimeError):
            xref_method(self.apk, 'com.example.App', 'target', self.root / 'x.txt',
                        jar=self.root / 'absent.jar')
        with self.assertRaises(RuntimeError):
            xref_method(self.apk, 'com.example.App', 'target', self.root / 'x.txt', jar=self.jar,
                        java=str(self.root / 'absent-java'))

    def test_validates_inputs_and_refuses_overwrite(self):
        stub = write_java_stub(self.root, self.record)
        with self.assertRaises(ValueError):
            xref_method(self.apk, 'App', 'target', self.root / 'x.txt', jar=self.jar, java=str(stub))
        with self.assertRaises(ValueError):
            xref_method(self.apk, 'com.example.App', 'bad name', self.root / 'x.txt', jar=self.jar, java=str(stub))
        with self.assertRaises(ValueError):
            xref_method(self.apk, 'com.example.App', 'target', self.root / 'x.txt', jar=self.jar,
                        java=str(stub), heap='lots')
        existing = self.root / 'exists.txt'
        existing.write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            xref_method(self.apk, 'com.example.App', 'target', existing, jar=self.jar, java=str(stub))
        self.assertEqual(existing.read_text(encoding='utf-8'), 'keep')

    def test_cli_reports_failure_as_json(self):
        stub = write_java_stub(self.root, self.record, exit_code=6)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(['xref-method', str(self.apk), 'com.example.App', 'target',
                         '--jar', str(self.jar), '--out', str(self.root / 'cli.txt'), '--java', str(stub)])
        self.assertEqual(code, 2)
        self.assertIn('exit 6', json.loads(buffer.getvalue())['error'])


if __name__ == '__main__':
    unittest.main()
