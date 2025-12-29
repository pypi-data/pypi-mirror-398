// Canvas Ops - tiny-skia 实现
// 实现：创建画布、获取上下文、绘制矩形、设置样式、导出图像

#[cfg(feature = "canvas")]
use deno_core::op2;

use crate::ext::canvas::registry::CANVAS_REGISTRY;
use crate::ext::canvas::color::parse_color;

#[cfg(feature = "canvas")]
use crate::ext::canvas::image::IMAGE_REGISTRY;

// ==================== Canvas 基础操作 ====================

/// 创建 Canvas
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_canvas_create(width: u32, height: u32) -> u32 {
    match CANVAS_REGISTRY.create(width, height) {
        Ok(id) => id,
        Err(e) => {
            eprintln!("Failed to create canvas: {}", e);
            0 // 返回 0 表示失败
        }
    }
}

/// 获取 Canvas 宽度
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_canvas_get_width(canvas_id: u32) -> u32 {
    match CANVAS_REGISTRY.get(canvas_id) {
        Ok(state) => {
            let state = state.lock().unwrap();
            state.width
        }
        Err(_) => 0,
    }
}

/// 获取 Canvas 高度
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_canvas_get_height(canvas_id: u32) -> u32 {
    match CANVAS_REGISTRY.get(canvas_id) {
        Ok(state) => {
            let state = state.lock().unwrap();
            state.height
        }
        Err(_) => 0,
    }
}

/// 导出 Canvas 为图像数据
#[cfg(feature = "canvas")]
#[op2]
#[buffer]
pub fn op_canvas_to_buffer(
    canvas_id: u32,
    #[string] mime_type: &str,
) -> Vec<u8> {
    let state = match CANVAS_REGISTRY.get(canvas_id) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("[Canvas] Failed to get canvas: {}", e);
            return Vec::new();
        }
    };

    let state = state.lock().unwrap();

    match mime_type {
        "image/png" => {
            // 使用 png crate 编码
            encode_png(&state.pixmap)
        }
        "image/jpeg" => {
            // 使用 image crate 编码 JPEG
            encode_jpeg(&state.pixmap, 90) // 默认质量 90
        }
        "image/webp" => {
            // 使用 image crate 编码 WebP
            encode_webp(&state.pixmap, 90.0) // 默认质量 90
        }
        _ => {
            eprintln!("[Canvas] Unsupported MIME type: {} (supported: image/png, image/jpeg, image/webp)", mime_type);
            Vec::new()
        }
    }
}

#[cfg(feature = "canvas")]
fn encode_jpeg(pixmap: &tiny_skia::Pixmap, quality: u8) -> Vec<u8> {
    use image::{ImageBuffer, RgbImage};
    use image::codecs::jpeg::JpegEncoder;
    use std::io::Cursor;

    // 转换为RGB（JPEG不支持alpha通道）
    let width = pixmap.width();
    let height = pixmap.height();
    let data = pixmap.data();

    let mut rgb_data = Vec::with_capacity((width * height * 3) as usize);

    for pixel in data.chunks_exact(4) {
        let r = pixel[0];
        let g = pixel[1];
        let b = pixel[2];
        let a = pixel[3];

        // unpremultiply alpha
        if a == 0 {
            rgb_data.extend_from_slice(&[255, 255, 255]); // 白色背景
        } else if a == 255 {
            rgb_data.extend_from_slice(&[r, g, b]);
        } else {
            let a_f = a as f32 / 255.0;
            let r_unmul = ((r as f32 / a_f).min(255.0)) as u8;
            let g_unmul = ((g as f32 / a_f).min(255.0)) as u8;
            let b_unmul = ((b as f32 / a_f).min(255.0)) as u8;

            // 使用白色背景合成
            let r_final = ((r_unmul as f32 * a_f) + (255.0 * (1.0 - a_f))) as u8;
            let g_final = ((g_unmul as f32 * a_f) + (255.0 * (1.0 - a_f))) as u8;
            let b_final = ((b_unmul as f32 * a_f) + (255.0 * (1.0 - a_f))) as u8;

            rgb_data.extend_from_slice(&[r_final, g_final, b_final]);
        }
    }

    let img: RgbImage = ImageBuffer::from_raw(width, height, rgb_data)
        .expect("Failed to create RGB image");

    let mut buf = Vec::new();
    let mut cursor = Cursor::new(&mut buf);

    let mut encoder = JpegEncoder::new_with_quality(&mut cursor, quality);
    if let Err(e) = encoder.encode_image(&img) {
        eprintln!("[Canvas] Failed to encode JPEG: {}", e);
        return Vec::new();
    }

    buf
}

