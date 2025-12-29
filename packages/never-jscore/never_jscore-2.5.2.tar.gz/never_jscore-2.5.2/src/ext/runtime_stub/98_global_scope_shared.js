// Minimal runtime stub for deno_node compatibility
// This provides the windowOrWorkerGlobalScope that deno_node's console.ts needs

import { Console } from "ext:deno_web/01_console.js";
import { core } from "ext:core/mod.js";

// Import deno_os modules to ensure they are evaluated and get exports
import * as denoOs from "ext:deno_os/30_os.js";
import "ext:deno_os/40_signals.js";

// Import deno_fs for cwd
import * as denoFs from "ext:deno_fs/30_fs.js";

// Create a minimal console instance
const consoleInstance = new Console((msg, level) => core.print(msg, level > 1));

// Set up Deno namespace if not exists
if (typeof globalThis.Deno === "undefined") {
  globalThis.Deno = {};
}

// Add deno_os exports to Deno namespace
globalThis.Deno.env = denoOs.env;
globalThis.Deno.exit = denoOs.exit;
globalThis.Deno.execPath = denoOs.execPath;
globalThis.Deno.hostname = denoOs.hostname;
globalThis.Deno.osRelease = denoOs.osRelease;
globalThis.Deno.loadavg = denoOs.loadavg;
globalThis.Deno.networkInterfaces = denoOs.networkInterfaces;
globalThis.Deno.systemMemoryInfo = denoOs.systemMemoryInfo;
globalThis.Deno.gid = denoOs.gid;
globalThis.Deno.uid = denoOs.uid;

// Add deno_fs exports to Deno namespace
globalThis.Deno.cwd = denoFs.cwd;
globalThis.Deno.chdir = denoFs.chdir;

// Add minimal version info
globalThis.Deno.version = {
  deno: "2.0.0",
  v8: "12.0.0",
  typescript: "5.0.0",
};

// Add args (empty array for compatibility)
globalThis.Deno.args = [];

// windowOrWorkerGlobalScope stub - only provides what deno_node needs
const windowOrWorkerGlobalScope = {
  console: {
    value: consoleInstance,
    writable: true,
    enumerable: false,
    configurable: true,
  },
};

export { windowOrWorkerGlobalScope };
