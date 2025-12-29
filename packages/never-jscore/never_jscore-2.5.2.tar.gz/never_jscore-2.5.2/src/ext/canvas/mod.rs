mod ops;

#[cfg(feature = "canvas")]
mod registry;
#[cfg(feature = "canvas")]
mod color;
#[cfg(feature = "canvas")]
mod image;

use deno_core::extension;

extension!(
    never_jscore_canvas,
    ops = [
        // Canvas Basic operation
        ops::op_canvas_create,
        ops::op_canvas_get_width,
        ops::op_canvas_get_height,
        ops::op_canvas_to_buffer,

        // Context2D Rectangular drawing
        ops::op_ctx2d_fill_rect,
        ops::op_ctx2d_stroke_rect,
        ops::op_ctx2d_clear_rect,

        // Context2D Styling
        ops::op_ctx2d_set_fill_style,
        ops::op_ctx2d_set_stroke_style,
        ops::op_ctx2d_set_line_width,
        ops::op_ctx2d_set_global_alpha,

        // Context2D Path Operations
        ops::op_ctx2d_begin_path,
        ops::op_ctx2d_close_path,
        ops::op_ctx2d_move_to,
        ops::op_ctx2d_line_to,
        ops::op_ctx2d_arc,
        ops::op_ctx2d_quadratic_curve_to,
        ops::op_ctx2d_bezier_curve_to,
        ops::op_ctx2d_fill,
        ops::op_ctx2d_stroke,

        // Context2D Status management
        ops::op_ctx2d_save,
        ops::op_ctx2d_restore,

        // Context2D Transform operations
        ops::op_ctx2d_translate,
        ops::op_ctx2d_rotate,
        ops::op_ctx2d_scale,
        ops::op_ctx2d_set_transform,
        ops::op_ctx2d_reset_transform,

        // Context2D Dotted line style
        ops::op_ctx2d_set_line_dash,
        ops::op_ctx2d_get_line_dash,
        ops::op_ctx2d_set_line_dash_offset,

        // Context2D Crop
        ops::op_ctx2d_clip,

        // Context2D Pixel Operations
        ops::op_ctx2d_get_image_data,
        ops::op_ctx2d_put_image_data,

        // Image loading and drawing
        ops::op_image_load_from_buffer,
        ops::op_image_load_from_file,
        ops::op_image_get_width,
        ops::op_image_get_height,
        ops::op_image_dispose,
        ops::op_ctx2d_draw_image,
    ],
    esm_entry_point = "ext:never_jscore_canvas/canvas.js",
    esm = [
        dir "src/ext/canvas",
        "canvas.js",
        "canvas_native.js",
    ],
);

pub fn extensions() -> Vec<deno_core::Extension> {
    vec![never_jscore_canvas::init()]
}