#[cfg(feature = "canvas")]
fn encode_webp(pixmap: &tiny_skia::Pixmap, _quality: f32) -> Vec<u8> {
    use image::{ImageBuffer, RgbaImage};
    use image::codecs::webp::WebPEncoder;
    use std::io::Cursor;

    // 转换为标准 RGBA
    let width = pixmap.width();
    let height = pixmap.height();
    let data = pixmap.data();

    let mut rgba_data = Vec::with_capacity((width * height * 4) as usize);

    for pixel in data.chunks_exact(4) {
        let r = pixel[0];
        let g = pixel[1];
        let b = pixel[2];
        let a = pixel[3];

        // unpremultiply alpha
        if a == 0 {
            rgba_data.extend_from_slice(&[0, 0, 0, 0]);
        } else if a == 255 {
            rgba_data.extend_from_slice(&[r, g, b, a]);
        } else {
            let a_f = a as f32 / 255.0;
            let r_unmul = ((r as f32 / a_f).min(255.0)) as u8;
            let g_unmul = ((g as f32 / a_f).min(255.0)) as u8;
            let b_unmul = ((b as f32 / a_f).min(255.0)) as u8;
            rgba_data.extend_from_slice(&[r_unmul, g_unmul, b_unmul, a]);
        }
    }

    let img: RgbaImage = ImageBuffer::from_raw(width, height, rgba_data)
        .expect("Failed to create RGBA image");

    let mut buf = Vec::new();
    let mut cursor = Cursor::new(&mut buf);

    let encoder = WebPEncoder::new_lossless(&mut cursor);
    if let Err(e) = encoder.encode(&img, width, height, image::ExtendedColorType::Rgba8) {
        eprintln!("[Canvas] Failed to encode WebP: {}", e);
        return Vec::new();
    }

    buf
}

#[cfg(feature = "canvas")]
fn encode_png(pixmap: &tiny_skia::Pixmap) -> Vec<u8> {
    use png::{BitDepth, ColorType, Encoder};
    use std::io::Cursor;

    let mut buf = Vec::new();
    let mut cursor = Cursor::new(&mut buf);

    {
        let mut encoder = Encoder::new(&mut cursor, pixmap.width(), pixmap.height());
        encoder.set_color(ColorType::Rgba);
        encoder.set_depth(BitDepth::Eight);

        let mut writer = match encoder.write_header() {
            Ok(w) => w,
            Err(e) => {
                eprintln!("[Canvas] Failed to write PNG header: {}", e);
                return Vec::new();
            }
        };

        // tiny-skia 使用 premultiplied RGBA 格式，需要转换为标准 RGBA
        let data = pixmap.data();
        let mut rgba_data = Vec::with_capacity(data.len());

        for pixel in data.chunks_exact(4) {
            let r = pixel[0];
            let g = pixel[1];
            let b = pixel[2];
            let a = pixel[3];

            // 将 premultiplied 转换为标准 RGBA
            if a == 0 {
                rgba_data.extend_from_slice(&[0, 0, 0, 0]);
            } else if a == 255 {
                rgba_data.extend_from_slice(&[r, g, b, a]);
            } else {
                let a_f = a as f32 / 255.0;
                let r_unmul = ((r as f32 / a_f).min(255.0)) as u8;
                let g_unmul = ((g as f32 / a_f).min(255.0)) as u8;
                let b_unmul = ((b as f32 / a_f).min(255.0)) as u8;
                rgba_data.extend_from_slice(&[r_unmul, g_unmul, b_unmul, a]);
            }
        }

        if let Err(e) = writer.write_image_data(&rgba_data) {
            eprintln!("[Canvas] Failed to write PNG data: {}", e);
            return Vec::new();
        }
    }

    buf
}

