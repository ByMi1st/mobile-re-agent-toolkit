"""Synthetic JS execution checks, not device compatibility tests."""
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from mrat.runtime.java_hook import generate_java_hook
from mrat.core.model import JavaMethodSpec

@unittest.skipUnless(shutil.which('node'), 'Node.js required for synthetic JS check')
class ProbeRuntimeTest(unittest.TestCase):
    def test_result_and_exception_survive_observation_failure(self):
        source = generate_java_hook(JavaMethodSpec('example.Target', 'run'), include_stack=False)
        harness = '''
const assert = require('assert');
let failOriginal = false, failObservation = false;
const originalError = new Error('original');
const method = {call: function() {if(failOriginal) throw originalError; return 42;}};
global.Process = {id: 123, getCurrentThreadId: () => 7};
global.Java = {perform: f => f(), use: () => ({run:{overload:()=>method}})};
global.send = () => {if(failObservation) throw new Error('observer');};
'''
        harness += source
        harness += '''
assert.equal(method.implementation.call({}), 42);
failObservation = true;
assert.equal(method.implementation.call({}), 42);
failOriginal = true;
assert.throws(() => method.implementation.call({}), e => e === originalError);
'''
        result = subprocess.run(['node', '-e', harness], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
