/// Browser Protection Extension
///
/// Protects Web APIs by:
/// 1. Making functions show '[native code]' instead of implementation
/// 2. Hiding Deno internals (Deno.core)
/// 3. Making the environment appear as a real browser

use deno_core::Extension;

/// Get the initialization JavaScript for browser protection
pub fn get_init_js() -> &'static str {
    include_str!("init_protection.js")
}

/// Create browser protection extensions
pub fn extensions(_options: &crate::ext::ExtensionOptions, _is_snapshot: bool) -> Vec<Extension> {
    vec![]
}
