// Stub extension for deno_http
// Provides minimal exports needed by deno_node's http.ts and http2.ts

deno_core::extension!(
    deno_http,
    esm = [
        dir "src/ext/http_stub",
        "00_serve.ts",
    ],
);

pub fn init() -> deno_core::Extension {
    deno_http::init()
}
