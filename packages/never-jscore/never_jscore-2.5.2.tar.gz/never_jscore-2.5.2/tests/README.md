# never-jscore 测试套件

本目录包含 never-jscore v2.5.0+ 的核心测试用例。

## 快速开始

```bash
# 运行所有测试
python tests/run_all_tests.py

# 运行单个测试
python tests/test_async_promise.py
```

## 核心测试文件

### 🔧 基础功能

| 测试文件 | 功能 | 说明 |
|---------|------|------|
| `test_async_promise.py` | Promise/async/await | Promise 链、setTimeout、微任务与宏任务 |
| `test_context_management.py` | Context 生命周期管理 | 避免 HandleScope 错误的最佳实践 |
| `test_new_extension_system.py` | 扩展系统架构 | 模块化扩展加载和配置 |
| `test_xmlhttprequest.py` | XMLHttpRequest API | HTTP 请求、响应处理、Hook 拦截 |

### 🌐 Web API 集成

| 测试文件 | 功能 | 说明 |
|---------|------|------|
| `test_deno_web_api.py` | Deno Web API | URL, TextEncoder, Streams, Events, fetch 等 |
| `test_browser_protection_deno_web.py` | 反检测保护 | 隐藏 Deno、函数显示 [native code] |

### 📦 Node.js 兼容性

| 测试文件 | 功能 | 说明 |
|---------|------|------|
| `test_node_require.py` | require() 功能 | Node.js 内置模块、npm 包加载 |
| `test_jsdom.py` | jsdom DOM 操作 | 完整的 DOM API 支持 |

### 🛡️ 逆向工程工具

| 测试文件 | 功能 | 说明 |
|---------|------|------|
| `test_terminate_hook.py` | 强制终止 Hook | V8 terminate，无法被 try-catch 捕获 |
| `test_random_seed.py` | 确定性随机数 | 调试包含随机 nonce 的加密算法 |

### ⚡ 性能与优化

| 测试文件 | 功能 | 说明 |
|---------|------|------|
| `test_memory_and_performance.py` | 内存监控 | V8 堆统计、堆快照、GC 优化 |
| `test_multithreading.py` | 多线程 | ThreadLocal + Context 复用模式 |
| `test_extension_modes_comparison.py` | 扩展模式对比 | 三种模式的性能和内存对比 |

---

## 核心功能示例

### 1. Context 管理（避免崩溃）

```python
# ✅ 正确：复用 Context
ctx = never_jscore.Context()
for i in range(1000):
    result = ctx.call("func", [i])
del ctx

# ❌ 错误：循环中用 with（会在 10-20 次后崩溃）
for i in range(100):
    with never_jscore.Context() as ctx:  # 错误！
        ctx.evaluate("...")
```

### 2. Hook 拦截（两种模式）

**模式 A：`$return()` - 可被 try-catch 捕获**
```python
result = ctx.evaluate("""
    CryptoLib.encrypt = function(text, key) {
        $return({ text, key });  // 提前返回
    };
    login('user', 'pass');
""")
print(f"密钥: {result['key']}")
```

**模式 B：`$terminate()` - 强制终止（推荐）**
```python
ctx.clear_hook_data()
try:
    ctx.evaluate("""
        CryptoLib.encrypt = function(text, key) {
            $terminate({ text, key });  // 无法被 try-catch 捕获
        };
        try {
            login('user', 'pass');
        } catch (e) {
            // 不会执行
        }
    """)
except:
    pass

data = json.loads(ctx.get_hook_data())
print(f"密钥: {data['key']}")
```

### 3. 确定性随机数

```python
# 固定种子让结果可重现
ctx = never_jscore.Context(random_seed=12345)
r1 = ctx.evaluate("Math.random()")
r2 = ctx.evaluate("Math.random()")
# 每次运行结果相同！
```

### 4. Node.js 兼容性

```python
# 使用 Node.js 模块和 npm 包
ctx = never_jscore.Context(enable_node_compat=True)

result = ctx.evaluate("""
    const path = require('path');
    const crypto = require('crypto');
    const { JSDOM } = require('jsdom');  // npm 包

    const dom = new JSDOM('<h1>Hello</h1>');
    dom.window.document.querySelector('h1').textContent
""")
print(result)  # 'Hello'
```

### 5. 多线程并行

