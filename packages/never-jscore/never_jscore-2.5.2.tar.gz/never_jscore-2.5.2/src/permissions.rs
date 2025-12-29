// Copyright never_jscore contributors. MIT license.
// Permissions system for Deno extensions integration
//
// In JS reverse engineering scenarios, we typically want full access
// to all APIs without restriction.

#[cfg(feature = "deno_web_api")]
use std::sync::Arc;
#[cfg(feature = "deno_web_api")]
use std::path::{Path, PathBuf};
#[cfg(feature = "deno_web_api")]
use std::borrow::Cow;
#[cfg(feature = "deno_web_api")]
use sys_traits;
#[cfg(feature = "deno_web_api")]
use deno_permissions::{
    PermissionsContainer, PermissionDescriptorParser,
    PathQueryDescriptor, PathDescriptor, ReadDescriptor, WriteDescriptor,
    NetDescriptor, EnvDescriptor, SysDescriptor,
    AllowRunDescriptor, DenyRunDescriptor, AllowRunDescriptorParseResult,
    RunDescriptorParseError, RunQueryDescriptor,
    FfiDescriptor, ImportDescriptor,
    SpecialFilePathQueryDescriptor,
    PathResolveError, NetDescriptorParseError, EnvDescriptorParseError,
    SysDescriptorParseError,
};

/// Simple PermissionDescriptorParser for reverse engineering scenarios
///
/// Returns descriptors that allow all operations without path resolution
#[cfg(feature = "deno_web_api")]
#[derive(Debug, Clone)]
struct AllowAllDescriptorParser;

#[cfg(feature = "deno_web_api")]
impl AllowAllDescriptorParser {
    /// Helper to create a PathDescriptor from a path string
    /// Uses new_known_absolute for simplicity - assumes all paths are absolute
    fn create_path_descriptor(&self, path: &str) -> PathDescriptor {
        PathDescriptor::new_known_absolute(Cow::Owned(PathBuf::from(path)))
    }
}

#[cfg(feature = "deno_web_api")]
impl PermissionDescriptorParser for AllowAllDescriptorParser {
    fn parse_read_descriptor(&self, text: &str) -> Result<ReadDescriptor, PathResolveError> {
        Ok(ReadDescriptor(self.create_path_descriptor(text)))
    }

    fn parse_write_descriptor(&self, text: &str) -> Result<WriteDescriptor, PathResolveError> {
        Ok(WriteDescriptor(self.create_path_descriptor(text)))
    }

    fn parse_net_descriptor(&self, text: &str) -> Result<NetDescriptor, NetDescriptorParseError> {
        // Use Deno's standard parsing method for consistency
        NetDescriptor::parse_for_list(text)
    }

    fn parse_import_descriptor(&self, text: &str) -> Result<ImportDescriptor, NetDescriptorParseError> {
        // Use Deno's standard parsing method for consistency
        ImportDescriptor::parse_for_list(text)
    }

    fn parse_env_descriptor(&self, text: &str) -> Result<EnvDescriptor, EnvDescriptorParseError> {
        Ok(EnvDescriptor::new(Cow::Borrowed(text)))
    }

    fn parse_sys_descriptor(&self, text: &str) -> Result<SysDescriptor, SysDescriptorParseError> {
        SysDescriptor::parse(text.to_string())
    }

    fn parse_allow_run_descriptor(&self, text: &str) -> Result<AllowRunDescriptorParseResult, RunDescriptorParseError> {
        Ok(AllowRunDescriptorParseResult::Descriptor(
            AllowRunDescriptor(self.create_path_descriptor(text))
        ))
    }

    fn parse_deny_run_descriptor(&self, text: &str) -> Result<DenyRunDescriptor, PathResolveError> {
        // If path contains separator, treat as path; otherwise as name
        if text.contains('/') || text.contains('\\') {
            Ok(DenyRunDescriptor::Path(self.create_path_descriptor(text)))
        } else {
            Ok(DenyRunDescriptor::Name(text.to_string()))
        }
    }

    fn parse_ffi_descriptor(&self, text: &str) -> Result<FfiDescriptor, PathResolveError> {
        Ok(FfiDescriptor(self.create_path_descriptor(text)))
    }

    fn parse_path_query<'a>(&self, path: Cow<'a, Path>) -> Result<PathQueryDescriptor<'a>, PathResolveError> {
        // Use the public constructor
        Ok(PathQueryDescriptor::new_known_absolute(path))
    }

    fn parse_net_query(&self, text: &str) -> Result<NetDescriptor, NetDescriptorParseError> {
        // Use Deno's query parsing method
        NetDescriptor::parse_for_query(text)
    }

    fn parse_run_query<'a>(&self, requested: &'a str) -> Result<RunQueryDescriptor<'a>, RunDescriptorParseError> {
        // Use Deno's standard RunQueryDescriptor::parse with RealSys
        RunQueryDescriptor::parse(requested, &sys_traits::impls::RealSys)
            .map_err(Into::into)
    }

    fn parse_special_file_descriptor<'a>(&self, path: PathQueryDescriptor<'a>) -> Result<SpecialFilePathQueryDescriptor<'a>, PathResolveError> {
        // Use the public parse method with RealSys
        SpecialFilePathQueryDescriptor::parse(&sys_traits::impls::RealSys, path)
    }
}

/// Create a fully permissive PermissionsContainer
///
/// This allows all operations without any permission checks,
/// which is appropriate for JavaScript reverse engineering scenarios
/// where we want to analyze and execute arbitrary JavaScript code.
#[cfg(feature = "deno_web_api")]
pub fn create_allow_all_permissions() -> PermissionsContainer {
    let parser: Arc<dyn PermissionDescriptorParser> = Arc::new(AllowAllDescriptorParser);
    PermissionsContainer::allow_all(parser)
}
