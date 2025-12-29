/**
 * Hook support for JS termination and data interception
 * Inspired by rustyscript's hook system
 */

/**
 * Save data and terminate JS execution (Enhanced version)
 *
 * This function uses V8's terminate_execution() which CANNOT be caught by try-catch.
 * This is the recommended method for hook interception in hardened code.
 *
 * @param {any} data - Data to save (will be JSON stringified)
 *
 * @example
 * // Hook encryption function and extract key
 * const original = CryptoLib.encrypt;
 * CryptoLib.encrypt = function(text, key) {
 *     $terminate({ text, key });  // Uncatchable termination
 * };
 */
function $terminate(data) {
    const jsonData = JSON.stringify(data);
    Deno.core.ops.op_save_hook_data(jsonData);
    Deno.core.ops.op_terminate_execution();
}

/**
 * Alias for $terminate (for backward compatibility)
 */
function __saveAndTerminate__(data) {
    $terminate(data);
}

// Make functions globally available
globalThis.$terminate = $terminate;
globalThis.__saveAndTerminate__ = __saveAndTerminate__;
