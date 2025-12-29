// Image Registry - 管理加载的图像
// 支持从文件、Buffer、Data URI 加载图像

#[cfg(feature = "canvas")]
use tiny_skia::Pixmap;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicU32, Ordering};
use once_cell::sync::Lazy;

/// 图像数据结构
#[cfg(feature = "canvas")]
pub struct ImageData {
    pub pixmap: Pixmap,
    pub width: u32,
    pub height: u32,
}

#[cfg(feature = "canvas")]
unsafe impl Send for ImageData {}

#[cfg(feature = "canvas")]
impl ImageData {
    /// 从 PNG 数据创建图像
    pub fn from_png(data: &[u8]) -> Result<Self, String> {
        let pixmap = Pixmap::decode_png(data)
            .map_err(|e| format!("Failed to decode PNG: {}", e))?;

        let width = pixmap.width();
        let height = pixmap.height();

        Ok(ImageData {
            pixmap,
            width,
            height,
        })
    }

    /// 从 SVG 数据创建图像
    pub fn from_svg(data: &[u8], width: Option<u32>, height: Option<u32>) -> Result<Self, String> {
        use resvg::usvg::{Options, Tree};
        use resvg::tiny_skia;

        // 解析 SVG
        let opt = Options::default();
        let tree = Tree::from_data(data, &opt)
            .map_err(|e| format!("Failed to parse SVG: {}", e))?;

        // 获取 SVG 尺寸
        let svg_size = tree.size();
        let (svg_width, svg_height) = (svg_size.width() as u32, svg_size.height() as u32);

        // 如果未指定尺寸，使用 SVG 原始尺寸
        let render_width = width.unwrap_or(svg_width);
        let render_height = height.unwrap_or(svg_height);

        if render_width == 0 || render_height == 0 {
            return Err("SVG dimensions must be positive".to_string());
        }

        // 创建 pixmap
        let mut pixmap = tiny_skia::Pixmap::new(render_width, render_height)
            .ok_or("Failed to create pixmap for SVG")?;

        // 计算缩放比例
        let scale_x = render_width as f32 / svg_width as f32;
        let scale_y = render_height as f32 / svg_height as f32;

        // 渲染 SVG
        let transform = tiny_skia::Transform::from_scale(scale_x, scale_y);
        resvg::render(&tree, transform, &mut pixmap.as_mut());

        Ok(ImageData {
            width: render_width,
            height: render_height,
            pixmap,
        })
    }

    /// 从任意格式图像数据创建（PNG, JPEG, WebP, SVG等）
    pub fn from_encoded(data: &[u8]) -> Result<Self, String> {
        use image::ImageReader;
        use std::io::Cursor;

        // 先尝试使用 tiny-skia 的 PNG 解码器（更快）
        if data.starts_with(b"\x89PNG") {
            if let Ok(img) = Self::from_png(data) {
                return Ok(img);
            }
        }

        // 检测 SVG 格式（查找 <svg 标签）
        let data_str = std::str::from_utf8(data).unwrap_or("");
        if data_str.trim_start().starts_with("<?xml") || data_str.contains("<svg") {
            return Self::from_svg(data, None, None);
        }

        // 使用 image crate 解码（支持 JPEG, WebP, PNG 等）
        let img = ImageReader::new(Cursor::new(data))
            .with_guessed_format()
            .map_err(|e| format!("Failed to guess image format: {}", e))?
            .decode()
            .map_err(|e| format!("Failed to decode image: {}", e))?;

        // 转换为 RGBA8
        let rgba = img.to_rgba8();
        let (width, height) = (rgba.width(), rgba.height());

        // 将标准 RGBA 转换为 premultiplied RGBA (tiny-skia 格式)
        let mut premul_data = Vec::with_capacity((width * height * 4) as usize);
        for pixel in rgba.pixels() {
            let r = pixel[0];
            let g = pixel[1];
            let b = pixel[2];
            let a = pixel[3];

            if a == 0 {
                premul_data.extend_from_slice(&[0, 0, 0, 0]);
            } else if a == 255 {
                // tiny-skia 使用 RGBA 顺序
                premul_data.extend_from_slice(&[r, g, b, a]);
            } else {
                let a_f = a as f32 / 255.0;
                let r_pre = (r as f32 * a_f) as u8;
                let g_pre = (g as f32 * a_f) as u8;
                let b_pre = (b as f32 * a_f) as u8;
                // tiny-skia 使用 RGBA 顺序
                premul_data.extend_from_slice(&[r_pre, g_pre, b_pre, a]);
            }
        }

        let pixmap = Pixmap::from_vec(
            premul_data,
            tiny_skia::IntSize::from_wh(width, height).ok_or("Invalid image size")?,
        )
        .ok_or("Failed to create pixmap")?;

        Ok(ImageData {
            pixmap,
            width,
            height,
        })
    }

