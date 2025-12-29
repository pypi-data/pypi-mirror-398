#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas 2D API 完整示例
展示 never-jscore Canvas 扩展的所有功能
"""

from never_jscore import Context
import os

# 创建输出目录
os.makedirs('../canvas_examples', exist_ok=True)

def example_basic_shapes():
    """示例 1: 基础形状绘制"""
    print("🎨 示例 1: 基础形状绘制...")

    ctx = Context(enable_extensions=True)

    code = """
    const canvas = createCanvas(800, 600);
    const ctx = canvas.getContext('2d');

    // 背景
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, 800, 600);

    // 填充矩形
    ctx.fillStyle = '#FF5722';
    ctx.fillRect(50, 50, 150, 100);

    // 描边矩形
    ctx.strokeStyle = '#2196F3';
    ctx.lineWidth = 5;
    ctx.strokeRect(250, 50, 150, 100);

    // 圆形
    ctx.fillStyle = '#4CAF50';
    ctx.beginPath();
    ctx.arc(500, 100, 60, 0, Math.PI * 2);
    ctx.fill();

    // 半圆
    ctx.strokeStyle = '#9C27B0';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(650, 100, 50, 0, Math.PI);
    ctx.stroke();

    // 三角形路径
    ctx.fillStyle = '#FFC107';
    ctx.beginPath();
    ctx.moveTo(100, 250);
    ctx.lineTo(200, 250);
    ctx.lineTo(150, 350);
    ctx.closePath();
    ctx.fill();

    // 贝塞尔曲线
    ctx.strokeStyle = '#E91E63';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(300, 300);
    ctx.bezierCurveTo(350, 250, 450, 350, 500, 300);
    ctx.stroke();

    canvas.toBuffer('image/png');
    """

    result = ctx.eval(code,return_value=True)
    with open('../canvas_examples/01_basic_shapes.png', 'wb') as f:
        f.write(bytes(result))

    print("   ✅ 已保存: canvas_examples/01_basic_shapes.png")


def example_line_styles():
    """示例 2: 线条样式（虚线、线帽）"""
    print("🎨 示例 2: 线条样式...")

    ctx = Context(enable_extensions=True)

    code = """
    const canvas = createCanvas(800, 400);
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 800, 400);

    // 不同宽度的线条
    for (let i = 0; i < 5; i++) {
        ctx.lineWidth = i + 1;
        ctx.strokeStyle = '#333';
        ctx.beginPath();
        ctx.moveTo(50, 50 + i * 30);
        ctx.lineTo(350, 50 + i * 30);
        ctx.stroke();
    }

    // 虚线样式
    const dashPatterns = [
        [5, 5],
        [10, 5],
        [15, 3, 3, 3],
        [20, 5, 5, 5],
        [25, 10]
    ];

    dashPatterns.forEach((pattern, i) => {
        ctx.setLineDash(pattern);
        ctx.strokeStyle = '#2196F3';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(450, 50 + i * 40);
        ctx.lineTo(750, 50 + i * 40);
        ctx.stroke();
    });

    // 虚线偏移动画（5 帧）
    ctx.setLineDash([20, 10]);
    for (let i = 0; i < 5; i++) {
        ctx.lineDashOffset = i * 6;
        ctx.strokeStyle = '#FF5722';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(50, 250 + i * 25);
        ctx.lineTo(750, 250 + i * 25);
        ctx.stroke();
    }

    canvas.toBuffer('image/png');
    """

    result = ctx.eval(code,return_value=True)
    with open('../canvas_examples/02_line_styles.png', 'wb') as f:
        f.write(bytes(result))

    print("   ✅ 已保存: canvas_examples/02_line_styles.png")


def example_transformations():
    """示例 3: 变换操作"""
    print("🎨 示例 3: 变换操作...")

    ctx = Context(enable_extensions=True)

    code = """
    const canvas = createCanvas(800, 600);
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#f0f0f0';
    ctx.fillRect(0, 0, 800, 600);

    // 平移
    ctx.save();
    ctx.translate(100, 100);
    ctx.fillStyle = '#FF5722';
    ctx.fillRect(0, 0, 50, 50);
    ctx.restore();

    // 旋转
    ctx.save();
    ctx.translate(250, 125);
    ctx.rotate(Math.PI / 4);
    ctx.fillStyle = '#2196F3';
    ctx.fillRect(-25, -25, 50, 50);
    ctx.restore();

    // 缩放
    ctx.save();
    ctx.translate(400, 100);
    ctx.scale(2, 1.5);
    ctx.fillStyle = '#4CAF50';
    ctx.fillRect(-25, -25, 50, 50);
    ctx.restore();

    // 组合变换（旋转动画）
    for (let i = 0; i < 8; i++) {
        ctx.save();
        ctx.translate(400, 400);
        ctx.rotate((i / 8) * Math.PI * 2);
        ctx.translate(100, 0);
        ctx.fillStyle = `hsl(${i * 45}, 70%, 50%)`;
        ctx.fillRect(-15, -15, 30, 30);
        ctx.restore();
    }

    canvas.toBuffer('image/png');
    """

    result = ctx.eval(code,return_value=True)
    with open('../canvas_examples/03_transformations.png', 'wb') as f:
        f.write(bytes(result))

    print("   ✅ 已保存: canvas_examples/03_transformations.png")


def example_clipping():
    """示例 4: 裁剪区域"""
    print("🎨 示例 4: 裁剪区域...")

    ctx = Context(enable_extensions=True)

    code = """
    const canvas = createCanvas(800, 600);
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 800, 600);

    // 圆形裁剪
    ctx.save();
    ctx.beginPath();
    ctx.arc(200, 200, 100, 0, Math.PI * 2);
    ctx.clip();

    // 在裁剪区域内绘制渐变色矩形（手动渐变）
    for (let i = 0; i < 200; i++) {
        const ratio = i / 200;
        const r = Math.floor(255 * ratio);
        const b = Math.floor(255 * (1 - ratio));
        ctx.fillStyle = `rgb(${r}, 0, ${b})`;
        ctx.fillRect(100, 100 + i, 200, 1);
    }
    ctx.restore();

    // 矩形裁剪
    ctx.save();
    ctx.beginPath();
    ctx.rect(400, 100, 200, 200);
    ctx.clip();

    // 绘制交叉线条
    ctx.strokeStyle = '#FF5722';
    ctx.lineWidth = 3;
    for (let i = 0; i < 10; i++) {
        ctx.beginPath();
        ctx.moveTo(400, 100 + i * 20);
        ctx.lineTo(600, 100 + i * 20);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(400 + i * 20, 100);
        ctx.lineTo(400 + i * 20, 300);
        ctx.stroke();
    }
    ctx.restore();

    // 星形裁剪
    ctx.save();
    ctx.beginPath();
    ctx.translate(200, 450);
    for (let i = 0; i < 5; i++) {
        const angle = (i * 4 * Math.PI) / 5;
        const x = Math.cos(angle) * 80;
        const y = Math.sin(angle) * 80;
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }
    ctx.closePath();
    ctx.clip();

    ctx.fillStyle = '#FFC107';
    ctx.fillRect(-100, -100, 200, 200);
    ctx.restore();

    canvas.toBuffer('image/png');
    """

    result = ctx.eval(code,return_value=True)
    with open('../canvas_examples/04_clipping.png', 'wb') as f:
        f.write(bytes(result))

    print("   ✅ 已保存: canvas_examples/04_clipping.png")


def example_transparency():
    """示例 5: 透明度效果"""
    print("🎨 示例 5: 透明度效果...")

    ctx = Context(enable_extensions=True)

    code = """
    const canvas = createCanvas(800, 600);
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 800, 600);

    // 使用 rgba 颜色
    ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
    ctx.fillRect(50, 50, 150, 150);

    ctx.fillStyle = 'rgba(0, 255, 0, 0.5)';
    ctx.fillRect(100, 100, 150, 150);

    ctx.fillStyle = 'rgba(0, 0, 255, 0.5)';
    ctx.fillRect(150, 150, 150, 150);

    // 使用 globalAlpha
    for (let i = 0; i < 10; i++) {
        ctx.globalAlpha = 1 - (i / 10);
        ctx.fillStyle = '#FF5722';
        ctx.fillRect(400 + i * 15, 50, 100, 100);
    }

    ctx.globalAlpha = 1.0;

    // 半透明圆形叠加
    const colors = ['#F44336', '#2196F3', '#4CAF50', '#FFC107', '#9C27B0'];
    for (let i = 0; i < 5; i++) {
        ctx.globalAlpha = 0.6;
        ctx.fillStyle = colors[i];
        ctx.beginPath();
        ctx.arc(300 + i * 30, 400, 60, 0, Math.PI * 2);
        ctx.fill();
    }

    canvas.toBuffer('image/png');
    """

    result = ctx.eval(code,return_value=True)
    with open('../canvas_examples/05_transparency.png', 'wb') as f:
        f.write(bytes(result))

    print("   ✅ 已保存: canvas_examples/05_transparency.png")


def example_image_loading():
    """示例 6: 图像加载与绘制"""
    print("🎨 示例 6: 图像加载与绘制...")

    # 先创建一个测试图像
    ctx = Context(enable_extensions=True)

    # 创建测试图像
    create_test_image = """
    const testCanvas = createCanvas(200, 200);
    const testCtx = testCanvas.getContext('2d');

    testCtx.fillStyle = '#4CAF50';
    testCtx.fillRect(0, 0, 200, 200);

    testCtx.fillStyle = '#FFC107';
    testCtx.beginPath();
    testCtx.arc(100, 100, 80, 0, Math.PI * 2);
    testCtx.fill();

    testCanvas.toBuffer('image/png');
    """

    test_img = ctx.eval(create_test_image,return_value=True)
    with open('../canvas_examples/test_image.png', 'wb') as f:
        f.write(bytes(test_img))

    # 使用图像
    code = """
    const img = new Image();
    img.src = 'canvas_examples/test_image.png';

    const canvas = createCanvas(800, 600);
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#f0f0f0';
    ctx.fillRect(0, 0, 800, 600);

    // 原始尺寸绘制
    ctx.drawImage(img, 50, 50);

    // 缩放绘制
    ctx.drawImage(img, 300, 50, 150, 150);

    // 裁剪绘制（从源图像裁剪中心 100x100）
    ctx.drawImage(img, 50, 50, 100, 100, 500, 50, 150, 150);

    // 旋转绘制
    ctx.save();
    ctx.translate(150, 400);
    ctx.rotate(Math.PI / 4);
    ctx.drawImage(img, -100, -100, 200, 200);
    ctx.restore();

    // 半透明绘制
    ctx.globalAlpha = 0.5;
    ctx.drawImage(img, 400, 300);

    canvas.toBuffer('image/png');
    """

    result = ctx.eval(code,return_value=True)
    with open('../canvas_examples/06_image_loading.png', 'wb') as f:
        f.write(bytes(result))

    print("   ✅ 已保存: canvas_examples/06_image_loading.png")


def example_pixel_manipulation():
    """示例 7: 像素操作"""
    print("🎨 示例 7: 像素操作...")

    ctx = Context(enable_extensions=True)

    code = """
    const canvas = createCanvas(800, 400);
    const ctx = canvas.getContext('2d');

    // 绘制彩色渐变
    for (let x = 0; x < 200; x++) {
        for (let y = 0; y < 200; y++) {
            const r = Math.floor((x / 200) * 255);
            const g = Math.floor((y / 200) * 255);
            const b = 128;
            ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
            ctx.fillRect(x, y, 1, 1);
        }
    }

    // 获取像素数据
    const imageData = ctx.getImageData(0, 0, 200, 200);
    const data = imageData.data;

    // 滤镜 1: 反色
    const invertedData = ctx.createImageData(200, 200);
    for (let i = 0; i < data.length; i += 4) {
        invertedData.data[i] = 255 - data[i];
        invertedData.data[i + 1] = 255 - data[i + 1];
        invertedData.data[i + 2] = 255 - data[i + 2];
        invertedData.data[i + 3] = data[i + 3];
    }
    ctx.putImageData(invertedData, 220, 0);

    // 滤镜 2: 灰度
    const grayData = ctx.createImageData(200, 200);
    for (let i = 0; i < data.length; i += 4) {
        const gray = Math.floor((data[i] + data[i + 1] + data[i + 2]) / 3);
        grayData.data[i] = gray;
        grayData.data[i + 1] = gray;
        grayData.data[i + 2] = gray;
        grayData.data[i + 3] = data[i + 3];
    }
    ctx.putImageData(grayData, 440, 0);

    // 滤镜 3: 增强红色通道
    const redData = ctx.createImageData(200, 200);
    for (let i = 0; i < data.length; i += 4) {
        redData.data[i] = Math.min(data[i] * 1.5, 255);
        redData.data[i + 1] = data[i + 1] * 0.5;
        redData.data[i + 2] = data[i + 2] * 0.5;
        redData.data[i + 3] = data[i + 3];
    }
    ctx.putImageData(redData, 0, 220);

    // 滤镜 4: 二值化
    const binaryData = ctx.createImageData(200, 200);
    for (let i = 0; i < data.length; i += 4) {
        const gray = (data[i] + data[i + 1] + data[i + 2]) / 3;
        const binary = gray > 128 ? 255 : 0;
        binaryData.data[i] = binary;
        binaryData.data[i + 1] = binary;
        binaryData.data[i + 2] = binary;
        binaryData.data[i + 3] = data[i + 3];
    }
    ctx.putImageData(binaryData, 220, 220);

    canvas.toBuffer('image/png');
    """

    result = ctx.eval(code,return_value=True)
    with open('../canvas_examples/07_pixel_manipulation.png', 'wb') as f:
        f.write(bytes(result))

    print("   ✅ 已保存: canvas_examples/07_pixel_manipulation.png")


def example_format_export():
    """示例 8: 多格式导出"""
    print("🎨 示例 8: 多格式导出...")

    ctx = Context(enable_extensions=True)

    # 在同一个代码块中完成所有操作
    code = """
    const canvas = createCanvas(600, 400);
    const ctx = canvas.getContext('2d');

    // 绘制一些内容
    ctx.fillStyle = '#3F51B5';
    ctx.fillRect(0, 0, 600, 400);

    ctx.fillStyle = '#FFC107';
    ctx.beginPath();
    ctx.arc(300, 200, 150, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#F44336';
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.moveTo(150, 200);
    ctx.lineTo(450, 200);
    ctx.stroke();

    // 返回三种格式
    ({
        png: canvas.toBuffer('image/png'),
        jpeg: canvas.toBuffer('image/jpeg'),
        webp: canvas.toBuffer('image/webp')
    });
    """

    result = ctx.eval(code, return_value=True)

    # 保存 PNG
    with open('../canvas_examples/08_export.png', 'wb') as f:
        f.write(bytes(result['png']))

    # 保存 JPEG
    with open('../canvas_examples/08_export.jpg', 'wb') as f:
        f.write(bytes(result['jpeg']))

    # 保存 WebP
    with open('../canvas_examples/08_export.webp', 'wb') as f:
        f.write(bytes(result['webp']))

    print("   ✅ 已保存: canvas_examples/08_export.png")
    print("   ✅ 已保存: canvas_examples/08_export.jpg")
    print("   ✅ 已保存: canvas_examples/08_export.webp")


def example_complex_scene():
    """示例 9: 复杂场景"""
    print("🎨 示例 9: 复杂场景...")

    ctx = Context(enable_extensions=True)

    code = """
    const canvas = createCanvas(1200, 800);
    const ctx = canvas.getContext('2d');

    // 天空渐变（手动）
    for (let y = 0; y < 400; y++) {
        const ratio = y / 400;
        const r = Math.floor(135 + (200 - 135) * ratio);
        const g = Math.floor(206 + (230 - 206) * ratio);
        const b = Math.floor(235 + (255 - 235) * ratio);
        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        ctx.fillRect(0, y, 1200, 1);
    }

    // 草地
    ctx.fillStyle = '#7CB342';
    ctx.fillRect(0, 400, 1200, 400);

    // 太阳
    ctx.fillStyle = '#FDD835';
    ctx.beginPath();
    ctx.arc(1000, 100, 80, 0, Math.PI * 2);
    ctx.fill();

    // 太阳光晕
    ctx.globalAlpha = 0.3;
    ctx.fillStyle = '#FFF9C4';
    ctx.beginPath();
    ctx.arc(1000, 100, 120, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1.0;

    // 云朵
    function drawCloud(x, y) {
        ctx.fillStyle = '#FFFFFF';
        ctx.globalAlpha = 0.8;
        ctx.beginPath();
        ctx.arc(x, y, 30, 0, Math.PI * 2);
        ctx.arc(x + 25, y - 10, 35, 0, Math.PI * 2);
        ctx.arc(x + 50, y, 30, 0, Math.PI * 2);
        ctx.arc(x + 25, y + 10, 25, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1.0;
    }

    drawCloud(200, 120);
    drawCloud(500, 180);
    drawCloud(800, 100);

    // 房子
    ctx.fillStyle = '#D32F2F';
    ctx.beginPath();
    ctx.moveTo(300, 300);
    ctx.lineTo(450, 200);
    ctx.lineTo(600, 300);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = '#FFF9C4';
    ctx.fillRect(350, 300, 200, 200);

    // 门
    ctx.fillStyle = '#795548';
    ctx.fillRect(420, 400, 60, 100);

    // 窗户
    ctx.fillStyle = '#81D4FA';
    ctx.fillRect(380, 340, 50, 50);
    ctx.fillRect(470, 340, 50, 50);

    // 树
    ctx.fillStyle = '#5D4037';
    ctx.fillRect(750, 350, 40, 150);

    ctx.fillStyle = '#388E3C';
    ctx.beginPath();
    ctx.arc(770, 320, 70, 0, Math.PI * 2);
    ctx.fill();

    // 小路（虚线）
    ctx.setLineDash([20, 10]);
    ctx.strokeStyle = '#FFEB3B';
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(600, 500);
    ctx.quadraticCurveTo(800, 600, 1000, 700);
    ctx.stroke();
    ctx.setLineDash([]);

    // 鸟（V 字形）
    function drawBird(x, y, size) {
        ctx.strokeStyle = '#424242';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x - size, y);
        ctx.lineTo(x, y + size / 2);
        ctx.lineTo(x + size, y);
        ctx.stroke();
    }

    drawBird(250, 80, 15);
    drawBird(300, 90, 12);
    drawBird(350, 75, 18);

    canvas.toBuffer('image/png');
    """

    result = ctx.eval(code,return_value=True)
    with open('../canvas_examples/09_complex_scene.png', 'wb') as f:
        f.write(bytes(result))

    print("   ✅ 已保存: canvas_examples/09_complex_scene.png")


def main():
    """运行所有示例"""
    print("=" * 60)
    print("Canvas 2D API 完整示例")
    print("=" * 60)
    print()

    examples = [
        example_basic_shapes,
        example_line_styles,
        example_transformations,
        example_clipping,
        example_transparency,
        example_image_loading,
        example_pixel_manipulation,
        example_format_export,
        example_complex_scene,
    ]

    for i, example in enumerate(examples, 1):
        try:
            example()
        except Exception as e:
            print(f"   ❌ 错误: {e}")

        if i < len(examples):
            print()

    print()
    print("=" * 60)
    print("✨ 所有示例已完成！")
    print("📁 输出目录: canvas_examples/")
    print("=" * 60)


if __name__ == '__main__':
    main()
