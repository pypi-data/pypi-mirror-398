// XMLHttpRequest extension - provides browser-compatible XHR
// Based on fetch API, no Rust ops needed

use deno_core::Extension;

/// Get JavaScript initialization code for XMLHttpRequest
/// This provides a fetch-based XMLHttpRequest implementation
pub fn get_init_js() -> &'static str {
    include_str!("init_xhr.js")
}

/// Build XHR extension (no-op, just provides JS code)
/// XMLHttpRequest is loaded via get_init_js() in context initialization
pub fn extensions(_options: &crate::ext::ExtensionOptions, _is_snapshot: bool) -> Vec<Extension> {
    // No Rust operations needed, XMLHttpRequest is pure JavaScript
    vec![]
}
