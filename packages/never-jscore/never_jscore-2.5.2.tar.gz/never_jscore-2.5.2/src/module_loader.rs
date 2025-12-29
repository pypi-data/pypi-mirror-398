// File-based module loader for never-jscore
// Enables loading ESM modules from the file system

use deno_core::{
    ModuleLoadResponse, ModuleLoader, ModuleSource, ModuleSourceCode,
    ModuleSpecifier, ModuleType, ResolutionKind,
};
use deno_error::JsErrorBox;
use std::path::{Path, PathBuf};
use std::rc::Rc;

/// A simple file-based module loader that loads ESM modules from the file system
pub struct FileModuleLoader {
    /// Base path for relative module resolution
    base_path: String,
}

impl FileModuleLoader {
    pub fn new() -> Self {
        let cwd = std::env::current_dir()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|_| ".".to_string());
        Self { base_path: cwd }
    }

    pub fn new_with_base(base_path: String) -> Self {
        Self { base_path }
    }

    pub fn into_rc(self) -> Rc<dyn ModuleLoader> {
        Rc::new(self)
    }

    /// Find the module in node_modules by walking up the directory tree
    fn find_in_node_modules(specifier: &str, start_dir: &Path) -> Option<PathBuf> {
        // Split the specifier into package name and subpath
        let (package_name, subpath) = if specifier.starts_with('@') {
            // Scoped package: @scope/name/subpath
            let parts: Vec<&str> = specifier.splitn(3, '/').collect();
            if parts.len() >= 2 {
                let pkg = format!("{}/{}", parts[0], parts[1]);
                let sub = if parts.len() > 2 { Some(parts[2].to_string()) } else { None };
                (pkg, sub)
            } else {
                (specifier.to_string(), None)
            }
        } else {
            // Regular package: name/subpath
            let parts: Vec<&str> = specifier.splitn(2, '/').collect();
            let pkg = parts[0].to_string();
            let sub = if parts.len() > 1 { Some(parts[1].to_string()) } else { None };
            (pkg, sub)
        };

        let mut current = start_dir;
        loop {
            let node_modules = current.join("node_modules").join(&package_name);
            if node_modules.exists() {
                // Check package.json for exports field first
                let package_json = node_modules.join("package.json");
                if package_json.exists() {
                    if let Ok(content) = std::fs::read_to_string(&package_json) {
                        if let Ok(pkg) = serde_json::from_str::<serde_json::Value>(&content) {
                            // Get the subpath key for exports lookup
                            let export_key = if let Some(ref sub) = subpath {
                                format!("./{}", sub)
                            } else {
                                ".".to_string()
                            };

                            // Try "exports" field
                            if let Some(exports) = pkg.get("exports") {
                                if let Some(resolved) = Self::resolve_exports_subpath(exports, &export_key) {
                                    let resolved_path = node_modules.join(&resolved);
                                    if resolved_path.exists() {
                                        return Some(resolved_path);
                                    }
                                }
                            }

                            // For subpath without exports, try direct path
                            if let Some(ref sub) = subpath {
                                let target = node_modules.join(sub);
                                if target.exists() && target.is_file() {
                                    return Some(target);
                                }
                                let with_js = node_modules.join(format!("{}.js", sub));
                                if with_js.exists() {
                                    return Some(with_js);
                                }
                                let index_js = target.join("index.js");
                                if index_js.exists() {
                                    return Some(index_js);
                                }
                            }

                            // No subpath - use main field
                            if subpath.is_none() {
                                if let Some(main) = pkg.get("main").and_then(|m| m.as_str()) {
                                    let main_path = node_modules.join(main);
                                    if main_path.exists() {
                                        return Some(main_path);
                                    }
                                }
                            }
                        }
                    }
                }

                // If there's a subpath but no exports resolved, try direct path
                if let Some(ref sub) = subpath {
                    let target = node_modules.join(sub);
                    if target.exists() && target.is_file() {
                        return Some(target);
                    }
                    let with_js = node_modules.join(format!("{}.js", sub));
                    if with_js.exists() {
                        return Some(with_js);
                    }
                    let index_js = target.join("index.js");
                    if index_js.exists() {
                        return Some(index_js);
                    }
                }

                // Try index.js for package without subpath
                if subpath.is_none() {
                    let index = node_modules.join("index.js");
                    if index.exists() {
                        return Some(index);
                    }
                }
            }

            match current.parent() {
                Some(parent) => current = parent,
                None => break,
            }
        }

        None
    }

    /// Resolve package.json exports field with subpath support
    fn resolve_exports_subpath(exports: &serde_json::Value, subpath: &str) -> Option<String> {
        match exports {
            serde_json::Value::String(s) => {
                // Single string export only matches "."
                if subpath == "." {
                    Some(s.clone())
                } else {
                    None
                }
            }
            serde_json::Value::Object(map) => {
                // First try exact subpath match
                if let Some(entry) = map.get(subpath) {
                    return Self::resolve_export_entry(entry);
                }

                // For "." subpath, also check for direct condition keys
                if subpath == "." {
                    // If there's no "." key, check if this is a conditions object
                    if map.get(".").is_none() &&
                       (map.contains_key("require") || map.contains_key("import") ||
                        map.contains_key("default") || map.contains_key("node")) {
                        return Self::resolve_export_entry(exports);
                    }
                }

                None
            }
            _ => None,
        }
    }

    /// Resolve package.json exports field (legacy - used for "." only)
    fn resolve_exports(exports: &serde_json::Value, subpath: &str) -> Option<String> {
        Self::resolve_exports_subpath(exports, subpath)
    }

    fn resolve_export_entry(entry: &serde_json::Value) -> Option<String> {
        match entry {
            serde_json::Value::String(s) => Some(s.clone()),
            serde_json::Value::Object(map) => {
                // For ESM loading (which is what module loader is used for),
                // prefer import over require
                for key in &["import", "default", "node", "require"] {
                    if let Some(v) = map.get(*key) {
                        if let Some(s) = Self::resolve_export_entry(v) {
                            return Some(s);
                        }
                    }
                }
                None
            }
            _ => None,
        }
    }
}

