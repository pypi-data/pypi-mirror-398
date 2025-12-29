# Canvas 2D API 参考文档

## 📋 目录

- [功能总览](#功能总览)
- [快速开始](#快速开始)
- [完整使用示例](#完整使用示例)
- [API 参考](#api-参考)
  - [Canvas 类](#canvas-类)
  - [CanvasRenderingContext2D 类](#canvasrenderingcontext2d-类)
  - [Image 类](#image-类)
  - [ImageData 类](#imagedata-类)
- [兼容性对照表](#兼容性对照表)
- [性能优化建议](#性能优化建议)

---

## 功能总览

### ✅ 已实现功能 (9/13 - 69%)

| 功能类别 | 已实现 | 说明 |
|---------|--------|------|
| **基础绘图** | ✅ | 矩形、路径、圆弧、贝塞尔曲线 |
| **样式设置** | ✅ | 填充色、描边色、线宽、透明度 |
| **变换操作** | ✅ | 平移、旋转、缩放、变换矩阵 |
| **状态管理** | ✅ | save/restore |
| **图像操作** | ✅ | 加载、绘制图像 |
| **虚线样式** | ✅ | setLineDash, lineDashOffset |
| **裁剪** | ✅ | clip() |
| **像素操作** | ✅ | getImageData, putImageData, createImageData |
| **多格式支持** | ✅ | PNG, JPEG, WebP (导入/导出) |
| **文字渲染** | ❌ | fillText, strokeText, measureText |
| **渐变** | ❌ | createLinearGradient, createRadialGradient |
| **图案填充** | ❌ | createPattern |
| **阴影效果** | ❌ | shadowBlur, shadowColor, shadowOffset |

---

## 快速开始

### 安装

```bash
pip install never-jscore
```

### 基础示例

```python
from never_jscore import Context

# 创建 JavaScript 上下文（启用 Canvas 扩展）
ctx = Context(enable_extensions=True)

# 创建 Canvas
code = """
const canvas = createCanvas(800, 600);
const ctx = canvas.getContext('2d');

// 绘制红色矩形
ctx.fillStyle = '#FF0000';
ctx.fillRect(50, 50, 200, 100);

// 导出为 PNG
const buffer = canvas.toBuffer('image/png');
buffer;
"""

result = ctx.eval(code)

# 保存图像
with open('output.png', 'wb') as f:
    f.write(bytes(result))
```

---

## 完整使用示例

### 示例 1: 综合绘图

```python
from never_jscore import Context

ctx = Context(enable_extensions=True)

code = """
// 创建 800x600 画布
const canvas = createCanvas(800, 600);
const ctx = canvas.getContext('2d');

// 1. 背景
ctx.fillStyle = '#f0f0f0';
ctx.fillRect(0, 0, 800, 600);

// 2. 绘制渐变色矩形（使用纯色模拟）
ctx.fillStyle = '#4CAF50';
ctx.fillRect(50, 50, 200, 150);

// 3. 绘制描边圆角矩形
ctx.strokeStyle = '#2196F3';
ctx.lineWidth = 5;
ctx.beginPath();
ctx.moveTo(300, 50);
ctx.lineTo(480, 50);
ctx.arcTo(500, 50, 500, 70, 20);
ctx.lineTo(500, 180);
ctx.arcTo(500, 200, 480, 200, 20);
ctx.lineTo(300, 200);
ctx.arcTo(280, 200, 280, 180, 20);
ctx.lineTo(280, 70);
ctx.arcTo(280, 50, 300, 50, 20);
ctx.closePath();
ctx.stroke();

// 4. 绘制圆形路径
ctx.fillStyle = '#FF5722';
ctx.beginPath();
ctx.arc(400, 350, 80, 0, Math.PI * 2);
ctx.fill();

// 5. 绘制虚线
ctx.setLineDash([10, 5]);
ctx.strokeStyle = '#9C27B0';
ctx.lineWidth = 3;
ctx.beginPath();
ctx.moveTo(50, 450);
ctx.lineTo(750, 450);
ctx.stroke();
ctx.setLineDash([]); // 重置虚线

// 6. 使用变换绘制旋转矩形
ctx.save();
ctx.translate(650, 100);
ctx.rotate(Math.PI / 4);
ctx.fillStyle = '#FFC107';
ctx.fillRect(-50, -50, 100, 100);
ctx.restore();

// 7. 裁剪区域绘制
ctx.save();
ctx.beginPath();
ctx.arc(150, 350, 60, 0, Math.PI * 2);
ctx.clip();
ctx.fillStyle = '#E91E63';
ctx.fillRect(90, 290, 120, 120);
ctx.restore();

// 8. 设置透明度
ctx.globalAlpha = 0.5;
ctx.fillStyle = '#00BCD4';
ctx.fillRect(550, 400, 150, 100);
ctx.globalAlpha = 1.0;

// 导出为 PNG
canvas.toBuffer('image/png');
"""

result = ctx.eval(code)
with open('comprehensive_example.png', 'wb') as f:
    f.write(bytes(result))

print("✅ 综合绘图示例已保存到 comprehensive_example.png")
```

### 示例 2: 图像加载与处理

```python
from never_jscore import Context

ctx = Context(enable_extensions=True)

code = """
// 加载图像
const img = new Image();
img.src = 'input.png';

// 创建画布
const canvas = createCanvas(800, 600);
const ctx = canvas.getContext('2d');

// 绘制背景
ctx.fillStyle = '#ffffff';
ctx.fillRect(0, 0, 800, 600);

// 绘制原始图像
ctx.drawImage(img, 50, 50);

// 绘制缩放图像
ctx.drawImage(img, 300, 50, 200, 150);

// 绘制裁剪图像（从源图像截取部分）
ctx.drawImage(img, 0, 0, 100, 100, 550, 50, 150, 150);

// 像素操作：反色滤镜
const imageData = ctx.getImageData(50, 250, 200, 150);
const data = imageData.data;
for (let i = 0; i < data.length; i += 4) {
    data[i] = 255 - data[i];         // R
    data[i + 1] = 255 - data[i + 1]; // G
    data[i + 2] = 255 - data[i + 2]; // B
    // data[i + 3] 保持不变 (Alpha)
}
ctx.putImageData(imageData, 50, 250);

// 导出为 JPEG（质量 90）
canvas.toBuffer('image/jpeg');
"""

result = ctx.eval(code)
with open('image_processing.jpg', 'wb') as f:
    f.write(bytes(result))

print("✅ 图像处理示例已保存到 image_processing.jpg")
```

### 示例 3: 动画帧生成

```python
from never_jscore import Context
import os

ctx = Context(enable_extensions=True)

# 生成 60 帧动画
for frame in range(60):
    code = f"""
    const canvas = createCanvas(400, 400);
    const ctx = canvas.getContext('2d');

    // 背景
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, 400, 400);

    // 旋转的正方形
    const angle = ({frame} / 60) * Math.PI * 2;
    ctx.save();
    ctx.translate(200, 200);
    ctx.rotate(angle);

    ctx.fillStyle = '#00ff00';
    ctx.fillRect(-50, -50, 100, 100);

    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.strokeRect(-50, -50, 100, 100);
    ctx.restore();

    // 帧数显示
    ctx.fillStyle = '#ffffff';
    // ctx.font = '20px Arial'; // 文字渲染未实现
    // ctx.fillText('Frame: {frame}', 10, 30);

    canvas.toBuffer('image/png');
    """

    result = ctx.eval(code)
    with open(f'frames/frame_{frame:03d}.png', 'wb') as f:
        f.write(bytes(result))

print("✅ 60 帧动画已生成到 frames/ 目录")
```

### 示例 4: 图表绘制

```python
from never_jscore import Context

ctx = Context(enable_extensions=True)

code = """
const canvas = createCanvas(800, 600);
const ctx = canvas.getContext('2d');

// 背景
ctx.fillStyle = '#ffffff';
ctx.fillRect(0, 0, 800, 600);

// 数据
const data = [65, 59, 80, 81, 56, 55, 40];
const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

// 参数
const chartX = 100;
const chartY = 100;
const chartWidth = 600;
const chartHeight = 400;
const barWidth = chartWidth / data.length;
const maxValue = Math.max(...data);

// 绘制坐标轴
ctx.strokeStyle = '#333';
ctx.lineWidth = 2;
ctx.beginPath();
ctx.moveTo(chartX, chartY);
ctx.lineTo(chartX, chartY + chartHeight);
ctx.lineTo(chartX + chartWidth, chartY + chartHeight);
ctx.stroke();

// 绘制柱状图
data.forEach((value, index) => {
    const barHeight = (value / maxValue) * chartHeight;
    const x = chartX + index * barWidth + 10;
    const y = chartY + chartHeight - barHeight;

    // 柱子
    ctx.fillStyle = '#4CAF50';
    ctx.fillRect(x, y, barWidth - 20, barHeight);

    // 边框
    ctx.strokeStyle = '#2E7D32';
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, barWidth - 20, barHeight);
});

// 标题（文字渲染未实现，这里用矩形模拟）
ctx.fillStyle = '#333';
ctx.fillRect(300, 30, 200, 40);

canvas.toBuffer('image/png');
"""

result = ctx.eval(code)
with open('chart_example.png', 'wb') as f:
    f.write(bytes(result))

print("✅ 图表示例已保存到 chart_example.png")
```

---

## API 参考

### Canvas 类

#### 构造函数

```javascript
const canvas = new Canvas(width, height);
// 或使用工厂函数
const canvas = createCanvas(width, height);
```

**参数:**
- `width` (number): 画布宽度（像素），默认 300
- `height` (number): 画布高度（像素），默认 150

**示例:**
```javascript
const canvas = createCanvas(800, 600);
```

---

#### 属性

##### `canvas.width`
画布宽度（可读写）

```javascript
canvas.width = 1024;
console.log(canvas.width); // 1024
```

##### `canvas.height`
画布高度（可读写）

```javascript
canvas.height = 768;
console.log(canvas.height); // 768
```

---

#### 方法

##### `canvas.getContext(contextType)`
获取绘图上下文

**参数:**
- `contextType` (string): 上下文类型，目前仅支持 `"2d"`

**返回值:** `CanvasRenderingContext2D` | `null`

```javascript
const ctx = canvas.getContext('2d');
```

---

##### `canvas.toBuffer(mimeType)`
导出为图像缓冲区（Uint8Array）

**参数:**
- `mimeType` (string): MIME 类型
  - `"image/png"` - PNG 格式（默认）
  - `"image/jpeg"` - JPEG 格式
  - `"image/webp"` - WebP 格式

**返回值:** `Array<number>` (可转换为 Uint8Array)

```javascript
// PNG
const pngBuffer = canvas.toBuffer('image/png');

// JPEG (质量 90)
const jpegBuffer = canvas.toBuffer('image/jpeg');

// WebP (无损)
const webpBuffer = canvas.toBuffer('image/webp');
```

---

##### `canvas.toDataURL(type, quality)`
导出为 Base64 Data URL

**参数:**
- `type` (string): MIME 类型，默认 `"image/png"`
- `quality` (number): 图像质量 (0-1)，仅 JPEG 有效

**返回值:** `string`

```javascript
const dataUrl = canvas.toDataURL('image/png');
// data:image/png;base64,iVBORw0KG...

const jpegDataUrl = canvas.toDataURL('image/jpeg', 0.9);
```

---

##### `canvas.toBlob(callback, type, quality)`
导出为 Blob 对象（异步）

**参数:**
- `callback` (function): 回调函数 `(blob) => {}`
- `type` (string): MIME 类型
- `quality` (number): 图像质量

```javascript
canvas.toBlob((blob) => {
    console.log(blob.size);
}, 'image/png');
```

---

### CanvasRenderingContext2D 类

#### 属性

##### 填充和描边样式

```javascript
ctx.fillStyle = '#FF0000';        // CSS 颜色
ctx.fillStyle = 'rgb(255, 0, 0)';
ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';

ctx.strokeStyle = '#0000FF';
```

##### 线条样式

```javascript
ctx.lineWidth = 5;               // 线宽
ctx.lineCap = 'butt';            // 线帽: butt | round | square
ctx.lineJoin = 'miter';          // 线连接: miter | round | bevel
ctx.miterLimit = 10;             // 斜接限制
```

##### 虚线样式

```javascript
ctx.setLineDash([10, 5]);        // 虚线模式 [实线长度, 间隙长度, ...]
ctx.lineDashOffset = 0;          // 虚线偏移
const dash = ctx.getLineDash();  // 获取虚线模式
```

##### 透明度

```javascript
ctx.globalAlpha = 0.5;           // 全局透明度 (0-1)
```

##### 字体样式（未实现）

```javascript
ctx.font = '20px Arial';         // ❌ 未实现
ctx.textAlign = 'left';          // ❌ 未实现
ctx.textBaseline = 'alphabetic'; // ❌ 未实现
```

---

#### 矩形绘制方法

##### `ctx.fillRect(x, y, width, height)`
绘制填充矩形

```javascript
ctx.fillStyle = '#FF0000';
ctx.fillRect(50, 50, 200, 100);
```

##### `ctx.strokeRect(x, y, width, height)`
绘制描边矩形

```javascript
ctx.strokeStyle = '#0000FF';
ctx.lineWidth = 3;
ctx.strokeRect(50, 50, 200, 100);
```

##### `ctx.clearRect(x, y, width, height)`
清除矩形区域（变为透明）

```javascript
ctx.clearRect(50, 50, 200, 100);
```

---

#### 路径方法

##### `ctx.beginPath()`
开始新路径

```javascript
ctx.beginPath();
```

##### `ctx.closePath()`
闭合当前路径

```javascript
ctx.closePath();
```

##### `ctx.moveTo(x, y)`
移动到指定点（不绘制）

```javascript
ctx.moveTo(100, 100);
```

##### `ctx.lineTo(x, y)`
绘制直线到指定点

```javascript
ctx.beginPath();
ctx.moveTo(100, 100);
ctx.lineTo(200, 200);
ctx.stroke();
```

##### `ctx.arc(x, y, radius, startAngle, endAngle, anticlockwise)`
绘制圆弧

**参数:**
- `x`, `y`: 圆心坐标
- `radius`: 半径
- `startAngle`: 起始角度（弧度）
- `endAngle`: 结束角度（弧度）
- `anticlockwise`: 是否逆时针，默认 `false`

```javascript
// 绘制完整圆
ctx.beginPath();
ctx.arc(200, 200, 50, 0, Math.PI * 2);
ctx.fill();

// 绘制半圆
ctx.beginPath();
ctx.arc(300, 200, 50, 0, Math.PI);
ctx.stroke();
```

##### `ctx.arcTo(x1, y1, x2, y2, radius)`
绘制圆角（未实现）

```javascript
// ❌ 未实现
ctx.arcTo(100, 100, 200, 100, 20);
```

##### `ctx.quadraticCurveTo(cpx, cpy, x, y)`
绘制二次贝塞尔曲线

```javascript
ctx.beginPath();
ctx.moveTo(50, 100);
ctx.quadraticCurveTo(150, 50, 250, 100);
ctx.stroke();
```

##### `ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, x, y)`
绘制三次贝塞尔曲线

```javascript
ctx.beginPath();
ctx.moveTo(50, 100);
ctx.bezierCurveTo(100, 50, 200, 150, 250, 100);
ctx.stroke();
```

##### `ctx.rect(x, y, width, height)`
添加矩形路径

```javascript
ctx.beginPath();
ctx.rect(50, 50, 100, 100);
ctx.stroke();
```

##### `ctx.fill()`
填充当前路径

```javascript
ctx.beginPath();
ctx.arc(200, 200, 50, 0, Math.PI * 2);
ctx.fillStyle = '#FF0000';
ctx.fill();
```

##### `ctx.stroke()`
描边当前路径

```javascript
ctx.beginPath();
ctx.arc(200, 200, 50, 0, Math.PI * 2);
ctx.strokeStyle = '#0000FF';
ctx.lineWidth = 3;
ctx.stroke();
```

##### `ctx.clip()`
裁剪到当前路径

```javascript
ctx.beginPath();
ctx.arc(200, 200, 100, 0, Math.PI * 2);
ctx.clip();

// 后续绘制只在圆形区域内可见
ctx.fillStyle = '#FF0000';
ctx.fillRect(0, 0, 400, 400);
```

---

#### 变换方法

##### `ctx.save()`
保存当前绘图状态

```javascript
ctx.save();
ctx.fillStyle = '#FF0000';
ctx.restore(); // 恢复之前的状态
```

##### `ctx.restore()`
恢复之前保存的状态

```javascript
ctx.save();
ctx.fillStyle = '#FF0000';
ctx.restore();
console.log(ctx.fillStyle); // 恢复到保存前的值
```

##### `ctx.translate(x, y)`
平移坐标系

```javascript
ctx.translate(100, 100);
ctx.fillRect(0, 0, 50, 50); // 实际绘制在 (100, 100)
```

##### `ctx.rotate(angle)`
旋转坐标系

**参数:**
- `angle`: 旋转角度（弧度）

```javascript
ctx.translate(200, 200);
ctx.rotate(Math.PI / 4); // 旋转 45 度
ctx.fillRect(-25, -25, 50, 50);
```

##### `ctx.scale(x, y)`
缩放坐标系

```javascript
ctx.scale(2, 2); // 放大 2 倍
ctx.fillRect(0, 0, 50, 50); // 实际绘制 100x100
```

##### `ctx.setTransform(a, b, c, d, e, f)`
设置变换矩阵

```javascript
ctx.setTransform(1, 0, 0, 1, 100, 100); // 平移到 (100, 100)
```

##### `ctx.resetTransform()`
重置变换矩阵为单位矩阵

```javascript
ctx.resetTransform();
```

---

#### 图像方法

##### `ctx.drawImage(image, ...args)`
绘制图像

**三种调用形式:**

1. **基本形式:** `drawImage(image, dx, dy)`
```javascript
ctx.drawImage(img, 50, 50);
```

2. **缩放形式:** `drawImage(image, dx, dy, dWidth, dHeight)`
```javascript
ctx.drawImage(img, 50, 50, 200, 150);
```

3. **裁剪形式:** `drawImage(image, sx, sy, sWidth, sHeight, dx, dy, dWidth, dHeight)`
```javascript
// 从源图像 (10, 10) 处裁剪 100x100，绘制到 (50, 50)，缩放为 200x150
ctx.drawImage(img, 10, 10, 100, 100, 50, 50, 200, 150);
```

---

#### 像素操作方法

##### `ctx.createImageData(width, height)`
创建空白 ImageData 对象

```javascript
const imageData = ctx.createImageData(100, 100);
// 所有像素初始化为透明黑色 (0, 0, 0, 0)
```

##### `ctx.getImageData(sx, sy, sw, sh)`
获取像素数据

**返回值:** `ImageData` 对象

```javascript
const imageData = ctx.getImageData(50, 50, 100, 100);
console.log(imageData.width);  // 100
console.log(imageData.height); // 100
console.log(imageData.data);   // Uint8ClampedArray [R, G, B, A, ...]
```

##### `ctx.putImageData(imageData, dx, dy)`
放置像素数据

```javascript
const imageData = ctx.getImageData(0, 0, 100, 100);

// 反色滤镜
for (let i = 0; i < imageData.data.length; i += 4) {
    imageData.data[i] = 255 - imageData.data[i];       // R
    imageData.data[i + 1] = 255 - imageData.data[i + 1]; // G
    imageData.data[i + 2] = 255 - imageData.data[i + 2]; // B
}

ctx.putImageData(imageData, 0, 0);
```

---

#### 文字方法（未实现）

```javascript
ctx.fillText('Hello', 50, 50);     // ❌ 未实现
ctx.strokeText('World', 50, 100);  // ❌ 未实现
const metrics = ctx.measureText('Test'); // ❌ 未实现
```

---

### Image 类

#### 构造函数

```javascript
const img = new Image();
```

#### 属性

##### `img.src`
图像源（文件路径或 Data URL）

```javascript
img.src = 'path/to/image.png';
img.src = 'data:image/png;base64,...';
```

##### `img.width` (只读)
图像宽度

```javascript
console.log(img.width);
```

##### `img.height` (只读)
图像高度

```javascript
console.log(img.height);
```

##### `img.complete` (只读)
图像是否加载完成

```javascript
if (img.complete) {
    ctx.drawImage(img, 0, 0);
}
```

#### 事件

##### `img.onload`
图像加载完成回调

```javascript
img.onload = function() {
    console.log('Image loaded:', img.width, img.height);
};
img.src = 'image.png';
```

##### `img.onerror`
图像加载失败回调

```javascript
img.onerror = function(error) {
    console.error('Failed to load image:', error);
};
```

#### 方法

##### `img.dispose()`
释放图像内存

```javascript
img.dispose();
```

---

### 辅助函数

#### `loadImage(source)`
加载图像（返回 Promise）

**参数:**
- `source` (string | Uint8Array): 文件路径、Data URL 或图像缓冲区

**返回值:** `Promise<Image>`

```javascript
// 从文件加载
const img = await loadImage('image.png');

// 从 Buffer 加载
const buffer = new Uint8Array([...]);
const img = await loadImage(buffer);

// 从 Data URL 加载
const img = await loadImage('data:image/png;base64,...');
```

---

### ImageData 类

#### 构造函数

```javascript
const imageData = new ImageData(data, width, height);
```

**参数:**
- `data` (Uint8ClampedArray): 像素数据 (RGBA 格式)
- `width` (number): 宽度
- `height` (number): 高度

#### 属性

##### `imageData.data`
像素数据数组（Uint8ClampedArray）

每个像素 4 个字节：`[R, G, B, A, R, G, B, A, ...]`

```javascript
const imageData = ctx.getImageData(0, 0, 100, 100);
const pixels = imageData.data;

// 访问第一个像素
const r = pixels[0];
const g = pixels[1];
const b = pixels[2];
const a = pixels[3];

// 设置为红色
pixels[0] = 255; // R
pixels[1] = 0;   // G
pixels[2] = 0;   // B
pixels[3] = 255; // A
```

##### `imageData.width`
宽度

```javascript
console.log(imageData.width);
```

##### `imageData.height`
高度

```javascript
console.log(imageData.height);
```

---

## 兼容性对照表

### vs Web Canvas API

| 功能 | Web API | never-jscore | 兼容性 |
|------|---------|--------------|--------|
| **基础** |
| Canvas 创建 | `<canvas>` 或 `new OffscreenCanvas()` | `createCanvas(w, h)` | ⚠️ 语法不同 |
| 获取上下文 | `canvas.getContext('2d')` | `canvas.getContext('2d')` | ✅ 100% |
| 导出 PNG | `canvas.toDataURL()` | `canvas.toDataURL()` | ✅ 100% |
| 导出 JPEG | `canvas.toDataURL('image/jpeg')` | `canvas.toBuffer('image/jpeg')` | ✅ 支持 |
| 导出 WebP | `canvas.toDataURL('image/webp')` | `canvas.toBuffer('image/webp')` | ✅ 支持 |
| **矩形** |
| fillRect | ✅ | ✅ | ✅ 100% |
| strokeRect | ✅ | ✅ | ✅ 100% |
| clearRect | ✅ | ✅ | ✅ 100% |
| **路径** |
| beginPath | ✅ | ✅ | ✅ 100% |
| closePath | ✅ | ✅ | ✅ 100% |
| moveTo | ✅ | ✅ | ✅ 100% |
| lineTo | ✅ | ✅ | ✅ 100% |
| arc | ✅ | ✅ | ✅ 100% |
| arcTo | ✅ | ❌ | ❌ 未实现 |
| quadraticCurveTo | ✅ | ✅ | ✅ 100% |
| bezierCurveTo | ✅ | ✅ | ✅ 100% |
| rect | ✅ | ✅ | ✅ 100% |
| fill | ✅ | ✅ | ✅ 100% |
| stroke | ✅ | ✅ | ✅ 100% |
| clip | ✅ | ✅ | ✅ 100% |
| **样式** |
| fillStyle | ✅ | ✅ | ✅ 100% |
| strokeStyle | ✅ | ✅ | ✅ 100% |
| lineWidth | ✅ | ✅ | ✅ 100% |
| lineCap | ✅ | ⚠️ | ⚠️ 属性存在但未生效 |
| lineJoin | ✅ | ⚠️ | ⚠️ 属性存在但未生效 |
| globalAlpha | ✅ | ✅ | ✅ 100% |
| setLineDash | ✅ | ✅ | ✅ 100% |
| getLineDash | ✅ | ✅ | ✅ 100% |
| lineDashOffset | ✅ | ✅ | ✅ 100% |
| **变换** |
| save | ✅ | ✅ | ✅ 100% |
| restore | ✅ | ✅ | ✅ 100% |
| translate | ✅ | ✅ | ✅ 100% |
| rotate | ✅ | ✅ | ✅ 100% |
| scale | ✅ | ✅ | ✅ 100% |
| transform | ✅ | ❌ | ❌ 未实现 |
| setTransform | ✅ | ✅ | ✅ 100% |
| resetTransform | ✅ | ✅ | ✅ 100% |
| **图像** |
| drawImage | ✅ | ✅ | ✅ 100% |
| createImageData | ✅ | ✅ | ✅ 100% |
| getImageData | ✅ | ✅ | ✅ 100% |
| putImageData | ✅ | ✅ | ✅ 100% |
| **文字** |
| fillText | ✅ | ❌ | ❌ 未实现 |
| strokeText | ✅ | ❌ | ❌ 未实现 |
| measureText | ✅ | ❌ | ❌ 未实现 |
| **渐变** |
| createLinearGradient | ✅ | ❌ | ❌ 未实现 |
| createRadialGradient | ✅ | ❌ | ❌ 未实现 |
| createConicGradient | ✅ | ❌ | ❌ 未实现 |
| **图案** |
| createPattern | ✅ | ❌ | ❌ 未实现 |
| **阴影** |
| shadowBlur | ✅ | ❌ | ❌ 未实现 |
| shadowColor | ✅ | ❌ | ❌ 未实现 |
| shadowOffsetX | ✅ | ❌ | ❌ 未实现 |
| shadowOffsetY | ✅ | ❌ | ❌ 未实现 |

### vs node-canvas

| 功能 | node-canvas | never-jscore | 兼容性 |
|------|-------------|--------------|--------|
| 创建 Canvas | `createCanvas(w, h)` | `createCanvas(w, h)` | ✅ 100% |
| 图像加载 | `loadImage(src)` | `loadImage(src)` | ✅ 100% |
| PNG 导出 | `canvas.toBuffer('image/png')` | `canvas.toBuffer('image/png')` | ✅ 100% |
| JPEG 导出 | `canvas.toBuffer('image/jpeg')` | `canvas.toBuffer('image/jpeg')` | ✅ 100% |
| PDF 导出 | ✅ | ❌ | ❌ 不支持 |
| SVG 后端 | ✅ | ❌ | ❌ 仅支持光栅化 |
| 文字渲染 | ✅ | ❌ | ❌ 未实现 |
| 系统字体 | ✅ | ❌ | ❌ 未实现 |

---

## 性能优化建议

### 1. 批量绘制

**❌ 低效:**
```javascript
for (let i = 0; i < 1000; i++) {
    ctx.fillRect(i, i, 10, 10);
}
```

**✅ 高效:**
```javascript
ctx.beginPath();
for (let i = 0; i < 1000; i++) {
    ctx.rect(i, i, 10, 10);
}
ctx.fill();
```

### 2. 减少状态切换

**❌ 低效:**
```javascript
ctx.fillStyle = 'red';
ctx.fillRect(0, 0, 10, 10);
ctx.fillStyle = 'blue';
ctx.fillRect(10, 10, 10, 10);
ctx.fillStyle = 'red';
ctx.fillRect(20, 20, 10, 10);
```

**✅ 高效:**
```javascript
ctx.fillStyle = 'red';
ctx.fillRect(0, 0, 10, 10);
ctx.fillRect(20, 20, 10, 10);

ctx.fillStyle = 'blue';
ctx.fillRect(10, 10, 10, 10);
```

### 3. 避免频繁的 getImageData/putImageData

像素操作非常耗时，尽量一次性处理大块区域：

```javascript
// 一次性获取整个区域
const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
const data = imageData.data;

// 批量处理
for (let i = 0; i < data.length; i += 4) {
    data[i] = 255 - data[i];
}

// 一次性写回
ctx.putImageData(imageData, 0, 0);
```

### 4. 使用合适的图像格式

- **PNG**: 无损，支持透明，文件较大
- **JPEG**: 有损，不支持透明，文件小，适合照片
- **WebP**: 现代格式，压缩率高

```javascript
// 照片类图像使用 JPEG
const jpegBuffer = canvas.toBuffer('image/jpeg');

// 图标、UI 使用 PNG
const pngBuffer = canvas.toBuffer('image/png');

// 平衡质量和大小使用 WebP
const webpBuffer = canvas.toBuffer('image/webp');
```

---

## 已知限制

### 1. 文字渲染未实现
暂时无法使用 `fillText()`, `strokeText()`, `measureText()`

**替代方案:** 使用图像或预渲染文字

### 2. 渐变未实现
暂时无法使用 `createLinearGradient()`, `createRadialGradient()`

**替代方案:** 使用纯色或自己绘制渐变效果

### 3. 阴影未实现
暂时无法使用 `shadowBlur`, `shadowColor` 等

**替代方案:** 手动绘制阴影层

### 4. tiny-skia 限制
- 圆弧使用线段近似（质量略低于原生实现）
- 某些高级混合模式可能不支持

---

## 更新日志

### v2.5.2 (2025-01-XX)

**新增功能:**
- ✅ 虚线样式 (setLineDash, getLineDash, lineDashOffset)
- ✅ 裁剪功能 (clip)
- ✅ 像素操作 (getImageData, putImageData, createImageData)
- ✅ JPEG 格式支持（导入/导出）
- ✅ WebP 格式支持（导入/导出）

**改进:**
- 优化图像加载性能
- 修复 premultiplied alpha 转换问题

---

## 常见问题

### Q: 如何加载网络图片？

A: 先下载到本地，然后加载：

```python
import requests
from never_jscore import Context

# 下载图片
response = requests.get('https://example.com/image.png')
with open('temp.png', 'wb') as f:
    f.write(response.content)

# 在 JS 中加载
ctx = Context(enable_extensions=True)
code = """
const img = new Image();
img.src = 'temp.png';
// 使用 img...
"""
```

### Q: 为什么文字显示不出来？

A: 文字渲染功能尚未实现。建议使用图像或预渲染文字。

### Q: 如何绘制渐变？

A: 渐变功能尚未实现。可以手动绘制渐变效果：

```javascript
// 手动绘制线性渐变
for (let i = 0; i < 100; i++) {
    const ratio = i / 100;
    const r = Math.floor(255 * ratio);
    const g = Math.floor(128 * (1 - ratio));
    ctx.fillStyle = `rgb(${r}, ${g}, 0)`;
    ctx.fillRect(i, 0, 1, 100);
}
```

---

## 贡献指南

欢迎贡献代码！尚未实现的功能：

1. **文字渲染** - 需要集成字体引擎
2. **渐变** - tiny-skia 支持，需要封装
3. **图案填充** - tiny-skia 支持，需要封装
4. **阴影效果** - 需要实现高斯模糊

---

## 许可证

MIT License

---

## 链接

- **GitHub**: https://github.com/neverl805/never-jscore
- **文档**: https://github.com/neverl805/never-jscore/blob/main/README.md
- **问题反馈**: https://github.com/neverl805/never-jscore/issues
