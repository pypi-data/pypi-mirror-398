# 日志功能增强方案

## 当前状态

**已有功能**:
- ✅ `enable_logging` 参数（控制扩展操作日志）
- ✅ 基础 console ops (log, warn, error, info)
- ✅ 堆栈跟踪自动捕获
- ✅ 堆快照导出

**局限**:
- ❌ console 输出直接打印到 stdout/stderr，无法捕获
- ❌ 无法在 Python 侧获取 JS 的 console 输出
- ❌ 无法区分不同 Context 的日志
- ❌ 无法过滤或格式化日志

## 增强方案

### 方案 1: Console 输出捕获（推荐，实现简单）

**设计**:
1. 添加 `console_output_callback` 参数到 Context
2. JS 侧 console 调用 Rust op，op 触发 Python callback
3. Python 可以自定义日志处理（存储、过滤、格式化）

**API 设计**:
```python
def my_console_handler(level: str, message: str, stack: Optional[str]):
    print(f"[{level.upper()}] {message}")
    if stack:
        print(f"  Stack: {stack}")

ctx = never_jscore.Context(
    console_handler=my_console_handler  # 可选回调
)

ctx.evaluate("""
    console.log("test");    // 触发 my_console_handler("log", "test", None)
    console.error("error"); // 触发 my_console_handler("error", "error", stack)
""")
```

**实现复杂度**: ⭐⭐ 中等（2-3天）
- 需要实现 Python callback 机制
- 需要修改 console ops 传递 callback
- 需要处理线程安全（callback 跨 Rust-Python 边界）

**优势**:
- ✅ 完全控制 console 输出
- ✅ 可以将日志存储到文件/数据库
- ✅ 可以在 Jupyter Notebook 中漂亮展示
- ✅ 可以实现日志过滤和搜索

**劣势**:
- ⚠️ Python callback 开销
- ⚠️ 线程安全复杂度

---

### 方案 2: 基于 V8 Message Listener（全局错误捕获）

**设计**:
1. 使用 `isolate.add_message_listener()` 捕获所有错误消息
2. 自动记录错误堆栈
3. 可选：触发 Python callback

**API 设计**:
```python
def my_error_handler(error_type: str, message: str, source_line: str,
                     line_number: int, stack_trace: str):
    print(f"JS Error: {error_type}: {message}")
    print(f"  at line {line_number}: {source_line}")
    print(f"  Stack:\n{stack_trace}")

ctx = never_jscore.Context(
    error_handler=my_error_handler  # 可选
)

ctx.evaluate("undefinedFunc();")  // 触发 error_handler
```

**实现复杂度**: ⭐⭐ 中等（1-2天）
- 在 Context::new() 中添加 message listener
- 提取错误信息并格式化
- 触发 Python callback

**优势**:
- ✅ 捕获所有错误（包括异步错误）
- ✅ 比 try-catch 更全面
- ✅ 自动包含源代码行

**劣势**:
- ⚠️ 只捕获错误，不捕获普通 console
- ⚠️ 可能与现有错误处理冲突

---

### 方案 3: 日志收集器模式（无 callback，最简单）

**设计**:
1. Context 内部维护日志列表
2. console 调用追加到列表
3. Python 定期读取日志

**API 设计**:
```python
ctx = never_jscore.Context(capture_console=True)

ctx.evaluate("""
    console.log("message 1");
    console.warn("warning");
    console.error("error");
""")

# 读取所有日志
logs = ctx.get_console_logs()
# [
#   {"level": "log", "message": "message 1", "timestamp": 1234567890},
#   {"level": "warn", "message": "warning", "timestamp": 1234567891},
#   {"level": "error", "message": "error", "timestamp": 1234567892}
# ]

ctx.clear_console_logs()
```

**实现复杂度**: ⭐ 简单（几小时）
- 在 Context 中添加 `Vec<ConsoleLog>`
- console ops 追加到 Vec
- 添加 `get_console_logs()` 和 `clear_console_logs()` 方法

**优势**:
- ✅ 实现极其简单
- ✅ 无线程安全问题
- ✅ 性能最佳（无 callback 开销）
- ✅ 支持批量处理

**劣势**:
- ⚠️ 需要手动读取
- ⚠️ 内存占用（需要定期清理）
- ⚠️ 不适合实时监控

---

### 方案 4: JavaScript 侧拦截（Proxy，最灵活）

**设计**:
1. 在 JS 侧注入 Proxy 拦截 console
2. 通过现有的 `$return()` 或新 op 发送到 Python
3. 完全在 JS 层面控制

**实现**:
```javascript
// 在 polyfill 中添加
const originalConsole = {
    log: console.log,
    warn: console.warn,
    error: console.error
};

const logCollector = [];

console.log = function(...args) {
    const message = args.map(a => String(a)).join(' ');
    logCollector.push({ level: 'log', message, timestamp: Date.now() });
    originalConsole.log(...args);
};

// 类似地包装其他 console 方法

globalThis.__getConsoleLogs = function() {
    return logCollector;
};

globalThis.__clearConsoleLogs = function() {
    logCollector.length = 0;
};
```

**Python API**:
```python
ctx = never_jscore.Context()  # 无需修改

ctx.evaluate("console.log('test')")

logs = ctx.evaluate("__getConsoleLogs()")
# [{"level": "log", "message": "test", "timestamp": 1234567890}]

ctx.evaluate("__clearConsoleLogs()")
```

**实现复杂度**: ⭐ 非常简单（1小时）
- 只需修改 polyfill JS 代码
- 无需修改 Rust 代码
- 利用现有 evaluate() API

**优势**:
- ✅ 零 Rust 代码改动
- ✅ 灵活，用户可以自己扩展
- ✅ 性能好
- ✅ 支持复杂过滤逻辑

**劣势**:
- ⚠️ JS 侧可被绕过（用户代码可以覆盖）
- ⚠️ 不能捕获原生错误（需配合 message listener）

---

## 推荐方案

### 短期（1小时）: 方案 4 - JavaScript 侧拦截

**原因**:
1. 立即可用，无需等待 Rust 编译
2. 用户可以自己定制
3. 与现有 Hook 系统一致

**实现步骤**:
1. 修改 `src/dddd_js/js_polyfill.js`，添加 console 拦截
2. 添加 `__getConsoleLogs()` 和 `__clearConsoleLogs()` 全局函数
3. 创建 `examples/console_logging_demo.py` 演示用法
4. 添加文档 `docs/CONSOLE_LOGGING.md`

### 中期（1天）: 方案 3 - 日志收集器模式

**原因**:
1. 更可靠（不能被 JS 绕过）
2. 性能好
3. 实现简单

**实现步骤**:
1. 在 `Context` 结构添加 `console_logs: RefCell<Vec<ConsoleLog>>`
2. 修改 console ops，追加到日志列表
3. 添加 Python 方法 `get_console_logs()`, `clear_console_logs()`
4. 添加可选参数 `capture_console: bool`

### 长期（可选）: 方案 1 - Python Callback

**原因**:
1. 最灵活
2. 适合集成到复杂系统
3. 实时监控

**考虑因素**:
- 需要处理 Python GIL
- 需要处理线程安全
- 性能开销

---

## 立即行动：实现方案 4

最简单、最快的方案，立即为用户提供价值。
