"""Frida lifecycle runner. Imports Frida only when a capture is requested."""
from __future__ import annotations

import base64
import hashlib
import json
import math
import signal
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunSpec:
    script: Path
    out: Path
    duration: float = 10.0
    device_id: str | None = None
    remote: str | None = None
    local: bool = False
    pid: int | None = None
    spawn: tuple[str, ...] = ()
    max_events: int = 10000
    max_message_bytes: int = 262144
    max_binary_bytes: int = 65536
    setup_timeout: float = 15.0
    require_ready: bool = False

    def __post_init__(self):
        if sum([self.local, self.device_id is not None, self.remote is not None]) != 1:
            raise ValueError('select exactly one of local, device_id or remote')
        if (self.pid is not None) == bool(self.spawn):
            raise ValueError('select exactly one of pid or spawn')
        if self.pid is not None and self.pid <= 0:
            raise ValueError('pid must be positive')
        if not math.isfinite(self.duration) or not 0 < self.duration <= 86400:
            raise ValueError('duration must be finite and within (0, 86400]')
        if not math.isfinite(self.setup_timeout) or not 0 < self.setup_timeout <= 300:
            raise ValueError('setup_timeout must be finite and within (0, 300]')
        if not 1 <= self.max_events <= 1000000:
            raise ValueError('max_events must be within [1, 1000000]')
        if not 1024 <= self.max_message_bytes <= 1048576:
            raise ValueError('max_message_bytes must be within [1024, 1048576]')
        if not 0 <= self.max_binary_bytes <= 1048576:
            raise ValueError('max_binary_bytes must be within [0, 1048576]')
        if any(not a for a in self.spawn):
            raise ValueError('spawn arguments must not be empty')


