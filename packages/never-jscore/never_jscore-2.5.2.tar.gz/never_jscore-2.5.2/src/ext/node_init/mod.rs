// Node.js initialization extension for never-jscore
// Sets up global require() and other Node.js globals

deno_core::extension!(
    node_init,
    esm_entry_point = "ext:node_init/node_init.js",
    esm = [
        dir "src/ext/node_init",
        "node_init.js",
    ],
);

pub fn init() -> deno_core::Extension {
    node_init::init()
}
