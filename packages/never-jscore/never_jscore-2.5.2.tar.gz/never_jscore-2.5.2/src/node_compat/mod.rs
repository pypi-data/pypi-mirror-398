// Node.js compatibility layer for never-jscore
// Full deno_node integration for complete Node.js built-in modules support

use deno_core::Extension;
use std::path::PathBuf;
use std::rc::Rc;

#[cfg(feature = "node_compat")]
use deno_fs::sync::MaybeArc;

mod node_require_loader;
mod npm_checker;

pub use node_require_loader::NeverJsCoreRequireLoader;
pub use npm_checker::{NeverJsCoreNpmPackageChecker, NeverJsCoreNpmPackageFolderResolver};

/// Node.js compatibility layer configuration
#[derive(Clone, Debug)]
pub struct NodeCompatOptions {
    /// Path to node_modules directory
    pub node_modules_path: Option<PathBuf>,
    /// Current working directory for module resolution
    pub cwd: PathBuf,
}

impl Default for NodeCompatOptions {
    fn default() -> Self {
        Self {
            node_modules_path: Some(PathBuf::from("./node_modules")),
            cwd: std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")),
        }
    }
}

/// Create Node.js compatibility extensions
///
/// This function creates extensions for:
/// - deno_io (stdin/stdout/stderr)
/// - deno_fs (file system operations)
/// - deno_node (Node.js built-in modules and require())
#[cfg(feature = "node_compat")]
pub fn create_node_extensions(
    options: NodeCompatOptions,
    fs: deno_fs::FileSystemRc,
) -> Vec<Extension> {
    use deno_node::{NodeExtInitServices, NodeRequireLoaderRc};
    use node_resolver::{PackageJsonResolver, DenoIsBuiltInNodeModuleChecker};
    use node_resolver::cache::NodeResolutionSys;
    use sys_traits::impls::RealSys;

    let mut extensions = vec![];

    // Create the system implementation using RealSys
    let sys = RealSys;

    // Create NodeResolutionSys wrapper (with optional caching)
    let node_resolution_sys = NodeResolutionSys::new(sys.clone(), None);

    // Create package.json resolver
    let pkg_json_resolver: node_resolver::PackageJsonResolverRc<RealSys> =
        MaybeArc::new(PackageJsonResolver::new(sys.clone(), None));

    // Create npm package checker and folder resolver
    let npm_package_checker = NeverJsCoreNpmPackageChecker::default();
    let npm_folder_resolver = NeverJsCoreNpmPackageFolderResolver::new(options.node_modules_path.clone());

    // Create builtin module checker
    let builtin_checker = DenoIsBuiltInNodeModuleChecker;

    // Create the node resolver with correct type parameters
    let node_resolver: MaybeArc<deno_node::NodeResolver<
        NeverJsCoreNpmPackageChecker,
        NeverJsCoreNpmPackageFolderResolver,
        RealSys,
    >> = MaybeArc::new(node_resolver::NodeResolver::new(
        npm_package_checker.clone(),
        builtin_checker,
        npm_folder_resolver.clone(),
        pkg_json_resolver.clone(),
        node_resolution_sys,
        node_resolver::NodeResolverOptions::default(),
    ));

    // Create require loader
    let node_require_loader: NodeRequireLoaderRc = Rc::new(NeverJsCoreRequireLoader);

    // Create init services
    let node_init_services = NodeExtInitServices {
        node_require_loader,
        node_resolver,
        pkg_json_resolver,
        sys: sys.clone(),
    };

    // Add IO stubs extension first (provides op_set_raw stub for deno_io)
    extensions.push(crate::ext::never_jscore_io_stubs::init());

    // Add node ops stubs (provides missing ops like op_bootstrap_color_depth)
    extensions.push(crate::ext::node_ops_stub::never_jscore_node_ops::init());

    // Add deno_io extension (required by deno_node)
    // The extension! macro generates init(options) function
    extensions.push(deno_io::deno_io::init(
        Some(deno_io::Stdio::default()),
    ));

    // Add deno_fs extension (required by deno_node)
    extensions.push(deno_fs::deno_fs::init(fs.clone()));

    // Add deno_os extension (required by deno_process and deno_node)
    extensions.push(deno_os::deno_os::init(None));

    // Add deno_process extension (required by deno_node)
    extensions.push(deno_process::deno_process::init(None));

    // Add runtime stub extension (provides ext:runtime/98_global_scope_shared.js for deno_node)
    extensions.push(crate::ext::runtime_stub::init());

    // Add HTTP stub extension (provides ext:deno_http/00_serve.ts stub for deno_node)
    extensions.push(crate::ext::http_stub::init());

    // Add deno_node extension
    extensions.push(deno_node::deno_node::init::<
        NeverJsCoreNpmPackageChecker,
        NeverJsCoreNpmPackageFolderResolver,
        RealSys,
    >(
        Some(node_init_services),
        fs,
    ));

    // Add node initialization extension (sets up global require, etc.)
    extensions.push(crate::ext::node_init::init());

    extensions
}

/// Create Node.js compatibility extensions without deno_node
/// Uses our custom require.js polyfill instead
#[cfg(not(feature = "node_compat"))]
pub fn create_node_extensions(_options: NodeCompatOptions) -> Vec<Extension> {
    vec![]
}
