use deno_core::{extension, OpState, Extension};
use std::rc::Rc;

use super::ExtensionTrait;
use crate::storage::ResultStorage;

/// Op: Store JavaScript execution result
///
/// This op allows JavaScript code to store execution results to Rust side.
/// Uses #[op2(fast)] for performance optimization.
#[deno_core::op2(fast)]
pub fn op_store_result(state: &mut OpState, #[string] value: String) {
    if let Some(storage) = state.try_borrow_mut::<Rc<ResultStorage>>() {
        storage.store(value);
    }
}

/// Op: Early return (for Hook interception) - Legacy version using throw error
///
/// Used to return results early and terminate execution during JS execution.
/// Very useful in reverse engineering, e.g., Hook XMLHttpRequest.send to intercept parameters.
///
/// Implementation: Store value in ResultStorage and mark as early return,
/// JavaScript side needs to throw error to interrupt execution
#[deno_core::op2(fast)]
pub fn op_early_return(state: &mut OpState, #[string] value: String) {
    if let Some(storage) = state.try_borrow_mut::<Rc<ResultStorage>>() {
        storage.store(value.clone());
        storage.mark_early_return();
    }
}

/// Op: Log message to stderr (for debugging)
///
/// Used by the protection system to log Web API calls when logging is enabled.
#[deno_core::op2(fast)]
pub fn op_log(#[string] message: &str) {
    eprintln!("{}", message);
}

// Core extension - provides basic never_jscore functionality
extension!(
    init_core,
    ops = [op_store_result, op_early_return, op_log],
    options = {
        storage: Rc<ResultStorage>,
        enable_logging: bool,
    },
    state = |state, options| {
        state.put(options.storage);
        // Could add logging state here if needed
    }
);

impl ExtensionTrait<super::ExtensionOptions> for init_core {
    fn init(options: super::ExtensionOptions) -> Extension {
        init_core::init(options.storage, options.enable_logging)
    }
}

/// Get the JavaScript initialization code for core functions
pub fn get_init_js() -> &'static str {
    include_str!("init_core.js")
}

/// Build core extensions
pub fn extensions(options: super::ExtensionOptions, is_snapshot: bool) -> Vec<Extension> {
    vec![init_core::build(options, is_snapshot)]
}
