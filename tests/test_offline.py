import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from mrat.offline import fingerprint, search_exports, summarize_events

class OfflineTest(unittest.TestCase):
    def test_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'sample.bin'
            p.write_bytes(b'abc')
            self.assertEqual(fingerprint(p)['sha256'], hashlib.sha256(b'abc').hexdigest())
            self.assertEqual(fingerprint(p)['size_bytes'], 3)

    def test_search_and_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '0x100.c').write_text('first\nmemcpy(a,b,n);\nmemcpy(c,d,n);')
            result = search_exports(root, 'MEMCPY', limit=1)
            self.assertEqual(result['matches'][0]['line'], 2)
            self.assertEqual(result['coverage'], 'partial')
            self.assertEqual(result['stopped_reason'], 'match_limit')
            self.assertEqual(search_exports(root, 'absent')['coverage'], 'complete')
            self.assertEqual(search_exports(root, 'x', max_file_bytes=1)['coverage'], 'partial')
            self.assertEqual(search_exports(root, 'x', max_scan_bytes=1)['coverage'], 'partial')

    def test_invalid_query(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                search_exports(Path(directory), '', 1)

    def test_jsonl_summary_and_error(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'events.jsonl'
            p.write_text(json.dumps({'schema_version':1,'event':'probe_ready'})+'\n')
            self.assertTrue(summarize_events(p)['valid'])
            p.write_text(p.read_text()+'invalid\n')
            result = summarize_events(p)
            self.assertFalse(result['valid'])
            self.assertEqual(result['invalid_records'][0]['line'], 2)


class CliErrorsTest(unittest.TestCase):
    def test_cli_invalid_file_and_invalid_method(self):
        import contextlib
        import io
        from mrat.cli import main
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['fingerprint', '/nonexistent/mrat-test']), 2)
        self.assertIn('error', json.loads(output.getvalue()))
        with tempfile.TemporaryDirectory() as directory:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['generate-java-hook', '--class', 'Bad',
                    '--method', 'run', '--out', str(Path(directory)/'probe.js')]), 2)
