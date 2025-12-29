use deno_core::{extension, Extension, OpState};
use super::ExtensionTrait;

use crate::storage::{save_hook_data, get_hook_data, clear_hook_data};

/// Op: Save Hook intercepted data to global storage (new version, used with terminate_execution)
///
/// Save data before calling op_terminate_execution.
/// Data is saved to global static variable, accessible even after isolate termination.
#[deno_core::op2]
#[string]
pub fn op_save_hook_data(#[string] data: String) -> String {
    save_hook_data(data.clone());
    data
}

/// Op: Terminate JavaScript execution
///
/// Calls V8's terminate_execution(), which cannot be caught by try-catch.
/// Must be used with op_save_hook_data - save data first, then terminate.
///
/// ⚠️ Note: This op requires access to V8 IsolateHandle,
/// which must be stored during Context initialization.
#[deno_core::op2(fast)]
pub fn op_terminate_execution(state: &mut OpState) {
    // Get IsolateHandle from OpState
    if let Some(handle) = state.try_borrow_mut::<deno_core::v8::IsolateHandle>() {
        handle.terminate_execution();
    }
}

// Hook extension - provides JavaScript termination and data interception
extension!(
    init_hook,
    ops = [op_terminate_execution, op_save_hook_data]
);

impl ExtensionTrait<()> for init_hook {
    fn init(_: ()) -> Extension {
        init_hook::init()
    }
}

/// Get the JavaScript initialization code for hook functions
pub fn get_init_js() -> &'static str {
    include_str!("init_hook.js")
}

/// Build hook extensions
pub fn extensions(_options: (), is_snapshot: bool) -> Vec<Extension> {
    vec![init_hook::build((), is_snapshot)]
}

// Re-export hook utility functions for use in context.rs
pub use crate::storage::{get_hook_data as get_hook_data_storage, clear_hook_data as clear_hook_data_storage};
