"""Compare selected capture values to the synthetic fixture's independent output."""
from __future__ import annotations
import base64
import json
from pathlib import Path


def verify(events: Path, truth: Path) -> dict:
    rows = [json.loads(line) for line in events.read_text().splitlines()]
    final = next(row['data'] for row in reversed(rows) if row['event'] == 'runner_complete')
    if not final['success']:
        raise ValueError(f'capture failed: {final}')
    entries, exits, buffers = {}, {}, {}
    for row in rows:
        if row['event'] != 'frida_message': continue
        message = row['data']['message']
        if message.get('type') != 'send' or not isinstance(message.get('payload'),dict): continue
        payload = message['payload']; data = payload.get('data', {})
        call = data.get('invocation_id')
        if payload['event'] == 'native_enter': entries[call] = data
        if payload['event'] == 'native_leave': exits[call] = data
        if payload['event'] == 'native_buffer':
            binary = row['data']['binary']
            if binary['truncated']: raise ValueError('binary was truncated')
            buffers[(call,data['phase'])] = base64.b64decode(binary['data'])
    paired = sorted(set(entries) & set(exits))
    if not paired: raise ValueError('no paired native calls')
    for call in paired:
        args = entries[call]['raw_arguments']
        if int(args[0],16)!=19 or int(args[1],16)!=23: raise ValueError('wrong arguments')
        if exits[call]['return_i32'] != 42: raise ValueError('wrong return')
        if buffers.get((call,'enter')) != b'\x00\xffA\x00': raise ValueError('wrong input bytes')
        if buffers.get((call,'leave')) != b'\x00\xff@\x00': raise ValueError('wrong output bytes')
    actual = truth.read_text().splitlines()
    if len(actual)<len(paired) or any(line!='42,64' for line in actual):
        raise ValueError('independent fixture output differs')
    return {'paired_calls':len(paired),'fixture_calls':len(actual),
            'open_calls':len(set(entries)-set(exits)),
            'scope':'selected complete calls, not exhaustive whole-process coverage'}


if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('events',type=Path);p.add_argument('truth',type=Path)
    a=p.parse_args();print(json.dumps(verify(a.events,a.truth),indent=2))
