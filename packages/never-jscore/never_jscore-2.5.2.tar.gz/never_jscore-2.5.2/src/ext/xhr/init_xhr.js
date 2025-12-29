// XMLHttpRequest polyfill based on fetch API
// Provides browser-compatible XMLHttpRequest for reverse engineering

(() => {
    'use strict';

    // Dependency check: XMLHttpRequest requires fetch API
    if (typeof fetch === 'undefined') {
        console.error('[never-jscore] XMLHttpRequest requires fetch API');
        console.error('[never-jscore] Make sure deno_web_api feature is enabled');
        // Don't throw, just skip initialization
        return;
    }

    // XMLHttpRequest ready states
    const UNSENT = 0;
    const OPENED = 1;
    const HEADERS_RECEIVED = 2;
    const LOADING = 3;
    const DONE = 4;

    class XMLHttpRequest {
        constructor() {
            // State
            this.readyState = UNSENT;
            this.status = 0;
            this.statusText = '';
            this.responseText = '';
            this.responseXML = null;
            this.response = '';
            this.responseType = '';
            this.responseURL = '';

            // Headers
            this._requestHeaders = {};
            this._headers = this._requestHeaders;  // Alias for compatibility
            this._responseHeaders = {};

            // Request config
            this._method = '';
            this._url = '';
            this._async = true;
            this._user = null;
            this._password = null;

            // Event handlers
            this.onreadystatechange = null;
            this.onload = null;
            this.onerror = null;
            this.onprogress = null;
            this.onloadstart = null;
            this.onloadend = null;
            this.ontimeout = null;
            this.onabort = null;

            // Timeout
            this.timeout = 0;
            this._timedOut = false;

            // Instance constants (for compatibility)
            this.UNSENT = UNSENT;
            this.OPENED = OPENED;
            this.HEADERS_RECEIVED = HEADERS_RECEIVED;
            this.LOADING = LOADING;
            this.DONE = DONE;

            // Abort
            this._aborted = false;
            this._abortController = null;
        }

        // Open the request
        open(method, url, async = true, user = null, password = null) {
            this._method = method.toUpperCase();
            this._url = url;
            this._async = async;
            this._user = user;
            this._password = password;

            this.readyState = OPENED;
            this._dispatchEvent('readystatechange');
        }

        // Set request header
        setRequestHeader(name, value) {
            if (this.readyState !== OPENED) {
                throw new Error('InvalidStateError: setRequestHeader can only be called after open()');
            }
            this._requestHeaders[name] = value;
        }

        // Send the request
        send(body = null) {
            if (this.readyState !== OPENED) {
                throw new Error('InvalidStateError: send can only be called after open()');
            }

            // Fire loadstart event
            this._dispatchEvent('loadstart');

            // Create AbortController for timeout and manual abort
            this._abortController = new AbortController();

            // Setup timeout
            let timeoutId = null;
            if (this.timeout > 0) {
                timeoutId = setTimeout(() => {
                    this._timedOut = true;
                    this._abortController.abort();
                    this._dispatchEvent('timeout');
                }, this.timeout);
            }

            // Prepare fetch options
            const options = {
                method: this._method,
                headers: this._requestHeaders,
                signal: this._abortController.signal
            };

            // Add body if present
            if (body !== null && this._method !== 'GET' && this._method !== 'HEAD') {
                options.body = body;
            }

            // Add basic auth if provided
            if (this._user) {
                const credentials = btoa(`${this._user}:${this._password || ''}`);
                options.headers['Authorization'] = `Basic ${credentials}`;
            }

            // Perform the fetch
            fetch(this._url, options)
                .then(response => {
                    if (timeoutId) clearTimeout(timeoutId);

                    // Store response metadata
                    this.status = response.status;
                    this.statusText = response.statusText;
                    this.responseURL = response.url;

                    // Parse response headers
                    response.headers.forEach((value, name) => {
                        this._responseHeaders[name.toLowerCase()] = value;
                    });

                    // Update state to HEADERS_RECEIVED
                    this.readyState = HEADERS_RECEIVED;
                    this._dispatchEvent('readystatechange');

                    // Update state to LOADING
                    this.readyState = LOADING;
                    this._dispatchEvent('readystatechange');
                    this._dispatchEvent('progress');

                    // Get response body based on responseType
                    if (this.responseType === 'arraybuffer') {
                        return response.arrayBuffer();
                    } else if (this.responseType === 'blob') {
                        return response.blob();
                    } else if (this.responseType === 'json') {
                        return response.json();
                    } else {
                        return response.text();
                    }
                })
                .then(data => {
                    if (timeoutId) clearTimeout(timeoutId);

                    // Store response
                    if (this.responseType === 'json') {
                        this.response = data;
                        this.responseText = JSON.stringify(data);
                    } else if (this.responseType === 'arraybuffer' || this.responseType === 'blob') {
                        this.response = data;
                        this.responseText = '';
                    } else {
                        this.response = data;
                        this.responseText = data;
                    }

                    // Update state to DONE
                    this.readyState = DONE;
                    this._dispatchEvent('readystatechange');
                    this._dispatchEvent('load');
                    this._dispatchEvent('loadend');
                })
                .catch(error => {
                    if (timeoutId) clearTimeout(timeoutId);

                    if (this._aborted) {
                        this._dispatchEvent('abort');
                    } else if (this._timedOut) {
                        // Timeout event already fired
                    } else {
                        this._dispatchEvent('error');
                    }

                    this.readyState = DONE;
                    this._dispatchEvent('readystatechange');
                    this._dispatchEvent('loadend');
                });
        }

        // Abort the request
        abort() {
            this._aborted = true;
            if (this._abortController) {
                this._abortController.abort();
            }
        }

        // Get response header
        getResponseHeader(name) {
            return this._responseHeaders[name.toLowerCase()] || null;
        }

        // Get all response headers
        getAllResponseHeaders() {
            return Object.keys(this._responseHeaders)
                .map(name => `${name}: ${this._responseHeaders[name]}`)
                .join('\r\n');
        }

        // Override MIME type
        overrideMimeType(mimeType) {
            // Not implemented for this polyfill
        }

        // Dispatch event
        _dispatchEvent(eventName) {
            const handler = this[`on${eventName}`];
            if (typeof handler === 'function') {
                const event = {
                    type: eventName,
                    target: this,
                    currentTarget: this
                };
                handler.call(this, event);
            }
        }
    }

    // Export constants
    XMLHttpRequest.UNSENT = UNSENT;
    XMLHttpRequest.OPENED = OPENED;
    XMLHttpRequest.HEADERS_RECEIVED = HEADERS_RECEIVED;
    XMLHttpRequest.LOADING = LOADING;
    XMLHttpRequest.DONE = DONE;

    // Make XMLHttpRequest global
    globalThis.XMLHttpRequest = XMLHttpRequest;
})();
