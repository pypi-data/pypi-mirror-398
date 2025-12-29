// Canvas Registry - 管理所有 Canvas 实例的状态
// 使用 tiny-skia 纯 Rust 实现

#[cfg(feature = "canvas")]
use tiny_skia::{Pixmap, Color, Paint, Stroke, FillRule, PathBuilder, Transform, LineCap, LineJoin};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicU32, Ordering};
use once_cell::sync::Lazy;

/// 绘图状态（用于 save/restore）
#[cfg(feature = "canvas")]
#[derive(Clone)]
pub struct DrawingState {
    pub fill_color: Color,
    pub stroke_color: Color,
    pub line_width: f32,
    pub line_cap: LineCap,
    pub line_join: LineJoin,
    pub miter_limit: f32,
    pub global_alpha: f32,
    pub transform: Transform,
    pub line_dash: Vec<f32>,
    pub line_dash_offset: f32,
}

#[cfg(feature = "canvas")]
impl Default for DrawingState {
    fn default() -> Self {
        Self {
            fill_color: Color::BLACK,
            stroke_color: Color::BLACK,
            line_width: 1.0,
            line_cap: LineCap::Butt,
            line_join: LineJoin::Miter,
            miter_limit: 10.0,
            global_alpha: 1.0,
            transform: Transform::identity(),
            line_dash: Vec::new(),
            line_dash_offset: 0.0,
        }
    }
}

/// Canvas 状态结构
#[cfg(feature = "canvas")]
pub struct CanvasState {
    pub pixmap: Pixmap,
    pub width: u32,
    pub height: u32,

    // 当前绘图状态
    pub current: DrawingState,

    // 状态栈（用于 save/restore）
    pub state_stack: Vec<DrawingState>,

    // 当前路径
    pub path_builder: Option<PathBuilder>,

    // 裁剪路径（clip mask）
    pub clip_mask: Option<tiny_skia::Mask>,
}

#[cfg(feature = "canvas")]
unsafe impl Send for CanvasState {}

#[cfg(feature = "canvas")]
impl CanvasState {
    pub fn new(width: u32, height: u32) -> Option<Self> {
        let pixmap = Pixmap::new(width, height)?;

        Some(CanvasState {
            pixmap,
            width,
            height,
            current: DrawingState::default(),
            state_stack: Vec::new(),
            path_builder: None,
            clip_mask: None,
        })
    }

    // ==================== 状态管理 ====================

    /// 保存当前状态
    pub fn save(&mut self) {
        self.state_stack.push(self.current.clone());
    }

    /// 恢复之前保存的状态
    pub fn restore(&mut self) {
        if let Some(state) = self.state_stack.pop() {
            self.current = state;
        }
    }

    // ==================== 变换操作 ====================

    /// 平移
    pub fn translate(&mut self, x: f32, y: f32) {
        self.current.transform = self.current.transform.post_translate(x, y);
    }

    /// 旋转（弧度）
    pub fn rotate(&mut self, angle: f32) {
        self.current.transform = self.current.transform.post_rotate(angle);
    }

    /// 缩放
    pub fn scale(&mut self, x: f32, y: f32) {
        self.current.transform = self.current.transform.post_scale(x, y);
    }

    /// 设置变换矩阵
    pub fn set_transform(&mut self, a: f32, b: f32, c: f32, d: f32, e: f32, f: f32) {
        self.current.transform = Transform::from_row(a, b, c, d, e, f);
    }

    /// 重置变换
    pub fn reset_transform(&mut self) {
        self.current.transform = Transform::identity();
    }

    // ==================== 路径操作 ====================

    /// 开始新路径
    pub fn begin_path(&mut self) {
        self.path_builder = Some(PathBuilder::new());
    }

    /// 关闭路径
    pub fn close_path(&mut self) {
        if let Some(pb) = &mut self.path_builder {
            pb.close();
        }
    }

    /// 移动到指定点
    pub fn move_to(&mut self, x: f32, y: f32) {
        if self.path_builder.is_none() {
            self.begin_path();
        }
        if let Some(pb) = &mut self.path_builder {
            pb.move_to(x, y);
        }
    }

    /// 绘制直线到指定点
    pub fn line_to(&mut self, x: f32, y: f32) {
        if self.path_builder.is_none() {
            self.begin_path();
        }
        if let Some(pb) = &mut self.path_builder {
            pb.line_to(x, y);
        }
    }

