// Initialize Node.js globals for never-jscore
// This runs after deno_node is loaded to set up require() globally

import { internals, primordials } from "ext:core/mod.js";
import { createRequire } from "node:module";
import { op_fs_cwd } from "ext:core/ops";

// Get the requireImpl from internals (before it's deleted by initialize)
const requireImpl = internals.requireImpl;

// Set up that we're using local node_modules
if (requireImpl && typeof requireImpl.setUsesLocalNodeModulesDir === "function") {
  requireImpl.setUsesLocalNodeModulesDir();
}

// Initialize the Node.js runtime if available
// This sets up process, Buffer, setTimeout, etc.
if (internals.node && typeof internals.node.initialize === "function") {
  try {
    internals.node.initialize({
      usesLocalNodeModulesDir: true,  // We use local node_modules
      argv0: "never-jscore",
      runningOnMainThread: true,
      workerId: null,
      maybeWorkerMetadata: null,
      nodeDebug: "",
      warmup: false,
      moduleSpecifier: null,
    });
  } catch (e) {
    // Ignore initialization errors - we'll set up what we can manually
    // console.log("Node bootstrap error:", e.message);
  }
}

// Create a global require function based on current working directory
const cwd = op_fs_cwd();
const requireFromCwd = createRequire(cwd + "/");

// Expose require globally
globalThis.require = requireFromCwd;

// Also expose module for compatibility
globalThis.module = {
  exports: {},
  id: ".",
  path: cwd,
  filename: cwd + "/index.js",
  loaded: false,
  children: [],
  paths: requireFromCwd.resolve.paths(".") || [],
};

// Export __dirname and __filename based on CWD
globalThis.__dirname = cwd;
globalThis.__filename = cwd + "/index.js";