// ==================== Context2D 绘图操作 ====================

/// 填充矩形
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_fill_rect(ctx_id: u32, x: f64, y: f64, width: f64, height: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.fill_rect(x as f32, y as f32, width as f32, height as f32);
    }
}

/// 描边矩形
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_stroke_rect(ctx_id: u32, x: f64, y: f64, width: f64, height: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.stroke_rect(x as f32, y as f32, width as f32, height as f32);
    }
}

/// 清除矩形区域
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_clear_rect(ctx_id: u32, x: f64, y: f64, width: f64, height: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.clear_rect(x as f32, y as f32, width as f32, height as f32);
    }
}

// ==================== Context2D 样式设置 ====================

/// 设置填充样式
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_set_fill_style(ctx_id: u32, #[string] style: &str) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        let color = parse_color(style);
        state.current.fill_color = color;
    }
}

/// 设置描边样式
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_set_stroke_style(ctx_id: u32, #[string] style: &str) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        let color = parse_color(style);
        state.current.stroke_color = color;
    }
}

/// 设置线宽
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_set_line_width(ctx_id: u32, width: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.current.line_width = width as f32;
    }
}

// ==================== 路径操作 ====================

/// 开始新路径
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_begin_path(ctx_id: u32) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.begin_path();
    }
}

/// 关闭当前路径
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_close_path(ctx_id: u32) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.close_path();
    }
}

/// 移动到指定点
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_move_to(ctx_id: u32, x: f64, y: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.move_to(x as f32, y as f32);
    }
}

/// 绘制直线
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_line_to(ctx_id: u32, x: f64, y: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.line_to(x as f32, y as f32);
    }
}

/// 绘制圆弧
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_arc(ctx_id: u32, x: f64, y: f64, radius: f64, start_angle: f64, end_angle: f64, anticlockwise: bool) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.arc(x as f32, y as f32, radius as f32, start_angle as f32, end_angle as f32, anticlockwise);
    }
}

/// 绘制二次贝塞尔曲线
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_quadratic_curve_to(ctx_id: u32, cpx: f64, cpy: f64, x: f64, y: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.quadratic_curve_to(cpx as f32, cpy as f32, x as f32, y as f32);
    }
}

/// 绘制三次贝塞尔曲线
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_bezier_curve_to(ctx_id: u32, cp1x: f64, cp1y: f64, cp2x: f64, cp2y: f64, x: f64, y: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.bezier_curve_to(cp1x as f32, cp1y as f32, cp2x as f32, cp2y as f32, x as f32, y as f32);
    }
}

/// 填充路径
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_fill(ctx_id: u32) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.fill();
    }
}

/// 描边路径
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_stroke(ctx_id: u32) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.stroke();
    }
}

// ==================== 状态管理 ====================

/// 保存当前状态
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_save(ctx_id: u32) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.save();
    }
}

/// 恢复之前保存的状态
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_restore(ctx_id: u32) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.restore();
    }
}

// ==================== 变换操作 ====================

/// 平移
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_translate(ctx_id: u32, x: f64, y: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.translate(x as f32, y as f32);
    }
}

/// 旋转
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_rotate(ctx_id: u32, angle: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.rotate(angle as f32);
    }
}

/// 缩放
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_scale(ctx_id: u32, x: f64, y: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.scale(x as f32, y as f32);
    }
}

/// 设置变换矩阵
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_set_transform(ctx_id: u32, a: f64, b: f64, c: f64, d: f64, e: f64, f: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.set_transform(a as f32, b as f32, c as f32, d as f32, e as f32, f as f32);
    }
}

/// 重置变换矩阵
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_reset_transform(ctx_id: u32) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.reset_transform();
    }
}

// ==================== 其他样式属性 ====================