    /// 绘制圆弧
    pub fn arc(&mut self, x: f32, y: f32, radius: f32, start_angle: f32, end_angle: f32, anticlockwise: bool) {
        if self.path_builder.is_none() {
            self.begin_path();
        }

        if let Some(pb) = &mut self.path_builder {
            // tiny-skia 不直接支持arc，需要用贝塞尔曲线近似
            // 简化实现：将圆弧分解为多个线段
            let steps = ((end_angle - start_angle).abs() * radius / 5.0).ceil() as i32;
            let steps = steps.max(4).min(360);

            let angle_step = if anticlockwise {
                -(end_angle - start_angle) / steps as f32
            } else {
                (end_angle - start_angle) / steps as f32
            };

            let mut angle = start_angle;
            for _ in 0..steps {
                let x_pos = x + radius * angle.cos();
                let y_pos = y + radius * angle.sin();
                pb.line_to(x_pos, y_pos);
                angle += angle_step;
            }

            // 最后一个点
            let x_pos = x + radius * end_angle.cos();
            let y_pos = y + radius * end_angle.sin();
            pb.line_to(x_pos, y_pos);
        }
    }

    /// 绘制二次贝塞尔曲线
    pub fn quadratic_curve_to(&mut self, cpx: f32, cpy: f32, x: f32, y: f32) {
        if self.path_builder.is_none() {
            self.begin_path();
        }
        if let Some(pb) = &mut self.path_builder {
            pb.quad_to(cpx, cpy, x, y);
        }
    }

    /// 绘制三次贝塞尔曲线
    pub fn bezier_curve_to(&mut self, cp1x: f32, cp1y: f32, cp2x: f32, cp2y: f32, x: f32, y: f32) {
        if self.path_builder.is_none() {
            self.begin_path();
        }
        if let Some(pb) = &mut self.path_builder {
            pb.cubic_to(cp1x, cp1y, cp2x, cp2y, x, y);
        }
    }

    /// 填充当前路径
    pub fn fill(&mut self) {
        if let Some(pb) = self.path_builder.take() {
            if let Some(path) = pb.finish() {
                let mut paint = Paint::default();
                paint.set_color(self.current.fill_color);
                paint.set_color_rgba8(
                    (self.current.fill_color.red() * 255.0) as u8,
                    (self.current.fill_color.green() * 255.0) as u8,
                    (self.current.fill_color.blue() * 255.0) as u8,
                    (self.current.fill_color.alpha() * self.current.global_alpha * 255.0) as u8,
                );
                paint.anti_alias = true;

                self.pixmap.fill_path(
                    &path,
                    &paint,
                    FillRule::Winding,
                    self.current.transform,
                    self.clip_mask.as_ref(),
                );
            }
        }
    }

    /// 描边当前路径
    pub fn stroke(&mut self) {
        if let Some(pb) = self.path_builder.take() {
            if let Some(path) = pb.finish() {
                let mut paint = Paint::default();
                paint.set_color(self.current.stroke_color);
                paint.set_color_rgba8(
                    (self.current.stroke_color.red() * 255.0) as u8,
                    (self.current.stroke_color.green() * 255.0) as u8,
                    (self.current.stroke_color.blue() * 255.0) as u8,
                    (self.current.stroke_color.alpha() * self.current.global_alpha * 255.0) as u8,
                );
                paint.anti_alias = true;

                // 创建虚线模式（如果设置）
                let dash = if !self.current.line_dash.is_empty() {
                    tiny_skia::StrokeDash::new(
                        self.current.line_dash.clone(),
                        self.current.line_dash_offset,
                    )
                } else {
                    None
                };

                let stroke = Stroke {
                    width: self.current.line_width,
                    line_cap: self.current.line_cap,
                    line_join: self.current.line_join,
                    miter_limit: self.current.miter_limit,
                    dash,
                    ..Default::default()
                };

                self.pixmap.stroke_path(
                    &path,
                    &paint,
                    &stroke,
                    self.current.transform,
                    self.clip_mask.as_ref(),
                );
            }
        }
    }

    // ==================== 矩形绘制（已有功能，使用新状态）====================

    /// 填充矩形
    pub fn fill_rect(&mut self, x: f32, y: f32, width: f32, height: f32) {
        let mut pb = PathBuilder::new();
        if let Some(rect) = tiny_skia::Rect::from_xywh(x, y, width, height) {
            pb.push_rect(rect);
        }
        let path = pb.finish().unwrap();

        let mut paint = Paint::default();
        paint.set_color_rgba8(
            (self.current.fill_color.red() * 255.0) as u8,
            (self.current.fill_color.green() * 255.0) as u8,
            (self.current.fill_color.blue() * 255.0) as u8,
            (self.current.fill_color.alpha() * self.current.global_alpha * 255.0) as u8,
        );
        paint.anti_alias = true;

        self.pixmap.fill_path(
            &path,
            &paint,
            FillRule::Winding,
            self.current.transform,
            self.clip_mask.as_ref(),
        );
    }