```python
import threading
from concurrent.futures import ThreadPoolExecutor

thread_local = threading.local()

def get_context():
    if not hasattr(thread_local, 'ctx'):
        thread_local.ctx = never_jscore.Context()
        thread_local.ctx.compile(js_code)
    return thread_local.ctx

def worker(data):
    ctx = get_context()  # 每个线程复用自己的 Context
    return ctx.call("process", [data])

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(worker, data_list))
```

### 6. 内存监控

```python
# 获取 V8 堆统计信息
heap_stats = ctx.get_heap_statistics()
print(f"已使用: {heap_stats['used_heap_size'] / 1024 / 1024:.2f} MB")
print(f"使用率: {heap_stats['used_heap_size'] / heap_stats['total_heap_size'] * 100:.1f}%")

# 导出 Chrome DevTools 堆快照
ctx.take_heap_snapshot("heap.heapsnapshot")
# 在 Chrome DevTools -> Memory -> Load 加载分析

# 定期 GC
for i in range(1000):
    ctx.call("process", [i])
    if i % 100 == 0:
        ctx.gc()
```

### 7. API 日志（v2.5.1+）

```python
# 启用日志
ctx = never_jscore.Context(enable_logging=True)

ctx.evaluate("""
    setTimeout(() => {}, 100);  // [API] setTimeout([Function], 100)
    crypto.randomUUID();        // [API] randomUUID()
    atob('test');               // [API] atob(test)
""")
# 日志输出到 stderr
```

### 8. 扩展模式对比（v2.5.1+）

```python
# 测试三种模式的性能和内存
# test_extension_modes_comparison.py

# 纯净模式 - 最快初始化，最小内存
ctx = never_jscore.Context(enable_extensions=False)
# 初始化: ~16ms, 内存: ~2.5MB

# Web API 模式 - 默认，平衡
ctx = never_jscore.Context()
# 初始化: ~16ms, 内存: ~3MB

# Node.js 模式 - 完整功能
ctx = never_jscore.Context(enable_node_compat=True)
# 初始化: ~180ms, 内存: ~7MB

# 关键发现: 运行时性能差异 <8%，主要差异在初始化
```

---

## 测试覆盖

### ✅ JavaScript 核心
- Promise/async/await
- setTimeout/setInterval
- 事件循环（微任务/宏任务）

### ✅ Web API
- fetch/XMLHttpRequest
- crypto (getRandomValues, randomUUID, subtle)
- URL/URLSearchParams
- TextEncoder/TextDecoder
- Blob/File
- Streams API
- localStorage/sessionStorage
- performance API

### ✅ Node.js 兼容
- require() 函数
- Node.js 内置模块 (path, fs, crypto, buffer 等)
- npm 包加载 (jsdom, lodash 等)
- package.json exports 解析

### ✅ 逆向工程
- Hook 拦截 ($return, $terminate)
- 确定性随机数
- 反检测保护

### ✅ 性能与稳定性
- Context 生命周期管理
- 多线程支持
- 内存优化
- V8 堆监控

---

## 常见问题

### Q: 为什么循环中用 `with` 会崩溃？
A: 每次创建 Context 会累积 HandleScope，10-20 次后崩溃。应该复用 Context。

### Q: `$return()` 和 `$terminate()` 有什么区别？
A: `$return()` 使用 throw Error，可被 try-catch 捕获；`$terminate()` 使用 V8 terminate_execution，无法被捕获，适合对抗加固代码。

### Q: 如何使用 npm 包？
A: 启用 `enable_node_compat=True`，然后在项目目录下运行 `npm install <package>`。

### Q: 如何调试内存泄漏？
A: 使用 `ctx.get_heap_statistics()` 监控内存，用 `ctx.take_heap_snapshot()` 导出快照在 Chrome DevTools 中分析。

### Q: 应该选择哪种扩展模式？
A:
- **纯净模式** (`enable_extensions=False`): 不需要 Web API，最快最小
- **Web API 模式** (默认): 需要 fetch/crypto/localStorage 等
- **Node.js 模式** (`enable_node_compat=True`): 需要 require() 和 npm 包

运行 `test_extension_modes_comparison.py` 查看详细对比。

---

## 贡献测试

欢迎添加新测试用例！请遵循现有测试风格。

## 许可证

MIT License
