// 颜色解析工具 - 适配 tiny-skia 和 csscolorparser

#[cfg(feature = "canvas")]
use tiny_skia::Color;

/// 解析 CSS 颜色字符串为 tiny-skia Color
///
/// 支持的格式：
/// - 十六进制: #RGB, #RRGGBB, #RRGGBBAA
/// - 函数式: rgb(), rgba(), hsl(), hsla(), hwb(), lab(), lch(), oklab(), oklch()
/// - 命名颜色: red, blue, green, etc.
///
/// # Examples
/// ```
/// let red = parse_color("#FF0000");
/// let green = parse_color("rgb(0, 255, 0)");
/// let blue = parse_color("blue");
/// ```
#[cfg(feature = "canvas")]
pub fn parse_color(color_str: &str) -> Color {
    // 使用 csscolorparser 解析颜色字符串
    match csscolorparser::parse(color_str) {
        Ok(color) => {
            // 获取 RGBA 值 (u8 数组: [R, G, B, A])
            let rgba = color.to_rgba8();

            // 创建 tiny-skia Color
            Color::from_rgba8(rgba[0], rgba[1], rgba[2], rgba[3])
        }
        Err(e) => {
            // 解析失败时打印错误并回退到黑色
            eprintln!("[Canvas] Failed to parse color '{}': {}", color_str, e);
            Color::BLACK
        }
    }
}

/// 从 RGBA 值创建 Color
#[cfg(feature = "canvas")]
#[allow(dead_code)]
pub fn from_rgba(r: u8, g: u8, b: u8, a: u8) -> Color {
    Color::from_rgba8(r, g, b, a)
}

/// 从 RGB 值创建 Color (alpha = 255)
#[cfg(feature = "canvas")]
#[allow(dead_code)]
pub fn from_rgb(r: u8, g: u8, b: u8) -> Color {
    Color::from_rgba8(r, g, b, 255)
}

#[cfg(test)]
#[cfg(feature = "canvas")]
mod tests {
    use super::*;

    #[test]
    fn test_parse_hex_colors() {
        let red = parse_color("#FF0000");
        assert_eq!(red, Color::from_rgba8(255, 0, 0, 255));

        let green = parse_color("#00FF00");
        assert_eq!(green, Color::from_rgba8(0, 255, 0, 255));

        let blue = parse_color("#0000FF");
        assert_eq!(blue, Color::from_rgba8(0, 0, 255, 255));
    }

    #[test]
    fn test_parse_hex_with_alpha() {
        let semi_transparent_red = parse_color("#FF000080");
        assert_eq!(semi_transparent_red, Color::from_rgba8(255, 0, 0, 128));
    }

    #[test]
    fn test_parse_rgb_function() {
        let color = parse_color("rgb(255, 128, 0)");
        assert_eq!(color, Color::from_rgba8(255, 128, 0, 255));
    }

    #[test]
    fn test_parse_rgba_function() {
        let color = parse_color("rgba(255, 0, 0, 0.5)");
        assert_eq!(color, Color::from_rgba8(255, 0, 0, 127));
    }

    #[test]
    fn test_parse_named_colors() {
        let red = parse_color("red");
        assert_eq!(red, Color::from_rgba8(255, 0, 0, 255));

        let blue = parse_color("blue");
        assert_eq!(blue, Color::from_rgba8(0, 0, 255, 255));

        let white = parse_color("white");
        assert_eq!(white, Color::WHITE);
    }

    #[test]
    fn test_invalid_color_returns_black() {
        let color = parse_color("invalid-color");
        assert_eq!(color, Color::BLACK);
    }

    #[test]
    fn test_helper_functions() {
        let color1 = from_rgba(255, 128, 64, 200);
        assert_eq!(color1, Color::from_rgba8(255, 128, 64, 200));

        let color2 = from_rgb(100, 150, 200);
        assert_eq!(color2, Color::from_rgba8(100, 150, 200, 255));
    }
}