    /// 描边矩形
    pub fn stroke_rect(&mut self, x: f32, y: f32, width: f32, height: f32) {
        let mut pb = PathBuilder::new();
        if let Some(rect) = tiny_skia::Rect::from_xywh(x, y, width, height) {
            pb.push_rect(rect);
        }
        let path = pb.finish().unwrap();

        let mut paint = Paint::default();
        paint.set_color_rgba8(
            (self.current.stroke_color.red() * 255.0) as u8,
            (self.current.stroke_color.green() * 255.0) as u8,
            (self.current.stroke_color.blue() * 255.0) as u8,
            (self.current.stroke_color.alpha() * self.current.global_alpha * 255.0) as u8,
        );
        paint.anti_alias = true;

        // 创建虚线模式（如果设置）
        let dash = if !self.current.line_dash.is_empty() {
            tiny_skia::StrokeDash::new(
                self.current.line_dash.clone(),
                self.current.line_dash_offset,
            )
        } else {
            None
        };

        let stroke = Stroke {
            width: self.current.line_width,
            line_cap: self.current.line_cap,
            line_join: self.current.line_join,
            miter_limit: self.current.miter_limit,
            dash,
            ..Default::default()
        };

        self.pixmap.stroke_path(
            &path,
            &paint,
            &stroke,
            self.current.transform,
            self.clip_mask.as_ref(),
        );
    }

    /// 清除矩形区域
    pub fn clear_rect(&mut self, x: f32, y: f32, width: f32, height: f32) {
        let x_start = x.max(0.0) as u32;
        let y_start = y.max(0.0) as u32;
        let x_end = ((x + width) as u32).min(self.width);
        let y_end = ((y + height) as u32).min(self.height);

        for py in y_start..y_end {
            for px in x_start..x_end {
                self.pixmap.pixels_mut()[(py * self.width + px) as usize] = tiny_skia::ColorU8::from_rgba(0, 0, 0, 0).premultiply();
            }
        }
    }

    // ==================== 虚线样式 ====================

    /// 设置虚线模式
    pub fn set_line_dash(&mut self, segments: Vec<f32>) {
        self.current.line_dash = segments;
    }

    /// 获取虚线模式
    pub fn get_line_dash(&self) -> Vec<f32> {
        self.current.line_dash.clone()
    }

    /// 设置虚线偏移
    pub fn set_line_dash_offset(&mut self, offset: f32) {
        self.current.line_dash_offset = offset;
    }

    // ==================== 裁剪 ====================

    /// 裁剪到当前路径
    pub fn clip(&mut self) {
        if let Some(pb) = &self.path_builder {
            // 创建路径的副本（不消耗 path_builder）
            if let Some(path) = pb.clone().finish() {
                // 创建新的 mask
                let mut mask = tiny_skia::Mask::new(self.width, self.height).unwrap();

                // 填充 mask
                mask.fill_path(
                    &path,
                    FillRule::Winding,
                    true, // anti-alias
                    self.current.transform,
                );

                // 如果已有 clip_mask，则与新 mask 进行交集
                if let Some(existing_mask) = &self.clip_mask {
                    // 执行交集操作：保留两个 mask 都为非零的区域
                    let mask_data = mask.data_mut();
                    let existing_data = existing_mask.data();
                    for (i, pixel) in mask_data.iter_mut().enumerate() {
                        *pixel = (*pixel).min(existing_data[i]);
                    }
                }

                self.clip_mask = Some(mask);
            }
        }
    }

    // ==================== 像素操作 ====================

