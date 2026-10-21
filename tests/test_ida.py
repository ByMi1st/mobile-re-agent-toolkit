import contextlib
import io
import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from mrat.cli import main
from mrat.static.ida import ida_run


def write_idat_stub(directory, record, *, exit_code=0, sleep=0, write_log=True):
    stub = Path(directory) / 'idat-stub'
    log_line = 'echo "stub log line" > "$LOG"' if write_log else ':'
    stub.write_text(f"""#!/bin/sh
printf '%s\\n' "$@" > '{record}'
for arg in "$@"; do case "$arg" in -L*) LOG="${{arg#-L}}";; esac; done
[ {sleep} -gt 0 ] && sleep {sleep}
if [ {exit_code} -ne 0 ]; then echo 'synthetic idat failure' >&2; exit {exit_code}; fi
{log_line}
exit 0
""", encoding='utf-8')
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    return stub


class IdaRunTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.db = self.root / 'sample.i64'
        self.db.write_bytes(b'database bytes')
        self.script = self.root / 'batch.py'
        self.script.write_text('print("batch")\n', encoding='utf-8')
        self.record = self.root / 'record.txt'

    def test_runs_idat_batch_and_records_hashes(self):
        stub = write_idat_stub(self.root, self.record)
        log = self.root / 'logs' / 'run.log'
        result = ida_run(self.db, self.script, log, idat=str(stub))
        args = self.record.read_text(encoding='utf-8').splitlines()
        self.assertEqual(args, ['-A', f'-S{self.script}', f'-L{log}', str(self.db)])
        self.assertEqual(log.read_text(encoding='utf-8').strip(), 'stub log line')
        self.assertEqual(result['database_before']['sha256'], result['database_after']['sha256'])
        self.assertEqual(result['script']['size_bytes'], self.script.stat().st_size)

    def test_nonzero_exit_reports_stderr(self):
        stub = write_idat_stub(self.root, self.record, exit_code=7)
        with self.assertRaises(RuntimeError) as caught:
            ida_run(self.db, self.script, self.root / 'x.log', idat=str(stub))
        self.assertIn('exit 7', str(caught.exception))
        self.assertIn('synthetic idat failure', str(caught.exception))

    def test_missing_log_is_an_error(self):
        stub = write_idat_stub(self.root, self.record, write_log=False)
        with self.assertRaises(RuntimeError):
            ida_run(self.db, self.script, self.root / 'x.log', idat=str(stub))

    def test_timeout_is_reported(self):
        stub = write_idat_stub(self.root, self.record, sleep=5)
        with self.assertRaises(RuntimeError) as caught:
            ida_run(self.db, self.script, self.root / 'x.log', idat=str(stub), timeout=0.5)
        self.assertIn('timed out', str(caught.exception))

    def test_validates_inputs_and_refuses_existing_log(self):
        stub = write_idat_stub(self.root, self.record)
        with self.assertRaises(ValueError):
            ida_run(self.db, self.root / 'batch.txt', self.root / 'x.log', idat=str(stub))
        with self.assertRaises(ValueError):
            ida_run(self.root / 'missing.i64', self.script, self.root / 'x.log', idat=str(stub))
        log = self.root / 'exists.log'
        log.write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            ida_run(self.db, self.script, log, idat=str(stub))
        self.assertEqual(log.read_text(encoding='utf-8'), 'keep')

    def test_missing_idat_is_reported(self):
        with self.assertRaises(RuntimeError):
            ida_run(self.db, self.script, self.root / 'x.log', idat=str(self.root / 'absent'))

    def test_cli_prints_json(self):
        stub = write_idat_stub(self.root, self.record)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(['ida-run', str(self.db), '--script', str(self.script),
                         '--log', str(self.root / 'cli.log'), '--idat', str(stub)])
        self.assertEqual(code, 0)
        self.assertIn('database_after', json.loads(buffer.getvalue()))


if __name__ == '__main__':
    unittest.main()