/// 设置全局透明度
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_set_global_alpha(ctx_id: u32, alpha: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.current.global_alpha = alpha.max(0.0).min(1.0) as f32;
    }
}

// ==================== 虚线样式 ====================

/// 设置虚线模式
#[op2]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_set_line_dash(ctx_id: u32, #[serde] segments: Vec<f64>) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        // 过滤掉负数和 NaN，并转换为 f32
        let valid_segments: Vec<f32> = segments
            .into_iter()
            .filter(|&x| x >= 0.0 && !x.is_nan())
            .map(|x| x as f32)
            .collect();
        state.set_line_dash(valid_segments);
    }
}

/// 获取虚线模式
#[op2]
#[serde]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_get_line_dash(ctx_id: u32) -> Vec<f64> {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let state = state.lock().unwrap();
        state.get_line_dash().into_iter().map(|x| x as f64).collect()
    } else {
        Vec::new()
    }
}

/// 设置虚线偏移
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_set_line_dash_offset(ctx_id: u32, offset: f64) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.set_line_dash_offset(offset as f32);
    }
}

// ==================== 裁剪操作 ====================

/// 裁剪到当前路径
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_clip(ctx_id: u32) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.clip();
    }
}

// ==================== 像素操作 ====================

/// 获取图像数据
#[op2]
#[buffer]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_get_image_data(ctx_id: u32, sx: i32, sy: i32, sw: u32, sh: u32) -> Vec<u8> {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let state = state.lock().unwrap();
        state.get_image_data(sx, sy, sw, sh).unwrap_or_default()
    } else {
        Vec::new()
    }
}

/// 放置图像数据
#[op2]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_put_image_data(
    ctx_id: u32,
    dx: i32,
    dy: i32,
    width: u32,
    height: u32,
    #[serde] data: Vec<u8>,
) {
    if let Ok(state) = CANVAS_REGISTRY.get(ctx_id) {
        let mut state = state.lock().unwrap();
        state.put_image_data(&data, dx, dy, width, height);
    }
}

// ==================== 空实现（feature 未启用时）====================

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_canvas_create(_width: u32, _height: u32) -> u32 {
    0
}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_canvas_get_width(_canvas_id: u32) -> u32 {
    0
}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_canvas_get_height(_canvas_id: u32) -> u32 {
    0
}

