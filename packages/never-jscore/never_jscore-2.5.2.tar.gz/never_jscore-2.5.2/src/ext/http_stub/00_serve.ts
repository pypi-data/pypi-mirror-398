// Stub for deno_http/00_serve.ts
// Provides minimal exports needed by deno_node's http.ts

// Stub serve function - not implemented
export function serve() {
  throw new Error("HTTP serve is not supported in never-jscore");
}

export function upgradeHttpRaw() {
  throw new Error("HTTP upgrade is not supported in never-jscore");
}

export function serveHttpOnConnection() {
  throw new Error("HTTP serve on connection is not supported in never-jscore");
}
