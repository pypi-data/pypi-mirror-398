// Minimal runtime stub extension for deno_node compatibility
// Provides ext:runtime/98_global_scope_shared.js stub

deno_core::extension!(
    runtime,
    esm = [
        dir "src/ext/runtime_stub",
        "98_global_scope_shared.js",
    ],
);

pub fn init() -> deno_core::Extension {
    runtime::init()
}