def capture(spec: RunSpec, *, frida_module: Any = None,
            stop_event: threading.Event | None = None) -> dict:
    """Capture one script; kill only a process spawned by this invocation.

    Existing processes selected by PID are never killed or resumed. We do not
    create ADB forwards, start daemons or change any system configuration.
    """
    source_bytes = spec.script.read_bytes()
    if len(source_bytes) > 2 * 1024 * 1024:
        raise ValueError('script exceeds 2 MiB')
    source = source_bytes.decode('utf-8')
    if frida_module is None:
        try:
            import frida as frida_module
        except ImportError as error:
            raise RuntimeError('install the optional runtime dependency: pip install ".[runtime]"') from error
    spec.out.parent.mkdir(parents=True, exist_ok=True)
    stop = stop_event or threading.Event()
    lock = threading.RLock()
    session_id = uuid.uuid4().hex
    session = script = device = None
    owned_pid = pid = None
    stats = {'messages': 0, 'omitted_messages': 0, 'script_errors': 0,
             'oversized_messages': 0, 'binary_truncations': 0, 'probe_limits': 0, 'buffer_errors': 0, 'probe_ready_count': 0}
    reason = 'duration'
    cleanup_errors = []
    detached = threading.Event()
    detached_reason = None
    old_signals = {}
    handle = spec.out.open('x', encoding='utf-8')  # Never overwrite evidence.
    closed = False

    def write(event, **data):
        with lock:
            if closed:
                return
            handle.write(json.dumps({'schema_version': 1, 'event': event,
                'session_id': session_id, 'pid': pid,
                'host_monotonic_ns': time.monotonic_ns(), 'data': data},
                ensure_ascii=False) + '\n')
            handle.flush()

    def on_message(message, binary):
        try:
            with lock:
                if stats['messages'] >= spec.max_events:
                    stats['omitted_messages'] += 1
                    stop.set()
                    return
                stats['messages'] += 1
                encoded = json.dumps(message, ensure_ascii=False).encode('utf-8')
                if len(encoded) > spec.max_message_bytes:
                    stats['oversized_messages'] += 1
                    write('frida_message_oversized', bytes=len(encoded),
                          sha256=hashlib.sha256(encoded).hexdigest())
                    stop.set()
                    return
                binary_info = None
                if binary is not None:
                    raw = bytes(binary)
                    kept = raw[:spec.max_binary_bytes]
                    truncated = len(kept) != len(raw)
                    stats['binary_truncations'] += int(truncated)
                    binary_info = {'encoding': 'base64', 'data': base64.b64encode(kept).decode(),
                        'original_size': len(raw), 'retained_size': len(kept),
                        'sha256': hashlib.sha256(raw).hexdigest(), 'truncated': truncated}
                write('frida_message', message=message, binary=binary_info)
                payload = message.get('payload')
                if isinstance(payload, dict) and payload.get('event') == 'probe_ready':
                    stats['probe_ready_count'] += 1
                if isinstance(payload, dict) and payload.get('event') == 'probe_limit':
                    stats['probe_limits'] += 1
                    stop.set()
                if isinstance(payload, dict) and payload.get('event') == 'native_buffer_error':
                    stats['buffer_errors'] += 1
                if message.get('type') == 'error' or (
                    message.get('type') == 'send' and isinstance(message.get('payload'), dict)
                    and message['payload'].get('event') in {'probe_error', 'hook_error'}):
                    stats['script_errors'] += 1
                    stop.set()
                if stats['messages'] >= spec.max_events:
                    stop.set()
        except Exception as error:
            # Do not let callback errors silently masquerade as a clean capture.
            stats['script_errors'] += 1
            try:
                write('message_error', error=str(error))
            finally:
                stop.set()

    def on_detached(reason, crash=None):
        nonlocal detached_reason
        detached_reason = str(reason)
        detached.set()
        stop.set()

    cancellable = frida_module.Cancellable()
    timeout = threading.Timer(spec.setup_timeout, cancellable.cancel)
    timeout.daemon = True
    summary = None
    try:
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGINT, signal.SIGTERM):
                old_signals[sig] = signal.getsignal(sig)
                signal.signal(sig, lambda *_: stop.set())
        write('runner_start', script_sha256=hashlib.sha256(source_bytes).hexdigest(),
              frida_version=getattr(frida_module, '__version__', 'unknown'),
              device={'local': spec.local, 'device_id': spec.device_id, 'remote': spec.remote},
              target={'pid': spec.pid, 'spawn': list(spec.spawn)},
              limits={'duration': spec.duration, 'setup_timeout': spec.setup_timeout,
                      'max_events': spec.max_events, 'max_message_bytes': spec.max_message_bytes,
                      'max_binary_bytes': spec.max_binary_bytes},
              effects='script execution; owned spawn terminated on cleanup; attached target preserved')
        timeout.start()
        with cancellable:
            if spec.local:
                device = frida_module.get_local_device()
            elif spec.remote:
                device = frida_module.get_device_manager().add_remote_device(spec.remote)
            else:
                device = frida_module.get_device(spec.device_id, timeout=int(spec.setup_timeout))
            write('device_selected', device_id=getattr(device, 'id', None),
                  device_name=getattr(device, 'name', None), device_type=getattr(device, 'type', None))
            if spec.spawn:
                owned_pid = pid = device.spawn(list(spec.spawn))
                write('target_spawned', suspended=True)
            else:
                pid = spec.pid
            if stop.is_set():
                raise RuntimeError('capture cancelled during setup')
            session = device.attach(pid)
            session.on('detached', on_detached)
            script = session.create_script(source)
            script.on('message', on_message)
            script.load()
            write('script_loaded')
            if stats['script_errors']:
                raise RuntimeError('probe reported an error during setup')
            if owned_pid is not None:
                device.resume(owned_pid)
                write('target_resumed')
        timeout.cancel()
        write('capture_started')
        stop.wait(spec.duration)
        if stats['script_errors']:
            reason = 'script_error'
        elif stats['probe_limits']:
            reason = 'probe_limit'
        elif stats['oversized_messages']:
            reason = 'message_size_limit'
        elif stats['messages'] >= spec.max_events:
            reason = 'event_limit'
        elif detached.is_set():
            reason = 'target_detached'
        elif stop.is_set():
            reason = 'cancelled'
        if spec.require_ready and not stats['probe_ready_count'] and reason in {'duration', 'target_detached'}:
            reason = 'probe_not_ready'
    except Exception as error:
        reason = 'setup_error'
        write('runner_error', error=str(error), error_type=type(error).__name__)
    finally:
        timeout.cancel()
        # Each cleanup operation has its own deadline, independent of cancelled setup.
        def clean(label, operation):
            cancel = frida_module.Cancellable()
            timer = threading.Timer(spec.setup_timeout, cancel.cancel)
            timer.daemon = True
            timer.start()
            try:
                with cancel:
                    operation()
                write('cleanup_action', action=label, success=True)
            except Exception as error:
                cleanup_errors.append({'action': label, 'error': str(error)})
            finally:
                timer.cancel()
        if script is not None and not detached.is_set():
            clean('unload_script', script.unload)
        if session is not None and not detached.is_set():
            clean('detach_session', session.detach)
        if owned_pid is not None and device is not None and detached_reason != 'process-terminated':
            clean('terminate_owned_spawn', lambda: device.kill(owned_pid))
        summary = {'stop_reason': reason, 'detached_reason': detached_reason,
            **stats, 'cleanup_errors': cleanup_errors,
            'success': (reason == 'duration' or (reason == 'target_detached' and detached_reason == 'process-terminated')) and not stats['script_errors']
                       and not stats['oversized_messages'] and not cleanup_errors,
            'producer_loss': 'unknown',
            'coverage': 'partial' if reason in {'event_limit','message_size_limit','cancelled','setup_error','script_error','probe_limit','probe_not_ready'}
                        or stats['binary_truncations'] or stats['buffer_errors'] else 'selected-window-only'}
        write('runner_complete', **summary)
        with lock:
            closed = True
            handle.close()
        for sig, previous in old_signals.items():
            signal.signal(sig, previous)
    return summary