    /// 获取图像数据
    pub fn get_image_data(&self, sx: i32, sy: i32, sw: u32, sh: u32) -> Option<Vec<u8>> {
        // 边界检查
        if sw == 0 || sh == 0 {
            return None;
        }

        let mut result = vec![0u8; (sw * sh * 4) as usize];
        let pixels = self.pixmap.data();

        for y in 0..sh {
            for x in 0..sw {
                let canvas_x = (sx + x as i32) as u32;
                let canvas_y = (sy + y as i32) as u32;

                if canvas_x < self.width && canvas_y < self.height {
                    let src_idx = ((canvas_y * self.width + canvas_x) * 4) as usize;
                    let dst_idx = ((y * sw + x) * 4) as usize;

                    // tiny-skia 内部格式实际上是 RGBA (不是 BGRA!)
                    let r = pixels[src_idx];
                    let g = pixels[src_idx + 1];
                    let b = pixels[src_idx + 2];
                    let a = pixels[src_idx + 3];

                    // 转换为标准 RGBA（去除预乘）
                    if a == 0 {
                        result[dst_idx..dst_idx + 4].copy_from_slice(&[0, 0, 0, 0]);
                    } else if a == 255 {
                        result[dst_idx..dst_idx + 4].copy_from_slice(&[r, g, b, a]);
                    } else {
                        let a_f = a as f32 / 255.0;
                        let r_unmul = ((r as f32 / a_f).min(255.0)) as u8;
                        let g_unmul = ((g as f32 / a_f).min(255.0)) as u8;
                        let b_unmul = ((b as f32 / a_f).min(255.0)) as u8;
                        result[dst_idx..dst_idx + 4].copy_from_slice(&[r_unmul, g_unmul, b_unmul, a]);
                    }
                }
            }
        }

        Some(result)
    }

    /// 放置图像数据
    pub fn put_image_data(&mut self, data: &[u8], dx: i32, dy: i32, width: u32, height: u32) {
        if data.len() != (width * height * 4) as usize {
            eprintln!("[Canvas] putImageData: invalid data length");
            return;
        }

        let pixels = self.pixmap.pixels_mut();

        for y in 0..height {
            for x in 0..width {
                let canvas_x = (dx + x as i32) as u32;
                let canvas_y = (dy + y as i32) as u32;

                if canvas_x < self.width && canvas_y < self.height {
                    let src_idx = ((y * width + x) * 4) as usize;
                    let dst_idx = (canvas_y * self.width + canvas_x) as usize;

                    // 读取标准 RGBA
                    let r = data[src_idx];
                    let g = data[src_idx + 1];
                    let b = data[src_idx + 2];
                    let a = data[src_idx + 3];

                    // tiny-skia 内部使用 RGBA (premultiplied)
                    let pixel = if a == 0 {
                        tiny_skia::ColorU8::from_rgba(0, 0, 0, 0)
                    } else if a == 255 {
                        tiny_skia::ColorU8::from_rgba(r, g, b, a)
                    } else {
                        let a_f = a as f32 / 255.0;
                        let r_pre = (r as f32 * a_f) as u8;
                        let g_pre = (g as f32 * a_f) as u8;
                        let b_pre = (b as f32 * a_f) as u8;
                        tiny_skia::ColorU8::from_rgba(r_pre, g_pre, b_pre, a)
                    };

                    pixels[dst_idx] = pixel.premultiply();
                }
            }
        }
    }
}

/// Canvas 注册表 - 全局单例
pub struct CanvasRegistry {
    #[cfg(feature = "canvas")]
    canvases: Mutex<HashMap<u32, Arc<Mutex<CanvasState>>>>,
    next_id: AtomicU32,
}

impl CanvasRegistry {
    fn new() -> Self {
        CanvasRegistry {
            #[cfg(feature = "canvas")]
            canvases: Mutex::new(HashMap::new()),
            next_id: AtomicU32::new(1),
        }
    }

    /// 创建新的 Canvas 并返回 ID
    #[cfg(feature = "canvas")]
    pub fn create(&self, width: u32, height: u32) -> Result<u32, String> {
        let state = CanvasState::new(width, height)
            .ok_or_else(|| "Failed to create canvas pixmap".to_string())?;

        let id = self.next_id.fetch_add(1, Ordering::Relaxed);

        self.canvases.lock().unwrap().insert(id, Arc::new(Mutex::new(state)));

        Ok(id)
    }

    /// 获取 Canvas 状态（用于操作）
    #[cfg(feature = "canvas")]
    pub fn get(&self, id: u32) -> Result<Arc<Mutex<CanvasState>>, String> {
        self.canvases.lock().unwrap()
            .get(&id)
            .cloned()
            .ok_or_else(|| format!("Invalid canvas ID: {}", id))
    }

    /// 删除 Canvas
    #[cfg(feature = "canvas")]
    pub fn remove(&self, id: u32) {
        self.canvases.lock().unwrap().remove(&id);
    }

    /// 获取 Canvas 数量（用于调试）
    #[cfg(feature = "canvas")]
    #[allow(dead_code)]
    pub fn count(&self) -> usize {
        self.canvases.lock().unwrap().len()
    }
}

// 手动实现 Sync，因为内部使用了 Mutex 保护
unsafe impl Sync for CanvasRegistry {}

/// 全局 Canvas 注册表实例
pub static CANVAS_REGISTRY: Lazy<CanvasRegistry> = Lazy::new(CanvasRegistry::new);
