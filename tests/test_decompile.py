import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from mrat.cli import main
from mrat.static.decompile import decompile_class


def write_stub(directory, record, *, exit_code=0, sleep=0):
    stub = Path(directory) / 'jadx-stub'
    stub.write_text(f"""#!/bin/sh
printf '%s\\n' "$@" > '{record}'
printf 'JADX_CACHE_DIR=%s\\n' "$JADX_CACHE_DIR" >> '{record}'
while [ $# -gt 0 ]; do
  if [ "$1" = "--single-class-output" ]; then printf 'class Stub {{}}\\n' > "$2"; fi
  shift
done
[ {sleep} -gt 0 ] && sleep {sleep}
echo 'synthetic failure' >&2
exit {exit_code}
""", encoding='utf-8')
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    return stub


class DecompileTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.apk = self.root / 'sample.apk'
        with zipfile.ZipFile(self.apk, 'w') as archive:
            archive.writestr('classes.dex', b'placeholder')
        self.record = self.root / 'record.txt'

    def test_success_passes_safe_flags_cache_and_returns_record(self):
        stub = write_stub(self.root, self.record, exit_code=0)
        out = self.root / 'out' / 'App.java'
        result = decompile_class(self.apk, 'com.example.App', out, jadx=str(stub))
        args = self.record.read_text(encoding='utf-8').splitlines()
        self.assertIn('--no-res', args)
        self.assertIn('--show-bad-code', args)
        self.assertEqual(args[args.index('--single-class') + 1], 'com.example.App')
        cache_line = next(line for line in args if line.startswith('JADX_CACHE_DIR='))
        self.assertFalse(Path(cache_line.split('=', 1)[1]).exists())
        self.assertEqual(result['class'], 'com.example.App')
        self.assertEqual(result['output']['size_bytes'], len(b'class Stub {}\n'))
        self.assertTrue(result['limitations'])

    def test_nonzero_exit_reports_stderr(self):
        stub = write_stub(self.root, self.record, exit_code=3)
        with self.assertRaises(RuntimeError) as caught:
            decompile_class(self.apk, 'com.example.App', self.root / 'x.java', jadx=str(stub))
        self.assertIn('exit 3', str(caught.exception))
        self.assertIn('synthetic failure', str(caught.exception))

    def test_timeout_is_reported(self):
        stub = write_stub(self.root, self.record, sleep=5)
        with self.assertRaises(RuntimeError) as caught:
            decompile_class(self.apk, 'com.example.App', self.root / 'x.java', jadx=str(stub), timeout=0.5)
        self.assertIn('timed out', str(caught.exception))

    def test_missing_jadx_is_reported(self):
        with self.assertRaises(RuntimeError):
            decompile_class(self.apk, 'com.example.App', self.root / 'x.java',
                            jadx=str(self.root / 'absent'))

    def test_refuses_existing_output_and_bad_names(self):
        stub = write_stub(self.root, self.record)
        existing = self.root / 'exists.java'
        existing.write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            decompile_class(self.apk, 'com.example.App', existing, jadx=str(stub))
        for bad in ('App', 'com example.App', 'com.example.App;', ''):
            with self.assertRaises(ValueError):
                decompile_class(self.apk, bad, self.root / 'y.java', jadx=str(stub))
        self.assertEqual(existing.read_text(encoding='utf-8'), 'keep')

    def test_cli_reports_failure_as_json(self):
        stub = write_stub(self.root, self.record, exit_code=4)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(['decompile-class', str(self.apk), 'com.example.App',
                         '--out', str(self.root / 'cli.java'), '--jadx', str(stub)])
        self.assertEqual(code, 2)
        self.assertIn('exit 4', json.loads(buffer.getvalue())['error'])


@unittest.skipUnless(os.environ.get('MRAT_TEST_APK') and os.environ.get('MRAT_TEST_CLASS'),
                     'set MRAT_TEST_APK and MRAT_TEST_CLASS to run the real jadx check')
class RealJadxTest(unittest.TestCase):
    def test_real_jadx_produces_source(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'Real.java'
            result = decompile_class(Path(os.environ['MRAT_TEST_APK']), os.environ['MRAT_TEST_CLASS'], out)
            self.assertTrue(out.read_text(encoding='utf-8').strip())
            self.assertEqual(result['output']['size_bytes'], out.stat().st_size)
