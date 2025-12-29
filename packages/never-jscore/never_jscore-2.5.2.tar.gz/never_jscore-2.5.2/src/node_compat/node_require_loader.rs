// Node.js require loader implementation for never-jscore

use deno_core::FastString;
use deno_core::url::Url;
use deno_error::JsErrorBox;
use deno_node::{NodeRequireLoader, NodeRequireLoaderRc};
use deno_permissions::PermissionsContainer;
use node_resolver::errors::PackageJsonLoadError;
use std::borrow::Cow;
use std::path::Path;
use std::rc::Rc;

/// Simple NodeRequireLoader implementation for never-jscore
pub struct NeverJsCoreRequireLoader;

impl NeverJsCoreRequireLoader {
    pub fn new_rc() -> NodeRequireLoaderRc {
        Rc::new(Self)
    }
}

impl NodeRequireLoader for NeverJsCoreRequireLoader {
    fn ensure_read_permission<'a>(
        &self,
        _permissions: &mut PermissionsContainer,
        path: Cow<'a, Path>,
    ) -> Result<Cow<'a, Path>, JsErrorBox> {
        // For now, allow all read operations
        // In production, you might want to implement proper permission checks
        Ok(path)
    }

    fn load_text_file_lossy(&self, path: &Path) -> Result<FastString, JsErrorBox> {
        // Read file and convert to FastString
        let content = std::fs::read_to_string(path)
            .map_err(|e| JsErrorBox::from_err(e))?;
        Ok(FastString::from(content))
    }

    fn is_maybe_cjs(&self, specifier: &Url) -> Result<bool, PackageJsonLoadError> {
        // Check if the file might be CommonJS
        // For simplicity, assume .js files are CommonJS unless proven otherwise
        if let Some(path_segments) = specifier.path_segments() {
            if let Some(last) = path_segments.last() {
                return Ok(last.ends_with(".js") || last.ends_with(".cjs"));
            }
        }
        Ok(true)
    }
}
