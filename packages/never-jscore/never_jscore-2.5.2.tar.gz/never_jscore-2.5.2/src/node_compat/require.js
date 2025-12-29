// Complete Node.js require() implementation for never-jscore
// Supports: local modules, npm packages, node_modules resolution, package.json

(() => {
    'use strict';

    const { core } = globalThis.__bootstrap;
    const ops = core.ops;

    // Create minimal process object if it doesn't exist
    if (typeof globalThis.process === 'undefined') {
        globalThis.process = {
            mainModule: null,
            env: {},
            platform: 'never-jscore',
            version: 'v2.5.0',
            versions: {},
            arch: 'x64',
            cwd: () => ops.op_get_cwd(),
        };
    }

    // Module cache: filename -> module
    const Module =  {
        _cache: {},
        _pathCache: {},
        _extensions: {},
        _resolving: {},

        // Built-in modules (only those we have polyfills for)
        // Other modules will be loaded from node_modules if available
        _builtins: new Set([
            'buffer', 'events', 'fs', 'path', 'stream', 'tty', 'util', 'vm'
        ]),
    };

    // Module constructor
    function createModule(filename, parent) {
        const module = {
            id: filename,
            filename,
            loaded: false,
            parent,
            children: [],
            exports: {},
            paths: Module._nodeModulePaths(filename),
            require: null,  // Will be set later
        };

        // Add _compile method to each module instance
        module._compile = function(content, filename) {
            // Remove shebang
            content = content.replace(/^#!.*/, '');

            // Wrap in CommonJS wrapper
            const wrapper = Module.wrap(content);

            // Compile
            const compiledWrapper = eval('(function() { return ' + wrapper + ' })()');

            // Prepare arguments
            const dirname = filename.split('/').slice(0, -1).join('/');
            const require = makeRequire(module);
            const exports = module.exports;

            // Execute
            compiledWrapper.call(exports, exports, require, module, filename, dirname);
        };

        return module;
    }

    // Main require function
    function makeRequire(module) {
        function require(id) {
            return Module._load(id, module);
        }

        function resolve(request, options) {
            return Module._resolveFilename(request, module);
        }

        function paths(request) {
            return Module._resolveLookupPaths(request, module);
        }

        require.resolve = resolve;
        require.paths = paths;
        require.main = process.mainModule;
        require.extensions = Module._extensions;
        require.cache = Module._cache;

        return require;
    }

    // Resolve module filename
    Module._resolveFilename = function(request, parent) {
        // Check cache first
        const cacheKey = request + '\x00' + (parent ? parent.filename : '');
        if (Module._pathCache[cacheKey]) {
            return Module._pathCache[cacheKey];
        }

        // Built-in module check
        if (Module._builtins.has(request)) {
            return request;
        }

        // Resolve the path
        const filename = Module._findPath(request, parent);
        if (!filename) {
            const err = new Error(`Cannot find module '${request}'`);
            err.code = 'MODULE_NOT_FOUND';
            throw err;
        }

        Module._pathCache[cacheKey] = filename;
        return filename;
    };

    // Find module path
    Module._findPath = function(request, parent) {
        const paths = Module._resolveLookupPaths(request, parent);

        // Try to resolve as file first
        for (const basePath of paths) {
            const filename = Module._resolveAsFile(basePath, request);
            if (filename) return filename;

            const dirFilename = Module._resolveAsDirectory(basePath, request);
            if (dirFilename) return dirFilename;
        }

        return null;
    };

    // Resolve as file
    Module._resolveAsFile = function(basePath, request) {
        let filename = ops.op_resolve_path(basePath, request);

        // Try exact match
        if (ops.op_file_exists(filename) && ops.op_is_file(filename)) {
            return filename;
        }

        // Try with extensions
        const extensions = ['.js', '.json', '.node'];
        for (const ext of extensions) {
            const fileWithExt = filename + ext;
            if (ops.op_file_exists(fileWithExt) && ops.op_is_file(fileWithExt)) {
                return fileWithExt;
            }
        }

        return null;
    };

    // Resolve as directory
    Module._resolveAsDirectory = function(basePath, request) {
        const dirname = ops.op_resolve_path(basePath, request);

        if (!ops.op_is_directory(dirname)) {
            return null;
        }

        // Try package.json
        try {
            const pkg = ops.op_read_package_json(dirname);
            if (pkg && pkg.main) {
                const mainPath = ops.op_resolve_path(dirname, pkg.main);
                const resolved = Module._resolveAsFile(dirname, pkg.main);
                if (resolved) return resolved;
            }
        } catch (e) {
            // No package.json or invalid, continue
        }

        // Try index files
        const indexFiles = ['index.js', 'index.json', 'index.node'];
        for (const indexFile of indexFiles) {
            const indexPath = ops.op_resolve_path(dirname, indexFile);
            if (ops.op_file_exists(indexPath) && ops.op_is_file(indexPath)) {
                return indexPath;
            }
        }

        return null;
    };

    // Get node_modules lookup paths
    Module._resolveLookupPaths = function(request, parent) {
        // Absolute path
        if (request.startsWith('/')) {
            return ['/'];
        }

        // Relative path
        if (request.startsWith('./') || request.startsWith('../')) {
            const parentDir = parent ?
                (ops.op_is_directory(parent.filename) ? parent.filename : parent.filename.split('/').slice(0, -1).join('/')) :
                ops.op_get_cwd();
            return [parentDir];
        }

        // Module name - search in node_modules
        return Module._nodeModulePaths(parent ? parent.filename : ops.op_get_cwd());
    };

    // Generate node_modules paths
    Module._nodeModulePaths = function(from) {
        const paths = [];
        let current = from;

        while (current && current !== '/') {
            if (!current.endsWith('/node_modules')) {
                const nodeModulesPath = current + '/node_modules';
                paths.push(nodeModulesPath);
            }
            const parent = current.split('/').slice(0, -1).join('/');
            if (parent === current) break;
            current = parent;
        }

        // Add global node_modules
        paths.push(ops.op_get_cwd() + '/node_modules');

        return paths;
    };

    // Load module
    Module._load = function(request, parent) {
        const filename = Module._resolveFilename(request, parent);

        // Check cache
        const cachedModule = Module._cache[filename];
        if (cachedModule) {
            return cachedModule.exports;
        }

        // Built-in module
        if (Module._builtins.has(filename)) {
            return Module._loadBuiltin(filename);
        }

        // Check for circular dependency
        if (Module._resolving[filename]) {
            const module = Module._cache[filename];
            return module ? module.exports : {};
        }

        // Create new module
        const module = createModule(filename, parent);
        Module._cache[filename] = module;
        Module._resolving[filename] = true;

        try {
            // Load the module
            module.require = makeRequire(module);
            Module._extensions[getExtension(filename)](module, filename);
            module.loaded = true;
        } catch (err) {
            delete Module._cache[filename];
            throw err;
        } finally {
            delete Module._resolving[filename];
        }

        return module.exports;
    };

    // Load built-in module with polyfill implementations
    Module._loadBuiltin = function(name) {
        // Provide polyfill implementations for common Node.js built-in modules
        // These use deno APIs and Web standards where possible

        switch (name) {
            case 'path':
                return Module._createPathModule();
            case 'buffer':
                return Module._createBufferModule();
            case 'fs':
                return Module._createFsModule();
            case 'vm':
                return Module._createVmModule();
            case 'util':
                return Module._createUtilModule();
            case 'events':
                return Module._createEventsModule();
            case 'stream':
                return Module._createStreamModule();
            case 'tty':
                return Module._createTtyModule();
            default:
                console.warn(`[never-jscore] Built-in module '${name}' requested but not available`);
                return {};
        }
    };

    // Path module polyfill (pure JavaScript implementation)
    Module._createPathModule = function() {
        const path = {
            sep: '/',
            delimiter: ':',

            normalize: function(p) {
                if (!p) return '.';
                const isAbsolute = p.startsWith('/');
                const parts = p.split('/').filter(x => x && x !== '.');
                const result = [];
                for (const part of parts) {
                    if (part === '..') {
                        if (result.length > 0 && result[result.length - 1] !== '..') {
                            result.pop();
                        } else if (!isAbsolute) {
                            result.push('..');
                        }
                    } else {
                        result.push(part);
                    }
                }
                return (isAbsolute ? '/' : '') + result.join('/') || '.';
            },

            join: function(...args) {
                return path.normalize(args.filter(x => x).join('/'));
            },

            resolve: function(...args) {
                let resolved = '';
                for (let i = args.length - 1; i >= 0; i--) {
                    const p = args[i];
                    if (!p) continue;
                    resolved = p + '/' + resolved;
                    if (p.startsWith('/')) break;
                }
                return path.normalize(resolved || ops.op_get_cwd());
            },

            dirname: function(p) {
                const idx = p.lastIndexOf('/');
                return idx === -1 ? '.' : p.substring(0, idx) || '/';
            },

            basename: function(p, ext) {
                const idx = p.lastIndexOf('/');
                let base = idx === -1 ? p : p.substring(idx + 1);
                if (ext && base.endsWith(ext)) {
                    base = base.substring(0, base.length - ext.length);
                }
                return base;
            },

            extname: function(p) {
                const idx = p.lastIndexOf('.');
                const sepIdx = p.lastIndexOf('/');
                return (idx > sepIdx) ? p.substring(idx) : '';
            }
        };
        return path;
    };

    // Buffer module polyfill (based on Uint8Array)
    Module._createBufferModule = function() {
        function Buffer(arg, encodingOrOffset, length) {
            if (typeof arg === 'number') {
                return new Uint8Array(arg);
            } else if (typeof arg === 'string') {
                const encoding = encodingOrOffset || 'utf8';
                if (encoding === 'utf8' || encoding === 'utf-8') {
                    const encoder = new TextEncoder();
                    return encoder.encode(arg);
                } else if (encoding === 'base64') {
                    return Uint8Array.from(atob(arg), c => c.charCodeAt(0));
                }
            } else if (arg instanceof ArrayBuffer || Array.isArray(arg)) {
                return new Uint8Array(arg);
            }
            return new Uint8Array(0);
        }

        Buffer.from = function(value, encoding) {
            return Buffer(value, encoding);
        };

        Buffer.alloc = function(size, fill) {
            const buf = new Uint8Array(size);
            if (fill !== undefined) {
                buf.fill(fill);
            }
            return buf;
        };

        Buffer.allocUnsafe = function(size) {
            return new Uint8Array(size);
        };

        Buffer.isBuffer = function(obj) {
            return obj instanceof Uint8Array;
        };

        Buffer.concat = function(list, totalLength) {
            const length = totalLength !== undefined ? totalLength :
                list.reduce((acc, buf) => acc + buf.length, 0);
            const result = new Uint8Array(length);
            let offset = 0;
            for (const buf of list) {
                result.set(buf, offset);
                offset += buf.length;
            }
            return result;
        };

        return { Buffer };
    };

    // Fs module polyfill (using our ops)
    Module._createFsModule = function() {
        const { Buffer } = Module._createBufferModule();

        // Sync methods
        const fs = {
            readFileSync: function(path, options) {
                const encoding = typeof options === 'string' ? options : options?.encoding;
                const content = ops.op_read_file_sync(path);
                return encoding ? content : Buffer(content, 'utf8');
            },

            existsSync: function(path) {
                return ops.op_file_exists(path);
            },

            statSync: function(path) {
                const isFile = ops.op_is_file(path);
                const isDir = ops.op_is_directory(path);
                return {
                    isFile: () => isFile,
                    isDirectory: () => isDir,
                    isSymbolicLink: () => false,
                };
            },

            readdirSync: function(path) {
                // Not implemented - would need deno_fs ops
                return [];
            },

            // Promise-based methods (for jsdom compatibility)
            promises: {
                readFile: function(path, options) {
                    return Promise.resolve().then(() => {
                        const encoding = typeof options === 'string' ? options : options?.encoding;
                        const content = ops.op_read_file_sync(path);
                        return encoding ? content : Buffer(content, 'utf8');
                    });
                },

                stat: function(path) {
                    return Promise.resolve().then(() => {
                        const isFile = ops.op_is_file(path);
                        const isDir = ops.op_is_directory(path);
                        return {
                            isFile: () => isFile,
                            isDirectory: () => isDir,
                            isSymbolicLink: () => false,
                        };
                    });
                },

                readdir: function(path) {
                    return Promise.resolve([]);
                }
            }
        };

        return fs;
    };

    // Vm module polyfill (using eval - unsafe but works for jsdom)
    Module._createVmModule = function() {
        const vm = {
            runInContext: function(code, context) {
                // Simple implementation using eval
                // Not sandboxed but sufficient for jsdom
                return eval(code);
            },

            createContext: function(context) {
                return context || {};
            },

            runInNewContext: function(code, context) {
                return vm.runInContext(code, vm.createContext(context));
            },

            Script: function(code) {
                this.code = code;
            }
        };

        vm.Script.prototype.runInContext = function(context) {
            return vm.runInContext(this.code, context);
        };

        vm.Script.prototype.runInNewContext = function(context) {
            return vm.runInNewContext(this.code, context);
        };

        return vm;
    };

    // Util module polyfill
    Module._createUtilModule = function() {
        const util = {
            inherits: function(constructor, superConstructor) {
                constructor.super_ = superConstructor;
                constructor.prototype = Object.create(superConstructor.prototype, {
                    constructor: {
                        value: constructor,
                        enumerable: false,
                        writable: true,
                        configurable: true
                    }
                });
            },

            inspect: function(obj) {
                return JSON.stringify(obj, null, 2);
            },

            deprecate: function(fn, msg) {
                let warned = false;
                return function deprecated() {
                    if (!warned) {
                        console.warn('DeprecationWarning:', msg);
                        warned = true;
                    }
                    return fn.apply(this, arguments);
                };
            },

            format: function(fmt, ...args) {
                let i = 0;
                return fmt.replace(/%[sdj%]/g, (match) => {
                    if (match === '%%') return '%';
                    if (i >= args.length) return match;
                    const arg = args[i++];
                    switch (match) {
                        case '%s': return String(arg);
                        case '%d': return Number(arg);
                        case '%j': return JSON.stringify(arg);
                        default: return match;
                    }
                });
            }
        };
        return util;
    };

    // Events module polyfill
    Module._createEventsModule = function() {
        class EventEmitter {
            constructor() {
                this._events = {};
            }

            on(event, listener) {
                if (!this._events[event]) this._events[event] = [];
                this._events[event].push(listener);
                return this;
            }

            once(event, listener) {
                const wrapped = (...args) => {
                    this.off(event, wrapped);
                    listener.apply(this, args);
                };
                return this.on(event, wrapped);
            }

            off(event, listener) {
                if (!this._events[event]) return this;
                this._events[event] = this._events[event].filter(l => l !== listener);
                return this;
            }

            emit(event, ...args) {
                if (!this._events[event]) return false;
                this._events[event].forEach(listener => {
                    try {
                        listener.apply(this, args);
                    } catch (err) {
                        console.error('Error in event listener:', err);
                    }
                });
                return true;
            }

            removeAllListeners(event) {
                if (event) {
                    delete this._events[event];
                } else {
                    this._events = {};
                }
                return this;
            }
        }

        return { EventEmitter };
    };

    // Stream module polyfill (basic implementation)
    Module._createStreamModule = function() {
        const { EventEmitter } = Module._createEventsModule();

        class Readable extends EventEmitter {
            constructor() {
                super();
                this.readable = true;
            }

            pipe(dest) {
                this.on('data', chunk => dest.write(chunk));
                this.on('end', () => dest.end && dest.end());
                return dest;
            }
        }

        class Writable extends EventEmitter {
            constructor() {
                super();
                this.writable = true;
            }

            write(chunk) {
                this.emit('data', chunk);
                return true;
            }

            end() {
                this.emit('end');
            }
        }

        return { Readable, Writable, Stream: Readable };
    };

    // TTY module polyfill (minimal implementation)
    Module._createTtyModule = function() {
        const tty = {
            isatty: function(fd) {
                // Always return false in never-jscore environment
                return false;
            },
            ReadStream: class ReadStream {},
            WriteStream: class WriteStream {}
        };
        return tty;
    };

    // Get file extension
    function getExtension(filename) {
        const lastDot = filename.lastIndexOf('.');
        const lastSlash = Math.max(filename.lastIndexOf('/'), filename.lastIndexOf('\\'));

        // If no dot, or dot is before the last slash (part of directory name), default to .js
        if (lastDot === -1 || lastDot < lastSlash) {
            return '.js';
        }

        const ext = filename.substring(lastDot);
        // Only return if it's a known extension, otherwise default to .js
        if (Module._extensions[ext]) {
            return ext;
        }
        return '.js';
    }

    // Extension loaders
    Module._extensions['.js'] = function(module, filename) {
        const content = ops.op_read_file_sync(filename);
        module._compile(content, filename);
    };

    Module._extensions['.json'] = function(module, filename) {
        const content = ops.op_read_file_sync(filename);
        try {
            module.exports = JSON.parse(content);
        } catch (err) {
            err.message = filename + ': ' + err.message;
            throw err;
        }
    };

    Module._extensions['.node'] = function(module, filename) {
        throw new Error('Native addons (.node) are not supported in never-jscore');
    };

    // Wrap code in CommonJS format
    Module.wrap = function(script) {
        return Module.wrapper[0] + script + Module.wrapper[1];
    };

    Module.wrapper = [
        '(function (exports, require, module, __filename, __dirname) { ',
        '\n});'
    ];

    // Global require function
    const mainModule = createModule(ops.op_get_cwd() + '/[eval]', null);
    mainModule.require = makeRequire(mainModule);

    function require(id) {
        return Module._load(id, mainModule);
    }

    require.resolve = function(request) {
        return Module._resolveFilename(request, mainModule);
    };

    require.cache = Module._cache;
    require.extensions = Module._extensions;
    require.main = mainModule;

    // Export to global scope
    globalThis.require = require;
    globalThis.module = mainModule;
    globalThis.exports = mainModule.exports;

    // Also set process.mainModule
    if (typeof process !== 'undefined') {
        process.mainModule = mainModule;
    }

    // NOTE: console.log removed - causes "Bad resource ID" error
    // This happens because console depends on resources that may not be initialized yet
    // console.log('[never-jscore] Node.js require() system initialized');
})();
