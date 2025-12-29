// src/ops/mod.rs
// Legacy ops module - kept for backward compatibility
//
// Note: Core operations have been moved to the modular extension system in src/ext/
// This module is kept to maintain backward compatibility with existing code.
//
// New code should use the extension system directly via src/ext/core and src/ext/hook

// Re-export storage_ops for backward compatibility
pub mod storage_ops;
pub use storage_ops::*;
