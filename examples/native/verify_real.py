"""Run a source-built native fixture with real Frida. No phone required.

Usage: PYTHONPATH=src python examples/native/verify_real.py
Requires a compatible Frida binding and clang/cc. Writes only to a fresh temp dir.
"""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


def main():
    import frida
    compiler=shutil.which('clang') or shutil.which('cc')
    if not compiler: raise RuntimeError('C compiler required')
    if platform.system() not in ('Linux','Darwin'):
        raise RuntimeError('fixture build supports Linux/macOS only')
    work=Path(tempfile.mkdtemp(prefix='mrat-real-'))
    darwin=platform.system()=='Darwin'
    name='libmrat_fixture.dylib' if darwin else 'libmrat_fixture.so'
    lib=work/name; exe=work/'fixture'
    subprocess.run([compiler, '-dynamiclib' if darwin else '-shared', '-fPIC',
        str(ROOT/'examples/native/library.c'), '-o',str(lib)],check=True)
    subprocess.run([compiler,str(ROOT/'examples/native/driver.c'),'-L'+str(work),
        '-lmrat_fixture','-Wl,-rpath,'+str(work),'-o',str(exe)],check=True)
    from mrat.native_hook import NativeProbeSpec, generate_native_hook
    probe=work/'probe.js'
    probe.write_text(generate_native_hook(NativeProbeSpec(name,symbol='mrat_add',
        arg_count=3,buffer_arg=2,buffer_size=4)))
    env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'src')

    def run(out,truth,pid=None,script=probe,expected=0):
        command=[PYTHON,'-m','mrat.cli','run','--local','--script',str(script),
            '--out',str(out),'--require-ready','--duration','0.6','--setup-timeout','8']
        command+=['--pid',str(pid)] if pid else ['--spawn',str(exe),str(truth)]
        result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=40)
        if result.returncode!=expected:
            raise RuntimeError(f'{command}: exit={result.returncode}\n{result.stdout}\n{result.stderr}\nartifacts={work}')
        return json.loads(result.stdout.strip().splitlines()[-1])

    spec=importlib.util.spec_from_file_location('capture_verify',ROOT/'examples/native/verify_capture.py')
    verify_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify_module)
    spawn_result=run(work/'spawn.jsonl',work/'spawn-truth.txt')
    spawn_check=verify_module.verify(work/'spawn.jsonl',work/'spawn-truth.txt')
    # Verify the process created by the runner is no longer present.
    rows=[json.loads(l) for l in (work/'spawn.jsonl').read_text().splitlines()]
    spawned=next(r['pid'] for r in rows if r['event']=='target_spawned')
    try: os.kill(spawned,0)
    except ProcessLookupError: pass
    else: raise RuntimeError('owned spawn still exists after cleanup')

    external=subprocess.Popen([str(exe),str(work/'attach-truth.txt')])
    try:
        time.sleep(.2)
        attach_result=run(work/'attach.jsonl',work/'attach-truth.txt',pid=external.pid)
        if external.poll() is not None: raise RuntimeError('attach killed external fixture')
        attach_check=verify_module.verify(work/'attach.jsonl',work/'attach-truth.txt')
        bad=work/'bad.js';bad.write_text('throw new Error("synthetic failure");')
        bad_result=run(work/'error.jsonl',work/'unused',pid=external.pid,script=bad,expected=1)
        if external.poll() is not None: raise RuntimeError('error cleanup killed external fixture')
        if not bad_result['script_errors']: raise RuntimeError('script error not reported')
    finally:
        external.terminate()
        try: external.wait(timeout=3)
        except subprocess.TimeoutExpired: external.kill();external.wait()
    report={'host':platform.system(),'arch':platform.machine(),'frida':frida.__version__,
        'spawn':spawn_check,'attach':attach_check,'script_error_preserved_target':True,
        'owned_spawn_cleanup':True,'artifacts':str(work)}
    (work/'verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