impl Default for FileModuleLoader {
    fn default() -> Self {
        Self::new()
    }
}

impl ModuleLoader for FileModuleLoader {
    fn resolve(
        &self,
        specifier: &str,
        referrer: &str,
        _kind: ResolutionKind,
    ) -> Result<ModuleSpecifier, JsErrorBox> {
        // Handle file:// URLs directly
        if specifier.starts_with("file://") {
            return ModuleSpecifier::parse(specifier).map_err(|e| JsErrorBox::from_err(e));
        }

        // Handle relative paths
        if specifier.starts_with("./") || specifier.starts_with("../") {
            let referrer_url = ModuleSpecifier::parse(referrer)
                .unwrap_or_else(|_| {
                    ModuleSpecifier::from_file_path(&self.base_path)
                        .unwrap_or_else(|_| ModuleSpecifier::parse("file:///").unwrap())
                });

            let resolved = referrer_url
                .join(specifier)
                .map_err(|e| JsErrorBox::from_err(e))?;

            // Check if it exists, if not try adding .js extension
            if let Ok(path) = resolved.to_file_path() {
                if path.exists() {
                    return Ok(resolved);
                }
                // Try with .js
                let with_js = path.with_extension("js");
                if with_js.exists() {
                    return ModuleSpecifier::from_file_path(&with_js)
                        .map_err(|_| JsErrorBox::generic(format!("Invalid path: {:?}", with_js)));
                }
                // Try as directory with index.js
                let index = path.join("index.js");
                if index.exists() {
                    return ModuleSpecifier::from_file_path(&index)
                        .map_err(|_| JsErrorBox::generic(format!("Invalid path: {:?}", index)));
                }
            }

            return Ok(resolved);
        }

        // Handle absolute paths (Windows and Unix)
        if Path::new(specifier).is_absolute() {
            return ModuleSpecifier::from_file_path(specifier)
                .map_err(|_| JsErrorBox::generic(format!("Invalid file path: {}", specifier)));
        }

        // For node: specifiers, just return as-is (they're handled by deno_node)
        if specifier.starts_with("node:") {
            return ModuleSpecifier::parse(specifier).map_err(|e| JsErrorBox::from_err(e));
        }

        // For npm: specifiers
        if specifier.starts_with("npm:") {
            return ModuleSpecifier::parse(specifier).map_err(|e| JsErrorBox::from_err(e));
        }

        // Get the referrer's directory
        let referrer_dir = if referrer.starts_with("file://") {
            ModuleSpecifier::parse(referrer)
                .ok()
                .and_then(|u| u.to_file_path().ok())
                .and_then(|p| p.parent().map(|p| p.to_path_buf()))
        } else {
            None
        };

        let start_dir = referrer_dir
            .unwrap_or_else(|| Path::new(&self.base_path).to_path_buf());

        // Try to find in node_modules
        if let Some(resolved_path) = Self::find_in_node_modules(specifier, &start_dir) {
            return ModuleSpecifier::from_file_path(&resolved_path)
                .map_err(|_| JsErrorBox::generic(format!("Invalid path: {:?}", resolved_path)));
        }

        // Fallback: return as a relative path from base
        let full_path = Path::new(&self.base_path).join(specifier);
        ModuleSpecifier::from_file_path(&full_path)
            .map_err(|_| JsErrorBox::generic(format!("Cannot resolve module: {}", specifier)))
    }

    fn load(
        &self,
        module_specifier: &ModuleSpecifier,
        _maybe_referrer: Option<&deno_core::ModuleLoadReferrer>,
        _options: deno_core::ModuleLoadOptions,
    ) -> ModuleLoadResponse {
        let specifier = module_specifier.clone();

        // Handle file:// URLs
        if specifier.scheme() == "file" {
            let path = match specifier.to_file_path() {
                Ok(p) => p,
                Err(_) => {
                    return ModuleLoadResponse::Sync(Err(JsErrorBox::generic(format!(
                        "Invalid file URL: {}",
                        specifier
                    ))));
                }
            };

            // Read the file
            let code = match std::fs::read_to_string(&path) {
                Ok(c) => c,
                Err(e) => {
                    return ModuleLoadResponse::Sync(Err(JsErrorBox::generic(format!(
                        "Failed to read module {}: {}",
                        path.display(),
                        e
                    ))));
                }
            };

            // Determine module type based on extension
            let module_type = if path.extension().map(|e| e == "json").unwrap_or(false) {
                ModuleType::Json
            } else {
                ModuleType::JavaScript
            };

            return ModuleLoadResponse::Sync(Ok(ModuleSource::new(
                module_type,
                ModuleSourceCode::String(code.into()),
                &specifier,
                None,
            )));
        }

        // For other schemes, return error
        ModuleLoadResponse::Sync(Err(JsErrorBox::generic(format!(
            "Unsupported module scheme: {}",
            specifier.scheme()
        ))))
    }
}
