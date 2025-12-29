// Stub implementation for deno_telemetry
// Provides minimal no-op implementation to satisfy deno_fetch imports

export const TRACING_ENABLED = false;
export const METRICS_ENABLED = false;
export const PROPAGATORS = [];

export const builtinTracer = {
  startSpan() { return null; }
};

export class ContextManager {
  active() { return null; }
  with() { return null; }
}

export function enterSpan() {}
export function restoreSnapshot() {}

export const telemetry = {
  TRACING_ENABLED,
  METRICS_ENABLED,
};
