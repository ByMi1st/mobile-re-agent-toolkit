# Architecture

The toolkit is split into four boundaries.

```text
static candidate
  -> runtime discovery
  -> generated observation probe
  -> structured evidence event
  -> optional allowlisted invocation
```

## Runtime discovery

Answers whether the class, class loader, method, overload and object exist in
the selected process. Discovery never modifies arguments or return values.

## Probe generation

Produces deterministic Java or native observation probes from a typed spec.
Generated probes emit the same event envelope regardless of the target.

## Runner

Owns the explicit device/process selection, attach or spawn lifecycle, message
collection, timeouts, detach and cleanup. The runner must not select the first
available device implicitly.

## Allowlisted invocation

Stable, manually verified methods may later be exposed through a temporary,
loopback-only interface. Arbitrary reflection and arbitrary file access are out
of scope.

## Evidence boundary

Observations are tagged `natural`; argument replacement or direct invocation is
tagged `controlled`. Controlled results cannot be used to claim natural runtime
behavior.
