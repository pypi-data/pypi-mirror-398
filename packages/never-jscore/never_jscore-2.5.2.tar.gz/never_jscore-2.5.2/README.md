# never_jscore

基于 Deno Core (V8) 的高性能 Python JavaScript 执行引擎，**专为 JS 逆向工程优化**。

[![PyPI](https://img.shields.io/pypi/v/never-jscore)](https://pypi.org/project/never-jscore/)
[![Python](https://img.shields.io/pypi/pyversions/never-jscore)](https://pypi.org/project/never-jscore/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**警告**：仅供技术研究和学习，请勿用于违法用途，后果自负。

- **技术交流群**：加微信 xu970821582
- **提醒: 基于pyo3库的更新迭代情况,个人推荐使用 python3.14 版本来使用此库,可能会避免很多奇怪的报错**

博客: http://www.ma2e.top/
---

## 为什么选择 never_jscore？

### 核心优势

| 特性 | never_jscore | PyMiniRacer | PyExecJS |
|------|--------------|-------------|----------|
| **Promise/async** | ✅ 完整支持 | ❌ 不支持 | ❌ 不支持 |
| **Hook 拦截** | ✅ 双模式：`$return()` + `$terminate()` | ❌ | ❌ |
| **确定性随机数** | ✅ 种子控制 | ❌ | ❌ |
| **Web API** | ✅ 完整（fetch/URL/crypto/Blob） | ❌ | ❌ |
| **Node.js 兼容** | ✅ require/npm 包 | ❌ | ⚠️ 部分 |
| **性能（1000次调用）** | **11ms** 🏆 | 38ms | 69473ms |
| **上下文隔离** | ✅ 独立 V8 Isolate | ✅ | ⚠️ 进程隔离 |
| **类型提示** | ✅ .pyi 文件 | ⚠️ 部分 | ❌ |

### 专为逆向工程设计

- 🎣 **双模式 Hook 拦截**：
  - `$return()` - 快速拦截，适合简单场景
  - `$terminate()` - **V8 强制终止，无法被 try-catch 捕获**（v2.4.3+ 新增）
- 🎲 **确定性调试**：固定随机数种子，轻松调试动态加密算法
- 🌐 **完整 Web API**：官方 Deno Web API 支持（fetch, URL, crypto 等）
- 📦 **Node.js 兼容**：`require()` 和 npm 包支持，可加载 jsdom 等
- ⚡ **极致性能**：Rust + V8 直接绑定，比 PyExecJS 快 100-300 倍
- 🔄 **现代 JS 支持**：完整的 Promise、async/await、fetch、localStorage

### 性能基准测试

![img.png](img.png)

| 测试项目 | never_jscore | PyMiniRacer | PyExecJS |
|---------|-------------|-------------|----------|
| 简单计算 | 0.007ms | 0.005ms | 2.3ms |
| 字符串操作 | **0.004ms** 🏆 | 0.008ms | 2.3ms |
| 数组操作 | **0.004ms** 🏆 | 0.006ms | 2.3ms |
| 复杂算法(1000次) | **0.0111s** 🏆 | 0.0383s | 69.4735s |
| Promise | **✅ 0.003ms** | ❌ 不支持 | ❌ 不支持 |

---

```python
import never_jscore

# API 完全兼容，无需修改代码
ctx = never_jscore.Context()

# 使用Web API
url = ctx.evaluate("new URL('https://example.com/path').href")
print(url)  # https://example.com/path

# TextEncoder/TextDecoder
encoded = ctx.evaluate("""
    const encoder = new TextEncoder();
    Array.from(encoder.encode('Hello'))
""")
print(encoded)  # [72, 101, 108, 108, 111]

# ReadableStream
result = ctx.evaluate("""
    const stream = new ReadableStream({
        start(controller) {
            controller.enqueue('chunk1');
            controller.enqueue('chunk2');
            controller.close();
        }
    });
    const reader = stream.getReader();
    async function read() {
        const chunks = [];
        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            chunks.push(value);
        }
        return chunks;
    }
    read()
""")
print(result)  # ['chunk1', 'chunk2']
```

**支持的 Web API：**
- ✅ URL / URLSearchParams / URLPattern
- ✅ TextEncoder / TextDecoder / TextEncoderStream / TextDecoderStream
- ✅ atob / btoa (Base64)
- ✅ console (log/info/warn/error/debug)
- ✅ Event / EventTarget / CustomEvent
- ✅ structuredClone
- ✅ AbortController / AbortSignal
- ✅ crypto.randomUUID() / crypto.getRandomValues()
- ✅ setTimeout / setInterval / clearTimeout / clearInterval
- ✅ performance.now() / mark / measure
- ✅ ReadableStream / WritableStream / TransformStream

详见：[Deno Web API 测试结果](docs/DENO_WEB_API_TEST_RESULTS.md)

### 🆕 Node.js 兼容模式 (v2.5.0+)

通过 `enable_node_compat=True` 启用完整的 Node.js 兼容层，支持 `require()` 和 npm 包！

```python
import never_jscore

# 启用 Node.js 兼容模式
ctx = never_jscore.Context(enable_node_compat=True)

# 使用 Node.js 内置模块
result = ctx.evaluate("""
    const path = require('path');
    const crypto = require('crypto');

    ({
        joined: path.join('a', 'b', 'c'),
        hash: crypto.createHash('md5').update('hello').digest('hex')
    })
""")
print(result)
# {'joined': 'a\\b\\c', 'hash': '5d41402abc4b2a76b9719d911017c592'}

# 加载 npm 包（如 jsdom）
ctx2 = never_jscore.Context(enable_node_compat=True)
result = ctx2.evaluate("""
    const { JSDOM } = require('jsdom');
    const dom = new JSDOM('<html><body><h1>Hello World</h1></body></html>');
    const document = dom.window.document;

    ({
        tagName: document.querySelector('h1').tagName,
        textContent: document.querySelector('h1').textContent
    })
""")
print(result)
# {'tagName': 'H1', 'textContent': 'Hello World'}
```

**支持的功能**：
- ✅ `require()` 函数
- ✅ Node.js 内置模块 (path, fs, crypto, buffer, stream, etc.)
- ✅ npm 包加载 (jsdom, lodash, 等)
- ✅ `__dirname` / `__filename`
- ✅ `process.env` / `process.cwd()`
- ✅ `Buffer` 全局对象

**注意**：
- 需要在项目目录下有 `node_modules` 文件夹
- 使用前先运行 `npm install` 安装所需的包

---

## 快速开始

### 安装

```bash
pip install never-jscore
```

**支持平台**：Windows、Linux、macOS | **Python 版本**：3.8+

### 基本用法

```python
import never_jscore

# 创建独立的 JavaScript 执行环境
ctx = never_jscore.Context()

# 方式 1: 编译代码到全局作用域
ctx.compile("""
    function encrypt(text, key) {
        // 你的加密逻辑
        return btoa(text + key);
    }
""")

# 调用已定义的函数
result = ctx.call("encrypt", ["hello", "secret"])
print(result)  # 'aGVsbG9zZWNyZXQ='

# 方式 2: 一次性求值（不污染全局）
result = ctx.evaluate("1 + 2 + 3")
print(result)  # 6
```

### Promise 和 async/await（自动等待）

```python
ctx = never_jscore.Context()

# 定义异步函数
ctx.compile("""
    async function fetchUserData(userId) {
        // 模拟异步操作
        return await Promise.resolve({
            id: userId,
            name: "User" + userId,
            token: Math.random().toString(36)
        });
    }
""")

# 自动等待 Promise 完成
user = ctx.call("fetchUserData", [12345])
print(user)  # {'id': 12345, 'name': 'User12345', 'token': '0.xyz...'}

# Promise 链式调用
result = ctx.evaluate("""
    Promise.resolve(10)
        .then(x => x * 2)
        .then(x => x + 5)
""")
print(result)  # 25
```

---

## 高级功能

### 🎣 Hook 拦截：提取加密数据（基于新扩展架构）

在 JS 逆向中，经常需要拦截某个函数的调用并提取参数或返回值。never_jscore v2.5.0 采用**全新的模块化扩展架构**，提供**两种 Hook 模式**：

#### 模式 1: `$return()` - 快速拦截（可被 try-catch 捕获）

**来自**: Core Extension (`src/ext/core/`)

```python
ctx = never_jscore.Context()

# 适合简单场景
encrypted_data = ctx.evaluate("""
    (async () => {
        const originalSend = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.send = function(data) {
            $return({
                url: this._url,
                encrypted: data
            });
        };

        const xhr = new XMLHttpRequest();
        xhr.open('POST', 'https://api.example.com/login');
        xhr.send(encryptedPayload);
    })()
""")

print(f"拦截到的加密数据: {encrypted_data['encrypted']}")
```

#### 模式 2: `$terminate()` - 强制终止（**无法被 try-catch 捕获** ⭐ v2.5.0 增强）

**来自**: Hook Extension (`src/ext/hook/`)
**关键特性：** 使用 V8 `terminate_execution()`，绕过所有 try-catch 防护！

```python
import json

ctx = never_jscore.Context()
ctx.clear_hook_data()  # 清空之前的数据（可选，会自动清空）

# Hook XMLHttpRequest.send
ctx.compile("""
    XMLHttpRequest.prototype.send = function(data) {
        // ⚡ 使用 $terminate 强制终止，无法被 try-catch 捕获
        $terminate({
            url: this._url,
            method: this._method,
            encrypted: data
        });
    };
""")

# 执行目标代码（即使有 try-catch 也会被终止）
try:
    ctx.evaluate("""
        try {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', 'https://api.example.com/login');
            xhr.send(encryptedPayload);
        } catch (e) {
            // ❌ 这里不会执行 - $terminate 无法被捕获！
            console.log("Will not execute");
        }
    """)
except Exception as e:
    # ✅ Python 端捕获到终止
    print(f"JS 被强制终止: {e}")

# 获取拦截的数据
hook_data = ctx.get_hook_data()
if hook_data:
    data = json.loads(hook_data)
    print(f"拦截到的加密数据: {data['encrypted']}")

# ⚠️ 注意：每次 evaluate()/call() 前会自动清空 hook 数据
# 如果需要保留上一次的数据，必须在下一次执行前先读取
```

**两种模式对比：**

| 特性 | `$return()` | `$terminate()` ⭐ |
|------|-------------|-------------------|
| 速度 | ✅ 快 | ✅ 快 |
| try-catch | ⚠️ 可被捕获 | ✅ **无法被捕获** |
| 适用场景 | 简单 Hook | 对抗加固代码 |
| 数据获取 | 直接返回值 | `ctx.get_hook_data()` |
| 多次执行 | ✅ 可复用 Context | ⚠️ 建议清理后复用 |

**Hook API 总览**：
- **模式 1 (Core Extension)：** `$return(value)`, `$exit(value)`, `__neverjscore_return__(value)`
- **模式 2 (Hook Extension)：** `$terminate(value)`, `__saveAndTerminate__(value)` ⭐ 架构增强

**典型应用场景**：
- ✅ 拦截网络请求的加密参数
- ✅ 提取中间加密结果（如 AES/RSA 的输出）
- ✅ **绕过 try-catch 防护**（使用 `$terminate`）
- ✅ **对抗加固的商业代码**（使用 `$terminate`）

### 🎲 确定性随机数：调试动态加密

许多加密算法会混入随机数（nonce/salt），导致每次结果不同，难以调试。使用 `random_seed` 可以让所有随机数固定：

```python
# 使用固定种子
ctx = never_jscore.Context(random_seed=12345)

# 每次运行结果完全相同
r1 = ctx.evaluate("Math.random()")     # 0.8831156266...
r2 = ctx.evaluate("Math.random()")     # 0.5465919174...

# 新 Context 使用相同种子，结果也相同
ctx2 = never_jscore.Context(random_seed=12345)
r3 = ctx2.evaluate("Math.random()")    # 0.8831156266... (与 r1 相同!)

# 适用于所有随机 API
uuid = ctx.evaluate("crypto.randomUUID()")          # 固定的 UUID
random_bytes = ctx.evaluate("crypto.getRandomValues(new Uint8Array(4))")
```

**影响的 API**：
- `Math.random()`
- `crypto.randomUUID()`
- `crypto.getRandomValues()`

### 🌐 完整的 Web API：零配置补环境

启用扩展后（默认开启），自动提供浏览器和 Node.js 环境：

```python
ctx = never_jscore.Context(enable_extensions=True)  # 默认就是 True

# ✅ Node.js 模块系统
result = ctx.evaluate("""
    const CryptoJS = require('crypto-js');
    CryptoJS.AES.encrypt('message', 'secret').toString();
""")

# ✅ 网络请求
result = ctx.evaluate("""
    (async () => {
        const res = await fetch('https://api.github.com/users/github');
        const data = await res.json();
        return data.login;
    })()
""")

# ✅ 浏览器存储
ctx.eval("localStorage.setItem('token', 'abc123')")
token = ctx.evaluate("localStorage.getItem('token')")

# ✅ 浏览器环境对象
env_info = ctx.evaluate("""
    ({
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        cookieEnabled: navigator.cookieEnabled,
        language: navigator.language,
        href: location.href,
        origin: location.origin
    })
""")

# ✅ 加密和编码
result = ctx.evaluate("""
    const hash = md5('hello');
    const b64 = btoa(hash);
    const url = encodeURIComponent('https://example.com?q=测试');
    ({hash, b64, url})
""")
```

**内置 Web API 列表**：

<details>
<summary><b>展开查看完整 API 列表</b></summary>

- **Node.js 兼容**
  - `require()` - CommonJS 模块加载
  - `fs` - 文件系统（readFileSync, writeFileSync）
  - `path` - 路径操作
  - `Buffer` - 二进制数据处理
  - `process` - 进程信息

- **浏览器存储**
  - `localStorage` - 持久化存储
  - `sessionStorage` - 会话存储

- **浏览器环境**
  - `navigator` - 浏览器信息（userAgent, platform, language, cookieEnabled）
  - `location` - URL 信息（href, origin, hostname, pathname）
  - `document` - 文档对象（部分属性）
  - `window` - 全局对象
  - `screen` - 屏幕信息

- **网络请求**
  - `fetch()` - 现代 HTTP 客户端
  - `XMLHttpRequest` - 传统 Ajax
  - `Response`, `Request`, `Headers` - Fetch API 相关

- **URL 和表单**
  - `URL` - URL 解析和构造
  - `URLSearchParams` - 查询字符串处理
  - `FormData` - 表单数据
  - `Blob` - 二进制大对象

- **事件系统**
  - `Event` - 事件对象
  - `EventTarget` - 事件目标
  - `addEventListener`, `removeEventListener`, `dispatchEvent`

- **加密和哈希**
  - `md5()`, `sha1()`, `sha256()` - 哈希函数
  - `btoa()`, `atob()` - Base64 编解码
  - `crypto.randomUUID()` - UUID 生成
  - `crypto.getRandomValues()` - 随机数

- **编码和解码**
  - `encodeURIComponent()`, `decodeURIComponent()`
  - `encodeURI()`, `decodeURI()`
  - `TextEncoder`, `TextDecoder` - 文本编解码
  - `escape()`, `unescape()` - 遗留编码

- **定时器**
  - `setTimeout()`, `clearTimeout()`
  - `setInterval()`, `clearInterval()`
  - `queueMicrotask()`

- **性能监控**
  - `performance.now()` - 高精度时间
  - `performance.mark()` - 性能标记
  - `performance.measure()` - 性能测量
  - `Date.now()` - 时间戳

</details>

### 🔬 V8 堆内存分析：专业级内存调试

never_jscore 提供 V8 引擎的原生内存分析 API，可以深入分析 JavaScript 内存使用情况：

```python
ctx = never_jscore.Context()

# 1. 获取 V8 堆统计信息
heap_stats = ctx.get_heap_statistics()

print(f"总堆大小: {heap_stats['total_heap_size'] / 1024 / 1024:.2f} MB")
print(f"已使用堆: {heap_stats['used_heap_size'] / 1024 / 1024:.2f} MB")
print(f"堆大小限制: {heap_stats['heap_size_limit'] / 1024 / 1024:.2f} MB")
print(f"物理内存: {heap_stats['total_physical_size'] / 1024 / 1024:.2f} MB")
print(f"外部内存: {heap_stats['external_memory'] / 1024:.2f} KB")
print(f"使用率: {heap_stats['used_heap_size'] / heap_stats['total_heap_size'] * 100:.1f}%")

# 2. 导出堆快照到 Chrome DevTools
ctx.take_heap_snapshot("heap_snapshot.heapsnapshot")

# 然后在 Chrome DevTools 中分析：
# 1. 打开 Chrome -> F12 -> Memory 标签
# 2. 点击 "Load" 按钮加载快照文件
# 3. 查看对象分配、内存泄漏、循环引用等
```

**V8 堆统计字段说明**：
- `total_heap_size` - V8 堆总大小（包括未使用空间）
- `used_heap_size` - 已使用的堆内存
- `heap_size_limit` - V8 堆大小上限
- `total_physical_size` - 实际物理内存占用
- `malloced_memory` - 通过 malloc 分配的内存
- `external_memory` - 外部对象占用的内存
- `number_of_native_contexts` - 原生上下文数量

**实战场景：检测内存泄漏**

```python
ctx = never_jscore.Context()

# 基准快照
ctx.take_heap_snapshot("before.heapsnapshot")
heap_before = ctx.get_heap_statistics()

# 执行可能泄漏的代码
ctx.evaluate("""
    globalThis.leakedData = [];
    for (let i = 0; i < 10000; i++) {
        leakedData.push({
            id: i,
            data: new Array(100).fill(i)
        });
    }
""")

# 泄漏后快照
ctx.take_heap_snapshot("after.heapsnapshot")
heap_after = ctx.get_heap_statistics()

# 分析内存增长
growth = heap_after['used_heap_size'] - heap_before['used_heap_size']
print(f"内存增长: {growth / 1024 / 1024:.2f} MB")

# 在 Chrome DevTools 中对比两个快照，找出泄漏对象
```

---

## 核心 API 参考

### Context 类

```python
never_jscore.Context(
    enable_extensions: bool = True,
    enable_logging: bool = False,
    random_seed: int | None = None
)
```

**参数**：
- `enable_extensions` - 是否启用 Web API 扩展（默认 `True`，推荐开启）
- `enable_logging` - 是否打印 Rust 操作日志（默认 `False`，调试时可开启）
- `random_seed` - 随机数种子（默认 `None` 为真随机，传入整数则固定）

**方法详解**：

| 方法 | 用途 | 场景 |
|------|------|------|
| `compile(code)` | 编译代码到**全局作用域** | 定义函数、加载 JS 库 |
| `evaluate(code)` | 求值并返回结果（**不污染全局**） | 一次性执行、获取表达式值 |
| `eval(code)` | 执行代码（可选返回值） | 执行语句、修改全局变量 |
| `call(name, args)` | 调用已定义的函数 | 多次调用同一函数 |
| `gc()` | 请求垃圾回收 | 长时间运行时手动释放内存 |
| `get_stats()` | 获取统计信息 | 性能分析、调用计数 |
| `reset_stats()` | 重置统计 | 基准测试前清零 |
| `get_heap_statistics()` | **获取 V8 堆统计信息** | **内存监控、泄漏分析** |
| `take_heap_snapshot(path)` | **导出 V8 堆快照** | **Chrome DevTools 内存分析** |

**compile() vs evaluate() 的关键区别**：

```python
ctx = never_jscore.Context()

# compile: 只运行微任务（microtask），不等待 setTimeout
ctx.compile("""
    function delayedEncrypt(data) {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(btoa(data));
            }, 100);
        });
    }
""")
# ↑ 这里只是定义函数，不会等待 setTimeout

# call: 运行完整事件循环，会等待 setTimeout 和 Promise
result = ctx.call("delayedEncrypt", ["hello"])  # 会等待 100ms
print(result)  # 'aGVsbG8='

# evaluate: 也会等待完整事件循环
result = ctx.evaluate("""
    (async () => {
        await new Promise(r => setTimeout(r, 1000));
        return 'done';
    })()
""")  # 会等待 1 秒
print(result)  # 'done'
```

**上下文管理器（自动清理）**：

```python
# ✅ 单次使用：安全
with never_jscore.Context() as ctx:
    result = ctx.evaluate("1 + 2")
    print(result)  # 3
# 退出 with 块后自动释放资源
```

**⚠️ 重要警告：不要在循环中直接使用 `with` 语句！**

```python
# ❌ 错误用法：会崩溃！
for i in range(10):
    with never_jscore.Context() as ctx:  # HandleScope 错误
        result = ctx.evaluate(f"{i} + 1")

# ✅ 正确用法 1：包装在函数中
def process(data):
    with never_jscore.Context() as ctx:
        return ctx.evaluate(f"{data} + 1")

for i in range(100):
    result = process(i)  # 安全

# ✅ 正确用法 2：显式 del
for i in range(100):
    ctx = never_jscore.Context()
    result = ctx.evaluate(f"{i} + 1")
    del ctx  # 立即清理

# ✅ 正确用法 3：复用 Context（推荐，性能最佳）
ctx = never_jscore.Context()
for i in range(1000):
    result = ctx.evaluate(f"{i} + 1")
del ctx
```

**原因**：Python 的 `with` 语句调用 `__exit__` 但不保证立即销毁对象，循环中快速创建多个 Context 会导致 V8 HandleScope 累积崩溃。详见：[docs/CONTEXT_MANAGER_WARNING.md](docs/CONTEXT_MANAGER_WARNING.md)

### 类型转换表

| Python 类型 | JavaScript 类型 | 示例 |
|------------|----------------|------|
| `None` | `null` | `None` → `null` |
| `bool` | `boolean` | `True` → `true` |
| `int` | `number` | `42` → `42` |
| `float` | `number` | `3.14` → `3.14` |
| `str` | `string` | `"hello"` → `"hello"` |
| `list` | `Array` | `[1, 2]` → `[1, 2]` |
| `dict` | `Object` | `{"a": 1}` → `{a: 1}` |

**嵌套结构自动转换**：

```python
ctx = never_jscore.Context()

# Python → JavaScript
result = ctx.call("processData", [{
    "users": [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False}
    ],
    "count": 2
}])

# JavaScript → Python
data = ctx.evaluate("""
    ({
        status: 'success',
        data: [1, 2, 3],
        meta: {timestamp: Date.now()}
    })
""")
print(type(data))  # <class 'dict'>
print(data['data'])  # [1, 2, 3]
```

---

## 重要使用限制

### ⚠️ HandleScope 错误：循环中创建 Context

**问题**：在循环中反复创建 Context 而不释放会导致 V8 HandleScope 崩溃。

```python
# ❌ 错误：会在第 10-20 次迭代时崩溃
for i in range(100):
    ctx = never_jscore.Context()
    result = ctx.call("encrypt", [data])
    # 忘记 del ctx，导致 V8 Isolate 堆积
```

**解决方案（按推荐度排序）**：

<details>
<summary><b>方案 1：循环外创建 Context（最推荐）</b></summary>

```python
# ✅ 最佳实践：复用 Context
ctx = never_jscore.Context()
ctx.compile(js_code)  # 一次性加载 JS 代码

for i in range(10000):  # 可以循环任意多次
    result = ctx.call("encrypt", [data])
    print(result)
```

**性能**: 最快（无创建开销）
**适用**: 90% 的场景

</details>

<details>
<summary><b>方案 2：显式 del（需要每次创建）</b></summary>

```python
# ✅ 每次循环后立即释放
for i in range(100):
    ctx = never_jscore.Context()
    result = ctx.call("encrypt", [data])
    del ctx  # 立即释放，不依赖 GC
```

**性能**: 慢（每次创建开销 ~1-2ms）
**适用**: 必须隔离的场景（如多租户）

</details>

<details>
<summary><b>方案 3：函数作用域 + with（推荐）</b></summary>

```python
# ✅ 函数退出时自动清理
def encrypt_data(data):
    with never_jscore.Context() as ctx:
        ctx.compile(js_code)
        return ctx.call("encrypt", [data])

for i in range(1000):
    result = encrypt_data(data)
```

**性能**: 慢（同方案 2）
**适用**: 需要隔离且代码整洁

</details>

<details>
<summary><b>方案 4：多线程用 ThreadLocal（高级）</b></summary>

```python
# ✅ 每个线程复用一个 Context
import threading
from concurrent.futures import ThreadPoolExecutor

thread_local = threading.local()

def get_context():
    if not hasattr(thread_local, 'ctx'):
        thread_local.ctx = never_jscore.Context()
        thread_local.ctx.compile(js_code)
    return thread_local.ctx

def worker(data):
    ctx = get_context()
    return ctx.call("encrypt", [data])

# 4 个线程并行处理
with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(worker, data_list)
```

**性能**: 快（每线程一次创建）
**适用**: 多线程高并发场景

</details>

详见：[docs/HANDLESCOPE_ERROR_SOLUTIONS.md](docs/HANDLESCOPE_ERROR_SOLUTIONS.md)

### ⚠️ with 语句限制：不能直接在循环中使用

**问题**：Python 的 `with` 语句退出后，对象不会立即销毁（依赖 GC），导致循环中堆积。

```python
# ❌ 错误：会在第 5-10 次迭代时崩溃
for i in range(100):
    with never_jscore.Context() as ctx:
        result = ctx.call("encrypt", [data])
    # with 退出后对象还在内存中，未被 GC
```

**解决方案**：用函数包装 `with` 块

```python
# ✅ 正确：函数作用域强制清理
def process(data):
    with never_jscore.Context() as ctx:
        ctx.compile(js_code)
        return ctx.call("encrypt", [data])

for i in range(10000):  # 可以循环任意多次
    result = process(data)
```

**原理**：函数退出时，局部变量立即销毁，不依赖 GC。

详见：[docs/WITH_STATEMENT_LIMITATION.md](docs/WITH_STATEMENT_LIMITATION.md)

### ⚠️ 多线程使用

**Context 不是线程安全的**，不能跨线程共享，但可以多线程并行（每线程一个 Context）。

**推荐模式**：ThreadLocal 复用

```python
import threading
from concurrent.futures import ThreadPoolExecutor

thread_local = threading.local()

def get_context():
    if not hasattr(thread_local, 'ctx'):
        # 每个线程首次调用时创建 Context
        thread_local.ctx = never_jscore.Context()
        thread_local.ctx.compile(js_code)
    return thread_local.ctx

def worker(item):
    ctx = get_context()
    return ctx.call("process", [item])

# 4 线程并行，每个线程复用自己的 Context
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(worker, range(100)))
```

详见：[docs/MULTITHREADING.md](docs/MULTITHREADING.md)

---

## 常见问题 (FAQ)

<details>
<summary><b>Q: 什么时候选择 never_jscore 而不是 PyMiniRacer？</b></summary>

**选择 never_jscore**：
- ✅ 需要 Promise/async 支持（现代 JS 库必须）
- ✅ 需要浏览器/Node.js 环境（补环境）
- ✅ 需要 Hook 拦截功能（逆向神器）
- ✅ 需要确定性随机数（调试加密算法）
- ✅ 需要开箱即用（零配置）

**选择 PyMiniRacer**：
- ✅ 只需要执行简单同步 JS
- ✅ 追求极致性能（理论上比 never_jscore 快 5-10%）
- ✅ 不需要任何 Web API

</details>

<details>
<summary><b>Q: 为什么比 PyExecJS 快 100-300 倍？</b></summary>

**PyExecJS 架构**：
```
Python → 启动进程 → 外部 JS 引擎 → JSON 序列化 → 进程通信 → Python
```
每次调用都有进程启动和 IPC 开销（~2ms）。

**never_jscore 架构**：
```
Python → Rust FFI → V8 引擎 → Rust FFI → Python
```
直接内存通信，无进程开销（~0.004ms）。

</details>

<details>
<summary><b>Q: compile() 和 evaluate() 有什么区别？</b></summary>

**核心区别**：事件循环的运行深度。

| | compile() | evaluate() / call() |
|---|-----------|---------------------|
| **用途** | 定义函数、加载库 | 执行代码、获取结果 |
| **全局作用域** | ✅ 影响 | ❌ 不影响（evaluate） |
| **运行微任务** | ✅ queueMicrotask | ✅ queueMicrotask |
| **运行宏任务** | ❌ 不等待 setTimeout | ✅ 等待 setTimeout |
| **等待 Promise** | ❌ 不等待 | ✅ 自动等待 |

**典型用法**：
```python
# 第一步：用 compile 加载 JS 库（快）
ctx.compile("""
    function encrypt(data) {
        return new Promise(resolve => {
            setTimeout(() => resolve(btoa(data)), 100);
        });
    }
""")

# 第二步：用 call 调用函数（自动等待 Promise）
result = ctx.call("encrypt", ["hello"])  # 会等待 100ms
```

</details>

<details>
<summary><b>Q: with 语句为什么在循环中会崩溃？</b></summary>

**原因**：Python 的 `with` 只调用 `__exit__`，不保证对象立即销毁。

```python
for i in range(10):
    with never_jscore.Context() as ctx:
        pass
    # 此时 ctx 对象还在内存中，等待 GC
    # V8 Isolate 累积到一定数量就崩溃
```

**解决方案**：用函数作用域包装，函数退出时强制销毁局部变量。

```python
def run():
    with never_jscore.Context() as ctx:
        return ctx.evaluate("1 + 1")

for i in range(10000):
    result = run()  # 每次函数退出，ctx 立即销毁
```

</details>

<details>
<summary><b>Q: 如何调试 "执行结果和浏览器不一致" 的问题？</b></summary>

**步骤 1**：开启日志查看 Rust 操作调用
```python
ctx = never_jscore.Context(enable_logging=True)
```

**步骤 2**：使用 Hook 拦截中间值
```python
result = ctx.evaluate("""
    const step1 = someFunction(input);
    $return({step1});  // 提前返回中间结果

    const step2 = anotherFunction(step1);
    return step2;
""")
print("中间值:", result['step1'])
```

**步骤 3**：固定随机数排除随机因素
```python
ctx = never_jscore.Context(random_seed=12345)
```

**步骤 4**：检查环境对象是否缺失
```python
env = ctx.evaluate("[typeof navigator, typeof localStorage, typeof fetch]")
print(env)  # 应该都是 'object' 或 'function'
```

</details>

<details>
<summary><b>Q: 支持哪些 Node.js 模块？</b></summary>

**内置模块**（无需安装）：
- `fs` - 文件系统（同步方法）
- `path` - 路径处理
- `crypto` - 部分加密功能
- `buffer` - Buffer 类

**require() 第三方库**（需要先安装到 node_modules）：
```bash
npm install crypto-js
```

```python
ctx.evaluate("""
    const CryptoJS = require('crypto-js');
    CryptoJS.AES.encrypt('data', 'key').toString();
""")
```

**不支持**：异步模块（如 axios、node-fetch），因为 require 是同步的。

</details>

<details>
<summary><b>Q: 如何处理大量数据（避免内存溢出）？</b></summary>

**方法 1**：批量处理 + 手动 GC
```python
ctx = never_jscore.Context()
ctx.compile(js_code)

for batch in chunks(data, 1000):  # 每 1000 条处理一次
    results = [ctx.call("process", [item]) for item in batch]
    ctx.gc()  # 手动触发垃圾回收
    save_results(results)
```

**方法 2**：多进程并行（绕过 GIL）
```python
from multiprocessing import Pool

def process_chunk(chunk):
    ctx = never_jscore.Context()
    ctx.compile(js_code)
    return [ctx.call("process", [item]) for item in chunk]

with Pool(4) as pool:
    results = pool.map(process_chunk, chunks(data, 1000))
```

</details>

---

## 示例代码和测试

### 📦 完整测试套件（`tests/` 目录）

我们提供了 **10 个全面的测试文件**，展示所有核心功能的使用方法：

| 测试文件 | 功能说明 | 运行命令 |
|---------|---------|----------|
| `test_browser_protection.py` | 浏览器环境防检测 | `python tests/test_browser_protection.py` |
| `test_proxy_logging.py` | Proxy 日志系统 | `python tests/test_proxy_logging.py` |
| `test_random_seed.py` | 确定性随机数 | `python tests/test_random_seed.py` |
| `test_terminate_hook.py` | Hook 拦截系统 | `python tests/test_terminate_hook.py` |
| `test_async_promise.py` | Promise/async/await | `python tests/test_async_promise.py` |
| `test_web_apis.py` | Web API（fetch, localStorage 等） | `python tests/test_web_apis.py` |
| `test_context_management.py` | Context 管理和 with 语句 | `python tests/test_context_management.py` |
| `test_multithreading.py` | 多线程使用 | `python tests/test_multithreading.py` |
| `test_xmlhttprequest.py` | XMLHttpRequest | `python tests/test_xmlhttprequest.py` |
| `test_memory_and_performance.py` | 内存监控和性能调优 | `python tests/test_memory_and_performance.py` |

**运行所有测试：**
```bash
python tests/run_all_tests.py
```

### 🎯 快速示例

#### 1. Context 管理（with 语句）

```python
import never_jscore

# ✅ 正确：单次使用
with never_jscore.Context() as ctx:
    result = ctx.evaluate("1 + 2")

# ✅ 正确：循环复用 Context（最推荐）
ctx = never_jscore.Context()
for i in range(1000):
    result = ctx.call("func", [i])
del ctx

# ✅ 正确：函数作用域 + with
def process(data):
    with never_jscore.Context() as ctx:
        return ctx.evaluate(f"transform({data})")

for i in range(100):
    process(i)

# ❌ 错误：直接在循环中用 with（会崩溃！）
for i in range(100):  # ❌ 危险
    with never_jscore.Context() as ctx:
        ctx.evaluate(...)
```

#### 2. 多线程使用

```python
from concurrent.futures import ThreadPoolExecutor
import threading

# ✅ 最佳实践：ThreadLocal + Context 复用
thread_local = threading.local()

def get_context():
    if not hasattr(thread_local, 'ctx'):
        thread_local.ctx = never_jscore.Context()
        thread_local.ctx.compile(js_code)
    return thread_local.ctx

def worker(data):
    ctx = get_context()  # 每个线程复用自己的 Context
    return ctx.call("process", [data])

# 使用线程池并行处理
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(worker, data_list))
```

#### 3. 内存监控和性能调优

```python
# V8 堆统计信息
ctx = never_jscore.Context()
heap_stats = ctx.get_heap_statistics()
print(f"总堆大小: {heap_stats['total_heap_size'] / 1024 / 1024:.2f} MB")
print(f"已使用堆: {heap_stats['used_heap_size'] / 1024 / 1024:.2f} MB")
print(f"堆大小限制: {heap_stats['heap_size_limit'] / 1024 / 1024:.2f} MB")
print(f"使用率: {heap_stats['used_heap_size'] / heap_stats['total_heap_size'] * 100:.1f}%")

# 导出 Chrome DevTools 堆快照（分析内存泄漏）
ctx.take_heap_snapshot("heap_snapshot.heapsnapshot")
# 然后在 Chrome DevTools -> Memory -> Load 加载快照进行分析

# 定期触发 GC 清理内存
for i in range(1000):
    ctx.call("process", [i])
    if i % 100 == 0:
        ctx.gc()  # 每 100 次清理一次

# 获取统计信息
stats = ctx.get_stats()
print(f"evaluate: {stats['evaluate_count']} 次")
print(f"call: {stats['call_count']} 次")

# 启用日志进行调试
ctx = never_jscore.Context(enable_logging=True)
ctx.evaluate("console.log('Hello')")  # 会输出 Rust 日志
```

#### 4. XMLHttpRequest 使用

```python
ctx = never_jscore.Context()

result = ctx.evaluate("""
    (async () => {
        return new Promise((resolve) => {
            const xhr = new XMLHttpRequest();

            xhr.onload = function() {
                resolve({
                    status: xhr.status,
                    data: JSON.parse(xhr.responseText)
                });
            };

            xhr.open('GET', 'https://api.example.com/data');
            xhr.setRequestHeader('Authorization', 'Bearer token');
            xhr.send();
        });
    })()
""")

print(f"状态: {result['status']}")
print(f"数据: {result['data']}")
```

### 📚 详细文档

查看 `tests/README.md` 获取每个测试的详细说明和示例代码。

---

## 更新日志

### v2.5.1 (2025-11-30)
- 🔍 **Proxy 日志系统重构**
- 🔧 修复 localStorage 和 sessionStorage 函数方法没有暴露的问题
- 
### v2.5.0 (2025-11-30) 🎉 重大更新

- 🏗️ **全新模块化扩展架构** (参考 [rustyscript](https://github.com/rscarson/rustyscript))
  - **Core Extension** (`src/ext/core/`): 核心功能 (`$return`, `$exit`, `$storeResult`)
  - **Hook Extension** (`src/ext/hook/`): Hook 拦截 (`$terminate`, `__saveAndTerminate__`)
  - 完整集成 Deno 的 Node.js 兼容层，支持 require() 和 npm 包加载。
  - 统一的 `ExtensionTrait` 接口，易于维护和扩展
  - 支持的功能：
  - ✅ require() 函数
  - ✅ Node.js 内置模块 (path, fs, crypto, buffer, stream, url, util, events 等)
  - ✅ npm 包加载 (jsdom, lodash, crypto-js 等)
  - ✅ __dirname / __filename
  - ✅ process.env / process.cwd()
  - ✅ Buffer 全局对象
  - ✅ package.json exports 字段解析（含子路径）


- 🛡️ **API 保护增强** (`src/ext/api_protection.js`)
  - 新增 10+ 反检测工具函数
  - `makeNative()` - 函数显示为原生代码
  - `protectConstructor()` - 保护构造函数及原型
  - `hideDeno()` - 隐藏 Deno 特征
  - `createNativeProxy()` - 创建原生外观代理
  - `deepProtect()` - 深度对象保护
  - `cleanStack()` - 清理错误堆栈
  - `hideProperty()` / `freezeProperty()` - 属性操作工具

- 📚 **完整文档**
  - `docs/NEW_EXTENSION_ARCHITECTURE.md` - 新架构完整说明
  - 包含实战示例、API 对比、使用场景等

- ✅ **完整测试覆盖**
  - 新增 `tests/test_new_extension_system.py`
  - 6/6 测试全部通过（Core Extension, Hook Extension, API Protection）

- 🔄 **向后兼容**
  - 所有现有 API 完全兼容
  - 自动加载扩展，无需代码修改

### v2.4.3 (2025-01-XX) ⭐ 新增

- 🎯 **增强 Hook 拦截系统 - V8 强制终止**
  - 新增 `__saveAndTerminate__()` / `$terminate()` API
  - 使用 V8 `IsolateHandle::terminate_execution()`，**无法被 try-catch 捕获**
  - 数据保存到全局静态存储，即使 isolate 终止也能访问
  - Python API: `get_hook_data()` 和 `clear_hook_data()`
  - 适用场景：对抗加固代码、绕过 try-catch 防护
- 📚 **新增详细文档**
  - `docs/TERMINATE_HOOK_GUIDE.md` - 完整使用指南（60+ KB）
  - 包含最佳实践、使用场景、常见问题等
- ✅ **完整测试覆盖**
  - 新增 `tests/test_terminate_hook.py`
  - 6 个测试场景，验证强制终止功能

### v2.4.2 (2025-11-17)
- 🛡️ **增加浏览器环境防检测**
  - 隐藏 Deno 特征，所有函数显示为 `[native code]`
  - 保护 `Function.prototype.toString` 防止检测
  - 添加 `chrome` 对象（Chrome 浏览器特征）
- 🔍 **Proxy 日志系统增强**
  - `$proxy()` - 创建代理对象监控属性访问
  - `$getProxyLogs()` - 获取所有访问日志
  - `$proxyGlobal()` - 代理全局对象（如 `navigator`、`document`）
  - `$printProxyLogs()` - 格式化打印日志
- ✨ **新增了专业级的 V8 堆内存分析能力**
  - 实时内存监控 - get_heap_statistics() 提供 7 种堆内存指标
  - Chrome DevTools 集成 - take_heap_snapshot() 导出标准快照文件
  - 内存泄漏检测 - 通过快照对比分析内存泄漏

### v2.4.0 (2025-11-14)
- ✨ 新增 `Blob` 对象，完善 `URL` 和 `URLSearchParams` 方法
- ✨ 新增内置 API `__neverjscore_clear_all_timers__()` 清除所有定时器
- 🔧 重构 `__neverjscore_return__()` Hook 函数实现

### v2.3.1 (2025-11-13)
- ✨ 添加 `with never_jscore.Context() as ctx:` 上下文管理器
- ✨ 修复 `require()` 导入第三方库时的错误
- ✨ 多线程优化（线程本地 Tokio runtime）
- 🔧 重构 `setInterval`/`clearInterval` 计时器逻辑，修复递归 bug

### v2.3.0 (2025-11-12)
- ✨ 随机数种子控制（`random_seed` 参数）
- ✨ 支持 `Math.random`、`crypto.randomUUID`、`crypto.getRandomValues`
- ✨ 多线程优化（线程本地 Tokio runtime）
- 🔧 WASM 二进制加载修复
- 🔧 Base64 解码修复
- 📚 完整的多线程文档

### v2.2.2 (2025-11-12)
- ✨ Hook 拦截 API（`$return()`, `$exit()`, `__neverjscore_return__()`）
- ✨ 提前返回机制（立即终止 JS 执行）
- 🎯 适用于 Hook 加密函数、拦截请求数据
- 📚 完整的 Hook 使用文档和示例

### v2.2.1 (2025-11-11)
- ✨ Performance API（`performance.now`、`mark`、`measure`）
- 📊 高精度时间测量

### v2.2.0 (2025-11-11)
- ✨ `require()` - CommonJS 模块系统
- ✨ `fetch()` - HTTP 网络请求
- ✨ `localStorage`/`sessionStorage` - 浏览器存储
- ✨ 浏览器环境对象（`navigator`、`location`、`document` 等）
- ✨ `URL`/`URLSearchParams`、`FormData`
- ✨ `Event`/`EventTarget`、`XMLHttpRequest`

### v2.0.0 (2025-11-05)
- 🔄 改为 py_mini_racer 风格的实例化 API
- ✅ 修复 HandleScope 错误
- ✨ Web API 扩展系统（Crypto、URL 编码、定时器等）


---

## 文档和资源

### 📚 官方文档
- **快速开始**：本 README
- **HandleScope 错误解决方案**：[docs/HANDLESCOPE_ERROR_SOLUTIONS.md](docs/HANDLESCOPE_ERROR_SOLUTIONS.md)
- **with 语句限制说明**：[docs/WITH_STATEMENT_LIMITATION.md](docs/WITH_STATEMENT_LIMITATION.md)
- **多线程支持指南**：[docs/MULTITHREADING.md](docs/MULTITHREADING.md)


### 🔗 相关项目
- [py_mini_racer](https://github.com/sqreen/PyMiniRacer) - Python MiniRacer 实现
- [PyExecJS](https://github.com/doloopwhile/PyExecJS) - Python ExecJS 实现
- [Deno](https://github.com/denoland/deno) - 现代 JavaScript/TypeScript 运行时
- [PyO3](https://github.com/PyO3/pyo3) - Rust ↔ Python 绑定库

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 贡献和反馈

欢迎提交 Issue 和 Pull Request！

- **Bug 报告**：[GitHub Issues](https://github.com/neverl805/never-jscore/issues)
- **功能建议**：[GitHub Discussions](https://github.com/neverl805/never-jscore/discussions)
