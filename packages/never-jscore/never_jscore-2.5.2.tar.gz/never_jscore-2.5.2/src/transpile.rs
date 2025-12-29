// TypeScript transpiler for deno_node extensions
// This module provides TypeScript transpilation for Node.js polyfills

#[cfg(feature = "node_compat")]
use std::path::Path;

#[cfg(feature = "node_compat")]
use deno_ast::MediaType;
#[cfg(feature = "node_compat")]
use deno_ast::ParseParams;
#[cfg(feature = "node_compat")]
use deno_ast::SourceMapOption;
#[cfg(feature = "node_compat")]
use deno_core::ModuleCodeString;
#[cfg(feature = "node_compat")]
use deno_core::ModuleName;
#[cfg(feature = "node_compat")]
use deno_core::SourceMapData;
#[cfg(feature = "node_compat")]
use deno_error::JsErrorBox;

/// Transpile TypeScript source code to JavaScript
///
/// This function handles:
/// - `node:*` modules (always treated as TypeScript)
/// - `.ts`, `.mts` files
/// - Regular JavaScript files are passed through unchanged
#[cfg(feature = "node_compat")]
pub fn maybe_transpile_source(
    name: ModuleName,
    source: ModuleCodeString,
) -> Result<(ModuleCodeString, Option<SourceMapData>), JsErrorBox> {
    // Always transpile `node:` built-in modules, since they might be TypeScript.
    let media_type = if name.starts_with("node:") || name.starts_with("ext:deno_node") {
        MediaType::TypeScript
    } else {
        MediaType::from_path(Path::new(&name))
    };

    match media_type {
        MediaType::TypeScript | MediaType::Mts => {}
        MediaType::JavaScript | MediaType::Mjs | MediaType::Cjs => return Ok((source, None)),
        // For unknown types, treat as JavaScript
        _ => return Ok((source, None)),
    }

    let parsed = deno_ast::parse_module(ParseParams {
        specifier: deno_core::url::Url::parse(&name).unwrap_or_else(|_| {
            deno_core::url::Url::parse(&format!("file:///{}", name)).unwrap()
        }),
        text: source.into(),
        media_type,
        capture_tokens: false,
        scope_analysis: false,
        maybe_syntax: None,
    })
    .map_err(|e| JsErrorBox::from_err(std::io::Error::new(
        std::io::ErrorKind::Other,
        format!("TypeScript parse error: {}", e)
    )))?;

    let transpiled_source = parsed
        .transpile(
            &deno_ast::TranspileOptions {
                imports_not_used_as_values: deno_ast::ImportsNotUsedAsValues::Remove,
                ..Default::default()
            },
            &deno_ast::TranspileModuleOptions::default(),
            &deno_ast::EmitOptions {
                source_map: SourceMapOption::None,
                ..Default::default()
            },
        )
        .map_err(|e| JsErrorBox::from_err(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("TypeScript transpile error: {}", e)
        )))?
        .into_source();

    let maybe_source_map: Option<SourceMapData> = transpiled_source
        .source_map
        .map(|sm| sm.into_bytes().into());
    let source_text = transpiled_source.text;
    Ok((source_text.into(), maybe_source_map))
}
