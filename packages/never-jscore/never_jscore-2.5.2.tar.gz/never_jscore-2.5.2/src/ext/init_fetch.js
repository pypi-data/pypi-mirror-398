// Initialize fetch extension - import all modules including eventsource
import * as headers from "ext:deno_fetch/20_headers.js";
import * as formData from "ext:deno_fetch/21_formdata.js";
import * as request from "ext:deno_fetch/23_request.js";
import * as response from "ext:deno_fetch/23_response.js";
import * as fetch from "ext:deno_fetch/26_fetch.js";
import * as eventSource from "ext:deno_fetch/27_eventsource.js";

// Export to deno_web_init for global exposure
// (deno_web_init.js will handle globalThis assignment)
export { headers, formData, request, response, fetch, eventSource };
