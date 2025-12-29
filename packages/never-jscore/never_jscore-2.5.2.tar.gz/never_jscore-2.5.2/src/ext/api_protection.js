/**
 * API Protection Utilities - Deprecated
 *
 * NOTE: All protection logic has been moved to init_protection.js
 * This file is kept for backward compatibility only.
 *
 * Do not use these functions directly - they are no-ops.
 * Protection is applied automatically by init_protection.js.
 */

// No-op functions for backward compatibility
const makeNative = (fn) => fn;
const makeAllNative = (obj) => obj;
const protectConstructor = (c) => c;
const hideProperty = () => {};
const freezeProperty = () => {};
const hideDeno = () => {};
const createNativeProxy = (target, handler) => new Proxy(target, handler);
const deepProtect = (obj) => Object.freeze(obj);
const cleanStack = (error) => error;

// No-op descriptor helpers
const nonEnumerable = (value) => ({ value, enumerable: false });
const readOnly = (value) => ({ value, writable: false });
const writeable = (value) => ({ value, writable: true });
const getterOnly = (getter) => ({ get: getter });
const applyToGlobal = () => {};
const applyToDeno = () => {};

const ObjectProperties = {
    nonEnumerable: { writable: true, enumerable: false, configurable: true },
    readOnly: { writable: false, enumerable: false, configurable: true },
    writeable: { writable: true, enumerable: true, configurable: true },
    getterOnly: { enumerable: true, configurable: true },
};

// Export all (for backward compatibility)
export {
    nonEnumerable,
    readOnly,
    writeable,
    getterOnly,
    applyToGlobal,
    applyToDeno,
    makeNative,
    makeAllNative,
    protectConstructor,
    hideProperty,
    freezeProperty,
    hideDeno,
    createNativeProxy,
    deepProtect,
    cleanStack,
    ObjectProperties
};
