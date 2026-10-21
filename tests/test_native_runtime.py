import shutil
import subprocess
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mrat.native_hook import NativeProbeSpec, generate_native_hook

HARNESS=r'''
const assert=require('assert');const events=[];let callbacks;
class Pointer {
 constructor(n){this.n=n;}
 add(n){return new Pointer(this.n+n);}
 sub(p){return new Pointer(this.n-p.n);}
 compare(p){return this.n-p.n;}
 equals(p){return this.n===p.n;}
 toString(){return '0x'+this.n.toString(16);}
 toInt32(){return this.n|0;}
 readByteArray(n){return new Uint8Array([0,255,65,0]).slice(0,n).buffer;}
}
const moduleMock={name:'libtest',path:'/test/libtest',base:new Pointer(100),size:100,
 getExportByName:()=>new Pointer(110)};
global.Process={id:1,arch:'arm64',pointerSize:8,getCurrentThreadId:()=>9,
 findModuleByName:()=>moduleMock,findRangeByAddress:()=>({protection:'r-x'})};
global.Interceptor={attach:(p,c)=>{callbacks=c;return {detach(){}};},flush(){}};
global.send=(p,b)=>events.push({p,b});
'''

@unittest.skipUnless(shutil.which('node'),'Node required')
class NativeJsTest(unittest.TestCase):
    def run_node(self, ending, spec):
        return subprocess.run(['node','-e',HARNESS+generate_native_hook(spec)+ending],capture_output=True,text=True)

    def test_enter_return_and_binary_capture(self):
        ending=r'''
const invocation={threadId:9,context:{}};
callbacks.onEnter.call(invocation,[new Pointer(19),new Pointer(23),new Pointer(500)]);
callbacks.onLeave.call(invocation,new Pointer(42));
assert.equal(events[0].p.event,'probe_ready');
const entry=events.find(e=>e.p.event==='native_enter').p;
const exit=events.find(e=>e.p.event==='native_leave').p;
assert.equal(entry.data.invocation_id,exit.data.invocation_id);
assert.equal(exit.data.return_i32,42);
assert.deepEqual(Array.from(new Uint8Array(events.find(e=>e.b).b)),[0,255,65,0]);
'''
        result=self.run_node(ending,NativeProbeSpec('libtest',symbol='test',arg_count=3,buffer_arg=2,buffer_size=4))
        self.assertEqual(result.returncode,0,result.stderr)

    def test_limit_reported_once_when_calls_are_omitted(self):
        ending=r'''
const invocation={threadId:9,context:{}};
callbacks.onEnter.call(invocation,[new Pointer(1)]);
callbacks.onLeave.call(invocation,new Pointer(0));
assert.equal(events.filter(e=>e.p.event==='probe_limit').length,0);
callbacks.onEnter.call(invocation,[new Pointer(1)]);
callbacks.onEnter.call(invocation,[new Pointer(1)]);
assert.equal(events.filter(e=>e.p.event==='probe_limit').length,1);
'''
        result=self.run_node(ending,NativeProbeSpec('libtest',symbol='test',arg_count=1,max_calls=1))
        self.assertEqual(result.returncode,0,result.stderr)


class NativeGeneratorTest(unittest.TestCase):
    def test_validation_and_source(self):
        with self.assertRaises(ValueError): NativeProbeSpec('libx',symbol='f',offset=1)
        with self.assertRaises(ValueError): NativeProbeSpec('libx',symbol='f',buffer_arg=0,buffer_size=3)
        with self.assertRaises(ValueError): NativeProbeSpec('libx',symbol='f',arg_count=1,buffer_arg=0,buffer_size=5000)
        source=generate_native_hook(NativeProbeSpec('libx',symbol='f',arg_count=1))
        self.assertIn('native_enter',source); self.assertIn('native_leave',source)
        self.assertIn('module.getExportByName',source)
        self.assertNotIn('retval.replace',source)
        self.assertIn("build_hash:'not_verified'",source)
