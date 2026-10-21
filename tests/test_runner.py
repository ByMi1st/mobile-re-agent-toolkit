import base64
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from mrat.runner import RunSpec, capture
from mrat.native_hook import NativeProbeSpec, generate_native_hook


class Cancel:
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def cancel(self): pass


class FakeScript:
    def __init__(self, api): self.api = api
    def on(self, _, callback): self.callback = callback; self.api.callbacks.append(callback)
    def load(self):
        self.api.calls.append('load')
        if self.api.fail_load: raise RuntimeError('bad script')
        for msg, data in self.api.messages: self.callback(msg, data)
    def unload(self): self.api.calls.append('unload')


class FakeSession:
    def __init__(self, api): self.api = api
    def on(self, _, cb): self.callback = cb
    def create_script(self, source): return FakeScript(self.api)
    def detach(self):
        self.api.calls.append('detach')
        if self.api.fail_detach: raise RuntimeError('detach failed')


class FakeDevice:
    def __init__(self, api): self.api = api
    def spawn(self, argv): self.api.calls.append('spawn'); return 123
    def attach(self, pid):
        self.api.calls.append('attach')
        if self.api.fail_attach: raise RuntimeError('attach denied')
        return FakeSession(self.api)
    def resume(self, pid): self.api.calls.append('resume')
    def kill(self, pid): self.api.calls.append('kill')


class FakeFrida:
    __version__ = 'fake'
    Cancellable = Cancel
    def __init__(self, messages=(), fail_load=False, fail_attach=False, fail_detach=False):
        self.messages = messages
        self.fail_load, self.fail_attach, self.fail_detach = fail_load, fail_attach, fail_detach
        self.calls = []
        self.callbacks = []
    def get_local_device(self): return FakeDevice(self)


class RunnerTest(unittest.TestCase):
    def run_case(self, api, *, spawn=False, stop=False, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory); (p/'probe.js').write_text('send(1)')
            event = threading.Event()
            if stop: event.set()
            spec = RunSpec(script=p/'probe.js', out=p/'events.jsonl', local=True,
                duration=.001, spawn=('fixture',) if spawn else (), pid=None if spawn else 7, **kwargs)
            result = capture(spec, frida_module=api, stop_event=event)
            records = [json.loads(l) for l in (p/'events.jsonl').read_text().splitlines()]
            return result, records

    def test_spawn_order_and_cleanup(self):
        api = FakeFrida()
        result, _ = self.run_case(api, spawn=True)
        self.assertTrue(result['success'])
        self.assertEqual(api.calls, ['spawn','attach','load','resume','unload','detach','kill'])

    def test_attach_does_not_resume_or_kill(self):
        api = FakeFrida()
        self.run_case(api)
        self.assertNotIn('kill', api.calls); self.assertNotIn('resume', api.calls)

    def test_setup_failures_kill_owned_spawn(self):
        for key in ('fail_attach','fail_load'):
            api = FakeFrida(**{key:True})
            result, _ = self.run_case(api, spawn=True)
            self.assertFalse(result['success']); self.assertIn('kill', api.calls)

    def test_script_error_is_visible(self):
        api = FakeFrida(messages=[({'type':'error','description':'syntax'},None)])
        result, records = self.run_case(api, spawn=True)
        self.assertFalse(result['success']); self.assertEqual(result['script_errors'],1)
        self.assertNotIn('resume',api.calls)
        self.assertTrue(any(r['event']=='frida_message' for r in records))

    def test_binary_and_script_identity(self):
        api = FakeFrida(messages=[({'type':'send','payload':{'ok':True}},b'\x00\xff\x01')])
        result, records = self.run_case(api, max_binary_bytes=2)
        self.assertEqual(result['binary_truncations'],1)
        info = next(r['data']['binary'] for r in records if r['event']=='frida_message')
        self.assertEqual(base64.b64decode(info['data']),b'\x00\xff')
        self.assertEqual(info['original_size'],3)
        self.assertEqual(len(records[0]['data']['script_sha256']),64)

    def test_limits_and_cleanup_errors(self):
        api = FakeFrida(messages=[({'type':'send','payload':1},None)]*4)
        result, _ = self.run_case(api, max_events=2)
        self.assertEqual(result['messages'],2); self.assertEqual(result['omitted_messages'],2)
        self.assertEqual(result['stop_reason'],'event_limit'); self.assertFalse(result['success'])
        result, _ = self.run_case(FakeFrida(fail_detach=True))
        self.assertFalse(result['success']); self.assertTrue(result['cleanup_errors'])

    def test_oversize_and_cancellation(self):
        result, _ = self.run_case(FakeFrida(messages=[({'type':'send','payload':'x'*2000},None)]),max_message_bytes=1024)
        self.assertEqual(result['oversized_messages'],1); self.assertFalse(result['success'])
        result, _ = self.run_case(FakeFrida(), spawn=True, stop=True)
        self.assertFalse(result['success'])

    def test_required_probe_ready(self):
        result, _ = self.run_case(FakeFrida(), require_ready=True)
        self.assertEqual(result['stop_reason'], 'probe_not_ready')
        result, _ = self.run_case(FakeFrida(messages=[({'type':'send','payload':{'event':'probe_ready'}},None)]), require_ready=True)
        self.assertTrue(result['success'])

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory); (p/'s').write_text(''); (p/'out').write_text('keep')
            with self.assertRaises(FileExistsError):
                capture(RunSpec(script=p/'s',out=p/'out',local=True,pid=1),frida_module=FakeFrida())
            self.assertEqual((p/'out').read_text(),'keep')

    def test_late_callback_after_close_is_ignored(self):
        api = FakeFrida()
        self.run_case(api)
        api.callbacks[0]({'type': 'send', 'payload': 1}, None)

    def test_validation(self):
        for kwargs in ({'duration':float('nan')},{'max_events':0},{'max_binary_bytes':-1}):
            with self.assertRaises(ValueError): RunSpec(script=Path('s'),out=Path('o'),local=True,pid=1,**kwargs)
        with self.assertRaises(ValueError): RunSpec(script=Path('s'),out=Path('o'),pid=1)


class NativeGeneratorTest(unittest.TestCase):
    def test_validation_and_source(self):
        with self.assertRaises(ValueError): NativeProbeSpec('libx',symbol='f',offset=1)
        with self.assertRaises(ValueError): NativeProbeSpec('libx',symbol='f',buffer_arg=0,buffer_size=3)
        with self.assertRaises(ValueError): NativeProbeSpec('libx',symbol='f',arg_count=1,buffer_arg=0,buffer_size=5000)
        source = generate_native_hook(NativeProbeSpec('libx',symbol='f',arg_count=1))
        self.assertIn('native_enter',source); self.assertIn('native_leave',source)
        self.assertIn('module.getExportByName',source)
        self.assertNotIn('retval.replace',source)
        self.assertIn("build_hash:'not_verified'",source)
