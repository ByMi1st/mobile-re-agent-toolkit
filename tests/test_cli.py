import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from mrat.cli import main


def run_main(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(argv)
    return code, out.getvalue()


class CliTestBase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.script = self.root / 'probe.js'
        self.script.write_text('send(1)')
        self.out = self.root / 'events.jsonl'


class CliRunTest(CliTestBase):
    def run_argv(self, *extra):
        return ['run', '--local', '--pid', '7', '--script', str(self.script),
                '--out', str(self.out), *extra]

    def test_success_exits_zero_and_prints_summary(self):
        with mock.patch('mrat.cli.capture', return_value={'success': True, 'stop_reason': 'duration'}) as capture:
            code, text = run_main(self.run_argv())
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(text)['stop_reason'], 'duration')
        self.assertEqual(capture.call_args.args[0].pid, 7)

    def test_unsuccessful_capture_exits_one(self):
        with mock.patch('mrat.cli.capture', return_value={'success': False, 'stop_reason': 'script_error'}):
            code, _ = run_main(self.run_argv())
        self.assertEqual(code, 1)

    def test_transport_and_target_are_exclusive(self):
        with mock.patch('mrat.cli.capture') as capture, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(['run', '--local', '--device-id', 'X', '--pid', '7',
                      '--script', str(self.script), '--out', str(self.out)])
        capture.assert_not_called()

    def test_invalid_spec_is_json_error_with_exit_two(self):
        with mock.patch('mrat.cli.capture') as capture:
            code, text = run_main(self.run_argv('--duration', '0'))
        self.assertEqual(code, 2)
        self.assertIn('duration', json.loads(text)['error'])
        capture.assert_not_called()


class CliNativeTest(CliTestBase):
    def test_symbol_probe_is_written(self):
        out = self.root / 'native.js'
        code, _ = run_main(['generate-native-hook', '--module', 'libx.so', '--symbol', 'f', '--out', str(out)])
        self.assertEqual(code, 0)
        self.assertIn('native_enter', out.read_text(encoding='utf-8'))

    def test_offset_accepts_hex(self):
        out = self.root / 'native.js'
        code, _ = run_main(['generate-native-hook', '--module', 'libx.so', '--offset', '0x10', '--out', str(out)])
        self.assertEqual(code, 0)
        self.assertIn('"offset": 16', out.read_text(encoding='utf-8'))

    def test_invalid_offset_is_json_error_with_exit_two(self):
        code, text = run_main(['generate-native-hook', '--module', 'libx.so', '--offset', 'zz',
                               '--out', str(self.root / 'native.js')])
        self.assertEqual(code, 2)
        self.assertIn('error', json.loads(text))

    def test_symbol_and_offset_are_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(['generate-native-hook', '--module', 'libx.so', '--symbol', 'f', '--offset', '0x1',
                      '--out', str(self.root / 'native.js')])

    def test_buffer_size_requires_buffer_arg(self):
        code, text = run_main(['generate-native-hook', '--module', 'libx.so', '--symbol', 'f',
                               '--buffer-size', '4', '--out', str(self.root / 'native.js')])
        self.assertEqual(code, 2)
        self.assertIn('buffer_arg', json.loads(text)['error'])


class CliDoctorTest(unittest.TestCase):
    def test_version_flag(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), self.assertRaises(SystemExit) as caught:
            main(['--version'])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn('mrat', buffer.getvalue())

    def test_doctor_reports_each_tool(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(['doctor'])
        self.assertEqual(code, 0)
        report = json.loads(buffer.getvalue())
        names = {tool['name'] for tool in report['tools']}
        self.assertEqual(names, {'jadx', 'java', 'idat', 'xref_jar', 'frida_python'})
        self.assertEqual(report['operation'], 'doctor')


if __name__ == '__main__':
    unittest.main()