#[op2]
#[buffer]
#[cfg(not(feature = "canvas"))]
pub fn op_canvas_to_buffer(
    _canvas_id: u32,
    #[string] _mime_type: &str,
) -> Vec<u8> {
    eprintln!("[Canvas] Canvas feature not enabled");
    Vec::new()
}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_ctx2d_fill_rect(_ctx_id: u32, _x: f64, _y: f64, _width: f64, _height: f64) {}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_ctx2d_stroke_rect(_ctx_id: u32, _x: f64, _y: f64, _width: f64, _height: f64) {}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_ctx2d_clear_rect(_ctx_id: u32, _x: f64, _y: f64, _width: f64, _height: f64) {}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_ctx2d_set_fill_style(_ctx_id: u32, #[string] _style: &str) {}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_ctx2d_set_stroke_style(_ctx_id: u32, #[string] _style: &str) {}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_ctx2d_set_line_width(_ctx_id: u32, _width: f64) {}

// ==================== 图像加载操作 ====================

/// 从 PNG Buffer 加载图像
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_image_load_from_buffer(#[buffer] data: &[u8]) -> u32 {
    match IMAGE_REGISTRY.load_from_encoded(data) {
        Ok(id) => id,
        Err(e) => {
            eprintln!("[Canvas] Failed to load image from buffer: {}", e);
            0
        }
    }
}

/// 从文件路径加载图像
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_image_load_from_file(#[string] path: &str) -> u32 {
    match IMAGE_REGISTRY.load_from_file(path) {
        Ok(id) => id,
        Err(e) => {
            eprintln!("[Canvas] Failed to load image from file '{}': {}", path, e);
            0
        }
    }
}

/// 获取图像宽度
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_image_get_width(image_id: u32) -> u32 {
    match IMAGE_REGISTRY.get_size(image_id) {
        Ok((width, _)) => width,
        Err(_) => 0,
    }
}

/// 获取图像高度
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_image_get_height(image_id: u32) -> u32 {
    match IMAGE_REGISTRY.get_size(image_id) {
        Ok((_, height)) => height,
        Err(_) => 0,
    }
}

/// 删除图像（释放内存）
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_image_dispose(image_id: u32) {
    IMAGE_REGISTRY.remove(image_id);
}

// ==================== 图像绘制操作 ====================

/// 在 Canvas 上绘制图像
/// 支持三种形式：
/// - drawImage(image, dx, dy)
/// - drawImage(image, dx, dy, dWidth, dHeight)
/// - drawImage(image, sx, sy, sWidth, sHeight, dx, dy, dWidth, dHeight)
#[op2(fast)]
#[cfg(feature = "canvas")]
pub fn op_ctx2d_draw_image(
    ctx_id: u32,
    image_id: u32,
    sx: f64,
    sy: f64,
    s_width: f64,
    s_height: f64,
    dx: f64,
    dy: f64,
    d_width: f64,
    d_height: f64,
) {
    // 获取 canvas 状态
    let canvas_state = match CANVAS_REGISTRY.get(ctx_id) {
        Ok(state) => state,
        Err(e) => {
            eprintln!("[Canvas] Failed to get canvas: {}", e);
            return;
        }
    };

    // 获取图像数据
    let image_data = match IMAGE_REGISTRY.get(image_id) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("[Canvas] Failed to get image: {}", e);
            return;
        }
    };

    let mut canvas = canvas_state.lock().unwrap();
    let image = image_data.lock().unwrap();

    // 参数验证
    if sx < 0.0 || sy < 0.0 || s_width <= 0.0 || s_height <= 0.0 ||
       d_width <= 0.0 || d_height <= 0.0 {
        return;
    }

    let sx = sx as u32;
    let sy = sy as u32;
    let s_width = s_width as u32;
    let s_height = s_height as u32;

    // 检查源区域是否在图像范围内
    if sx + s_width > image.width || sy + s_height > image.height {
        eprintln!("[Canvas] Source region out of image bounds");
        return;
    }

    // 使用 tiny-skia 的 draw_pixmap 方法
    use tiny_skia::{PixmapPaint, FilterQuality};

    // 计算缩放和平移
    let scale_x = d_width as f32 / s_width as f32;
    let scale_y = d_height as f32 / s_height as f32;

    // 构建变换矩阵：先平移到目标位置，再缩放，再减去源偏移
    let mut transform = canvas.current.transform;
    transform = transform.post_translate(dx as f32, dy as f32);
    transform = transform.post_scale(scale_x, scale_y);
    transform = transform.post_translate(-(sx as f32), -(sy as f32));

    let paint = PixmapPaint {
        opacity: canvas.current.global_alpha,
        blend_mode: tiny_skia::BlendMode::SourceOver,
        quality: FilterQuality::Bilinear,
    };

    canvas.pixmap.draw_pixmap(
        0,
        0,
        image.pixmap.as_ref(),
        &paint,
        transform,
        None,
    );
}

// ==================== 空实现（feature 未启用时）====================

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_image_load_from_buffer(#[buffer] _data: &[u8]) -> u32 {
    eprintln!("[Canvas] Canvas feature not enabled");
    0
}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_image_load_from_file(#[string] _path: &str) -> u32 {
    eprintln!("[Canvas] Canvas feature not enabled");
    0
}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_image_get_width(_image_id: u32) -> u32 {
    0
}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_image_get_height(_image_id: u32) -> u32 {
    0
}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_image_dispose(_image_id: u32) {}

#[op2(fast)]
#[cfg(not(feature = "canvas"))]
pub fn op_ctx2d_draw_image(
    _ctx_id: u32,
    _image_id: u32,
    _sx: f64,
    _sy: f64,
    _s_width: f64,
    _s_height: f64,
    _dx: f64,
    _dy: f64,
    _d_width: f64,
    _d_height: f64,
) {}
