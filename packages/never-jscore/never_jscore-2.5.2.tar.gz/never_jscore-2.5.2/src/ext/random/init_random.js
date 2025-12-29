// Override Math.random() to use seeded RNG
// This allows deterministic random number generation for debugging

(() => {
    if (typeof Math !== 'undefined' && typeof Deno !== 'undefined' && Deno.core && Deno.core.ops.op_crypto_random) {
        const originalMathRandom = Math.random;

        Math.random = function() {
            try {
                // Use seeded RNG if available
                return Deno.core.ops.op_crypto_random();
            } catch (e) {
                // Fallback to original if op fails
                return originalMathRandom.call(Math);
            }
        };
    }
})();
