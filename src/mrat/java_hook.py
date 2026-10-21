"""Generate deterministic Frida Java method probes."""

from __future__ import annotations

import json

from .model import JavaMethodSpec, ProbeContext


def _js(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def generate_java_hook(
    spec: JavaMethodSpec,
    context: ProbeContext | None = None,
    *,
    include_stack: bool = True,
) -> str:
    """Return a standalone Frida Java probe for one exact overload.

    The generator deliberately requires an exact overload. Runtime discovery
    is intentionally separate from source generation and is not included here.
    """

    context = context or ProbeContext()
    overload_args = ", ".join(_js(item) for item in spec.overload)
    stack_expr = (
        "Java.use('android.util.Log').getStackTraceString("
        "Java.use('java.lang.Exception').$new())"
        if include_stack
        else "null"
    )
    return f"""'use strict';

Java.perform(function () {{
  const targetClassName = {_js(spec.class_name)};
  const targetMethodName = {_js(spec.method_name)};
  const overloadTypes = {_js(list(spec.overload))};
  const Target = Java.use(targetClassName);
  const Method = Target[targetMethodName].overload({overload_args});
  let sequence = 0;

  function safeValue(value) {{
    if (value === null || value === undefined) return null;
    try {{
      const text = String(value);
      return {{ type: value.$className || typeof value, value: text.slice(0, 4096), truncated: text.length > 4096 }};
    }} catch (error) {{
      return {{ type: typeof value, value: '<unprintable>', error: String(error) }};
    }}
  }}

  Method.implementation = function () {{
    const args = Array.prototype.slice.call(arguments);
    const invocationId = Process.id + ':' + Process.getCurrentThreadId() + ':' + (++sequence);
    const startedAt = Date.now();
    let result = null;
    let failure = null;

    try {{
      result = Method.call.apply(Method, [this].concat(args));
      return result;
    }} catch (error) {{
      failure = String(error);
      throw error;
    }} finally {{
      try {{
      send({{
        schema_version: 1,
        event: 'java_method_invocation',
        observation_mode: {_js(context.observation_mode)},
        invocation_id: invocationId,
        scene_id: {_js(context.scene_id)},
        request_id: {_js(context.request_id)},
        timestamp_ms: Date.now(),
        duration_ms: Date.now() - startedAt,
        pid: Process.id,
        tid: Process.getCurrentThreadId(),
        target: {{
          class_name: targetClassName,
          method_name: targetMethodName,
          overload: overloadTypes
        }},
        arguments: args.map(safeValue),
        return_value: failure === null ? safeValue(result) : null,
        exception: failure,
        stack: {stack_expr}
      }});
      }} catch (observationError) {{
        // Instrumentation must not replace the original result or exception.
      }}
    }}
  }};

  send({{
    schema_version: 1,
    event: 'probe_ready',
    observation_mode: {_js(context.observation_mode)},
    timestamp_ms: Date.now(),
    pid: Process.id,
    target: {{
      class_name: targetClassName,
      method_name: targetMethodName,
      overload: overloadTypes
    }}
  }});
}});
"""