    /// 从文件路径加载图像
    pub fn from_file(path: &str) -> Result<Self, String> {
        use std::fs;

        let data = fs::read(path)
            .map_err(|e| format!("Failed to read file '{}': {}", path, e))?;

        Self::from_encoded(&data)
    }

    /// 从 RGBA 数据创建图像
    pub fn from_rgba(width: u32, height: u32, data: Vec<u8>) -> Result<Self, String> {
        if data.len() != (width * height * 4) as usize {
            return Err(format!(
                "Invalid RGBA data length: expected {}, got {}",
                width * height * 4,
                data.len()
            ));
        }

        // 将标准 RGBA 转换为 premultiplied RGBA（tiny-skia 格式）
        let mut premul_data = Vec::with_capacity(data.len());
        for chunk in data.chunks_exact(4) {
            let r = chunk[0];
            let g = chunk[1];
            let b = chunk[2];
            let a = chunk[3];

            // premultiply: R,G,B *= alpha
            if a == 0 {
                premul_data.extend_from_slice(&[0, 0, 0, 0]);
            } else if a == 255 {
                // tiny-skia 使用 RGBA 顺序
                premul_data.extend_from_slice(&[r, g, b, a]);
            } else {
                let a_f = a as f32 / 255.0;
                let r_pre = (r as f32 * a_f) as u8;
                let g_pre = (g as f32 * a_f) as u8;
                let b_pre = (b as f32 * a_f) as u8;
                // tiny-skia 使用 RGBA 顺序
                premul_data.extend_from_slice(&[r_pre, g_pre, b_pre, a]);
            }
        }

        let pixmap = Pixmap::from_vec(premul_data, tiny_skia::IntSize::from_wh(width, height).ok_or("Invalid size")?)
            .ok_or("Failed to create pixmap")?;

        Ok(ImageData {
            pixmap,
            width,
            height,
        })
    }
}

/// 图像注册表 - 全局单例
pub struct ImageRegistry {
    #[cfg(feature = "canvas")]
    images: Mutex<HashMap<u32, Arc<Mutex<ImageData>>>>,
    next_id: AtomicU32,
}

impl ImageRegistry {
    fn new() -> Self {
        ImageRegistry {
            #[cfg(feature = "canvas")]
            images: Mutex::new(HashMap::new()),
            next_id: AtomicU32::new(1),
        }
    }

    /// 从 PNG 数据加载图像
    #[cfg(feature = "canvas")]
    pub fn load_from_png(&self, data: &[u8]) -> Result<u32, String> {
        let image_data = ImageData::from_png(data)?;
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);

        self.images.lock().unwrap().insert(id, Arc::new(Mutex::new(image_data)));

        Ok(id)
    }

    /// 从任意格式加载图像（PNG, JPEG, WebP等）
    #[cfg(feature = "canvas")]
    pub fn load_from_encoded(&self, data: &[u8]) -> Result<u32, String> {
        let image_data = ImageData::from_encoded(data)?;
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);

        self.images.lock().unwrap().insert(id, Arc::new(Mutex::new(image_data)));

        Ok(id)
    }

    /// 从文件路径加载图像
    #[cfg(feature = "canvas")]
    pub fn load_from_file(&self, path: &str) -> Result<u32, String> {
        let image_data = ImageData::from_file(path)?;
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);

        self.images.lock().unwrap().insert(id, Arc::new(Mutex::new(image_data)));

        Ok(id)
    }

    /// 从 RGBA 数据加载图像
    #[cfg(feature = "canvas")]
    pub fn load_from_rgba(&self, width: u32, height: u32, data: Vec<u8>) -> Result<u32, String> {
        let image_data = ImageData::from_rgba(width, height, data)?;
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);

        self.images.lock().unwrap().insert(id, Arc::new(Mutex::new(image_data)));

        Ok(id)
    }

    /// 获取图像数据
    #[cfg(feature = "canvas")]
    pub fn get(&self, id: u32) -> Result<Arc<Mutex<ImageData>>, String> {
        self.images.lock().unwrap()
            .get(&id)
            .cloned()
            .ok_or_else(|| format!("Invalid image ID: {}", id))
    }

    /// 获取图像尺寸
    #[cfg(feature = "canvas")]
    pub fn get_size(&self, id: u32) -> Result<(u32, u32), String> {
        let img = self.get(id)?;
        let img = img.lock().unwrap();
        Ok((img.width, img.height))
    }

    /// 删除图像
    #[cfg(feature = "canvas")]
    pub fn remove(&self, id: u32) {
        self.images.lock().unwrap().remove(&id);
    }

    /// 获取图像数量（用于调试）
    #[cfg(feature = "canvas")]
    #[allow(dead_code)]
    pub fn count(&self) -> usize {
        self.images.lock().unwrap().len()
    }
}

// 手动实现 Sync
unsafe impl Sync for ImageRegistry {}

/// 全局图像注册表实例
pub static IMAGE_REGISTRY: Lazy<ImageRegistry> = Lazy::new(ImageRegistry::new);
