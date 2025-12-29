/**
 * Core never_jscore functionality
 * Provides basic operations for result storage and early return
 */

/**
 * Store result to Rust side
 * @param {any} value - Value to store (will be JSON stringified)
 */
function $storeResult(value) {
    const jsonData = JSON.stringify(value);
    Deno.core.ops.op_store_result(jsonData);
}

/**
 * Early return with value (Legacy version using throw error)
 *
 * This version can be caught by try-catch blocks.
 * For uncatchable termination, use $terminate() from hook extension.
 *
 * @param {any} value - Value to return
 *
 * @example
 * // Hook and return early (can be caught by try-catch)
 * function processData(data) {
 *     if (data.secret) {
 *         $return({ intercepted: data.secret });
 *     }
 *     return normalProcess(data);
 * }
 */
function $return(value) {
    const jsonData = JSON.stringify(value);
    Deno.core.ops.op_early_return(jsonData);
    // Throw special error to interrupt execution
    throw new Error('[NEVER_JSCORE_EARLY_RETURN]' + jsonData);
}

/**
 * Exit execution with value (alias for $return)
 */
function $exit(value) {
    $return(value);
}

/**
 * Alias for backward compatibility
 */
function __neverjscore_return__(value) {
    $return(value);
}

// Make functions globally available
globalThis.$storeResult = $storeResult;
globalThis.$return = $return;
globalThis.$exit = $exit;
globalThis.__neverjscore_return__ = __neverjscore_return__;
