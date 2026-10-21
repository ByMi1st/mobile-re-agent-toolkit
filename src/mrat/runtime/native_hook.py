"""Generate a bounded native Interceptor observation script, without mutation."""
from __future__ import annotations
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class NativeProbeSpec:
    module: str
    symbol: str | None = None
    offset: int | None = None
    arg_count: int = 0
    buffer_arg: int | None = None
    buffer_size: int = 0
    max_calls: int = 1000
    backtrace: bool = False

    def __post_init__(self):
        if not self.module or (self.symbol is None) == (self.offset is None):
            raise ValueError('require module and exactly one symbol or offset')
        if self.symbol == '' or self.offset is not None and not 0 <= self.offset < 2**53:
            raise ValueError('invalid symbol or offset')
        if not 0 <= self.arg_count <= 8 or not 1 <= self.max_calls <= 100000:
            raise ValueError('arg_count must be 0..8; max_calls must be 1..100000')
        if not 0 <= self.buffer_size <= 4096:
            raise ValueError('buffer_size must be 0..4096')
        if (self.buffer_arg is None) != (self.buffer_size == 0):
            raise ValueError('buffer_arg and nonzero buffer_size must be provided together')
        if self.buffer_arg is not None and not 0 <= self.buffer_arg < self.arg_count:
            raise ValueError('buffer_arg must refer to a captured argument')


def generate_native_hook(spec: NativeProbeSpec) -> str:
    config = json.dumps(spec.__dict__)
    return r''' 'use strict';
const config = CONFIG;
let sequence = 0;
let active = null;
let observer = null;
let limitReported = false;
function emit(event, data, binary) {
  try { send({schema_version:1,event:event,pid:Process.id,
    tid:Process.getCurrentThreadId(),timestamp_ms:Date.now(),data:data}, binary); }
  catch (_) { /* Never alter the target result due to a logging failure. */ }
}
function snapshot(callId, phase, pointer) {
  if (config.buffer_arg === null) return;
  try {
    const bytes = pointer.readByteArray(config.buffer_size);
    emit('native_buffer', {invocation_id:callId,phase:phase,
      address:pointer.toString(),size:config.buffer_size}, bytes);
  } catch (error) {
    emit('native_buffer_error', {invocation_id:callId,phase:phase,error:String(error)});
  }
}
function install(module) {
  if (active !== null) return;
  try {
    const address = config.symbol !== null ? module.getExportByName(config.symbol) : module.base.add(config.offset);
    if (address.compare(module.base) < 0 || address.compare(module.base.add(module.size)) >= 0)
      throw new Error('address is outside selected module');
    const range = Process.findRangeByAddress(address);
    if (range === null || range.protection.indexOf('x') < 0)
      throw new Error('selected address is not executable');
    const identity = {name:module.name,path:module.path,base:module.base.toString(),
      size:module.size,address:address.toString(),offset:address.sub(module.base).toString(),
      arch:Process.arch,pointer_size:Process.pointerSize,build_hash:'not_verified'};
    const listener = Interceptor.attach(address, {
      onEnter(args) {
        this.selected = sequence < config.max_calls;
        if (!this.selected) {
          if (!limitReported) {
            limitReported = true;
            emit('probe_limit', {limit:config.max_calls,scope:'selected calls; later calls omitted'});
          }
          return;
        }
        this.callId = Process.id + ':' + this.threadId + ':' + (++sequence);
        const raw = [];
        for (let i=0;i<config.arg_count;i++) raw.push(args[i].toString());
        if (config.buffer_arg !== null) this.buffer = args[config.buffer_arg];
        let stack = null, stackError = null;
        if (config.backtrace) {
          try { stack = Thread.backtrace(this.context, Backtracer.ACCURATE).map(p => p.toString()); }
          catch (error) { stackError = String(error); }
        }
        emit('native_enter', {invocation_id:this.callId,target:identity,
          raw_arguments:raw,backtrace:stack,backtrace_error:stackError});
        snapshot(this.callId, 'enter', this.buffer);
      },
      onLeave(retval) {
        if (!this.selected) return;
        snapshot(this.callId, 'leave', this.buffer);
        emit('native_leave', {invocation_id:this.callId,target:identity,
          raw_return:retval.toString(),return_i32:retval.toInt32()});
      }
    });
    active = {module:module,listener:listener};
    Interceptor.flush();
    emit('probe_ready', {target:identity,max_calls:config.max_calls,
      arguments:'raw general-purpose ABI slots; floats/structures unsupported'});
  } catch (error) { emit('hook_error', {module:config.module,error:String(error)}); }
}
const found = Process.findModuleByName(config.module);
if (found !== null) install(found);
if (typeof Process.attachModuleObserver === 'function') {
  observer = Process.attachModuleObserver({
    onAdded(module) { if (module.name === config.module) install(module); },
    onRemoved(module) {
      if (active !== null && module.base.equals(active.module.base)) {
        try { active.listener.detach(); } catch (_) {}
        active = null;
        emit('module_unloaded', {name:module.name,base:module.base.toString()});
      }
    }
  });
} else if (found === null) {
  emit('hook_error', {error:'module not loaded and module observer API unavailable'});
}
'''.replace('CONFIG', config).lstrip()
