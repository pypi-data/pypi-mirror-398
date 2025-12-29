# JavaScript 调试功能深度分析报告

## 当前状态

**目前只能使用 console.log**，但 deno_core 和 rusty_v8 提供了丰富的调试 API。

---

## 🎯 可实现的调试方案（按实现难度排序）

### ⭐ 优先级 1：立即可实现（简单）

#### 1.1 增强的堆栈跟踪捕获

**功能：** 自动捕获未捕获异常的完整堆栈信息

**API：** `isolate.set_capture_stack_trace_for_uncaught_exceptions(true, 50)`

**实现位置：** `src/context.rs::new()`

**用户体验：**
```python
ctx = never_jscore.Context()
try:
    ctx.evaluate("function foo() { bar(); } function bar() { throw new Error('test'); } foo()")
except Exception as e:
    # 自动包含完整堆栈信息
    print(e)  # 包含：at bar (eval:1:50) at foo (eval:1:25)
```

#### 1.2 获取当前执行堆栈

**功能：** 在任意时刻获取 JS 调用堆栈

**API：** `v8::StackTrace::current_stack_trace(scope, frame_limit)`

**新增方法：**
```rust
pub fn get_current_stack_trace(&self, frame_limit: usize) -> PyResult<Vec<StackFrameInfo>>
```

**用户体验：**
```python
ctx = never_jscore.Context()
ctx.compile("function a() { return b(); } function b() { return c(); } function c() { return ctx.get_stack(); }")

# 在 JS 中调用 Python 暴露的方法获取堆栈
stack = ctx.evaluate("a()")
for frame in stack:
    print(f"{frame['function']} at {frame['file']}:{frame['line']}:{frame['column']}")
```

#### 1.3 堆快照导出

**功能：** 导出完整的 V8 堆快照用于内存分析

**API：** `isolate.take_heap_snapshot(callback)`

**新增方法：**
```rust
pub fn take_heap_snapshot(&self, file_path: String) -> PyResult<()>
```

**用户体验：**
```python
ctx = never_jscore.Context()
ctx.evaluate("let arr = new Array(1000000).fill(0)")

# 导出堆快照，可以用 Chrome DevTools 分析
ctx.take_heap_snapshot("heap_snapshot.heapsnapshot")
# 在 Chrome DevTools -> Memory -> Load 加载分析
```

#### 1.4 更详细的错误消息

**功能：** 使用 `v8::Message` 获取详细错误信息（源码行、位置等）

**API：** `message.get_source_line()`, `message.get_line_number()` 等

**增强现有错误处理：**
```rust
// 在错误处理中添加详细信息
if let Some(message) = try_catch.message(scope) {
    let source_line = message.get_source_line(scope, context);
    let line_number = message.get_line_number(scope, context);
    // 构建更详细的错误信息
}
```

---

### ⭐ 优先级 2：中等实现难度（推荐）

#### 2.1 消息监听器（全局错误捕获）

**功能：** 捕获所有 JS 错误，包括异步错误

**API：** `isolate.add_message_listener(callback)`

**实现方式：**
```rust
// 在 Context 初始化时添加
isolate.add_message_listener(message_callback);

// 回调函数
extern "C" fn message_callback(message: Local<Message>, exception: Local<Value>) {
    // 记录到全局错误日志
    // 可以提供 Python 回调接口
}
```

**用户体验：**
```python
def error_handler(error_info):
    print(f"JS Error: {error_info['message']} at {error_info['file']}:{error_info['line']}")

ctx = never_jscore.Context()
ctx.set_error_listener(error_handler)

# 所有错误都会被捕获，包括 Promise rejection
ctx.evaluate("Promise.reject('error')")
# 自动调用 error_handler
```

#### 2.2 自定义堆栈格式化

**功能：** 自定义 JS Error.stack 的格式

**API：** `isolate.set_prepare_stack_trace_callback(callback)`

**用户体验：**
```python
ctx = never_jscore.Context()
ctx.set_stack_formatter("detailed")  # 或 "compact", "json"

# Error.stack 会按照自定义格式输出
```

#### 2.3 执行时手动触发 GC

**功能：** 更精细的 GC 控制

**API：** `isolate.request_garbage_collection_for_testing(gc_type)`

**新增方法：**
```rust
pub fn gc_full(&self) -> PyResult<()>  // Full GC
pub fn gc_minor(&self) -> PyResult<()> // Scavenge GC
```

**用户体验：**
```python
ctx = never_jscore.Context()
ctx.evaluate("let arr = new Array(10000000).fill(0)")

before = ctx.get_heap_statistics()
ctx.gc_full()  # 强制完整 GC
after = ctx.get_heap_statistics()

print(f"Released: {(before['used_heap_size'] - after['used_heap_size']) / 1024 / 1024:.2f} MB")
```

---

### ⭐ 优先级 3：高级功能（复杂）

#### 3.1 Chrome DevTools Inspector 集成

**功能：** 启用 V8 Inspector，可用 Chrome DevTools 调试

**API：**
- `RuntimeOptions { inspector: true, ... }`
- `runtime.maybe_init_inspector()`
- `runtime.inspector()`

**实现方式：**
```rust
// 新建一个 DebugContext 类型
pub struct DebugContext {
    runtime: RefCell<JsRuntime>,
    inspector_port: u16,
}

impl DebugContext {
    pub fn new_with_inspector(port: u16) -> Self {
        let runtime = JsRuntime::new(RuntimeOptions {
            inspector: true,
            is_main: true,
            ..Default::default()
        });
        runtime.maybe_init_inspector();
        // 启动 WebSocket 服务器监听 port
    }
}
```

**用户体验：**
```python
# 启动带调试器的上下文
ctx = never_jscore.DebugContext(inspector_port=9229)

# 打开 Chrome，访问 chrome://inspect
# 点击 "Configure" 添加 localhost:9229
# 可以看到 JS 执行，设置断点，单步调试

ctx.evaluate("""
    function complex_algorithm() {
        debugger;  // Chrome DevTools 会在这里暂停
        for (let i = 0; i < 100; i++) {
            console.log(i);  // 可以在 DevTools 看到输出
        }
    }
    complex_algorithm();
""")
```

#### 3.2 本地 Inspector Session（编程式调试）

**功能：** 通过 Chrome DevTools Protocol 编程控制调试

**API：**
- `LocalInspectorSession`
- Chrome DevTools Protocol 命令

**实现方式：**
```rust
pub fn create_inspector_session(&mut self) -> LocalInspectorSession {
    let inspector = self.runtime.inspector();
    JsRuntimeInspector::create_local_session(
        inspector,
        callback,
        InspectorSessionOptions::default()
    )
}

pub fn send_cdp_command(&mut self, method: String, params: String) -> PyResult<String> {
    // 发送 CDP 命令并返回结果
}
```

**用户体验：**
```python
ctx = never_jscore.DebugContext()
session = ctx.create_inspector_session()

# 设置断点
session.send_command("Debugger.enable")
session.send_command("Debugger.setBreakpointByUrl", {
    "lineNumber": 10,
    "url": "eval",
    "columnNumber": 0
})

# 执行会在断点暂停
ctx.evaluate("function test() { console.log('line 10'); } test()")

# 在暂停状态执行表达式
result = session.send_command("Debugger.evaluateOnCallFrame", {
    "callFrameId": "frame_id",
    "expression": "1 + 1"
})
print(result)  # {"result": {"value": 2}}

# 单步执行
session.send_command("Debugger.stepInto")
session.send_command("Debugger.stepOver")
session.send_command("Debugger.resume")
```

#### 3.3 CPU 性能分析

**功能：** 分析 JS 代码性能热点

**实现方式：** 通过 Inspector Session 发送 Profiler 命令

**用户体验：**
```python
ctx = never_jscore.DebugContext()
session = ctx.create_inspector_session()

# 启动 CPU 分析
session.send_command("Profiler.enable")
session.send_command("Profiler.start")

# 运行要分析的代码
ctx.evaluate("""
    function slow() {
        let sum = 0;
        for (let i = 0; i < 1000000; i++) {
            sum += Math.sqrt(i);
        }
        return sum;
    }
    slow();
""")

# 停止并获取分析结果
profile = session.send_command("Profiler.stop")
# profile 包含调用树、时间分布等
ctx.save_profile(profile, "cpu_profile.cpuprofile")
# 可以在 Chrome DevTools -> Profiler 中加载分析
```

#### 3.4 堆内存采样分析

**功能：** 追踪内存分配，查找内存泄漏

**用户体验：**
```python
ctx = never_jscore.DebugContext()
session = ctx.create_inspector_session()

# 启动堆采样
session.send_command("HeapProfiler.enable")
session.send_command("HeapProfiler.startSampling", {
    "samplingInterval": 32768  # 每 32KB 采样一次
})

# 运行代码
for i in range(100):
    ctx.evaluate(f"let arr{i} = new Array(10000).fill({i})")

# 获取采样结果
profile = session.send_command("HeapProfiler.stopSampling")
# 显示哪些函数分配了最多内存
```

#### 3.5 代码覆盖率分析

**功能：** 查看哪些代码被执行了

**用户体验：**
```python
ctx = never_jscore.DebugContext()
session = ctx.create_inspector_session()

# 启动精确覆盖率
session.send_command("Profiler.enable")
session.send_command("Profiler.startPreciseCoverage", {
    "callCount": True,
    "detailed": True
})

# 运行代码
ctx.evaluate("""
    function used() { return 1; }
    function unused() { return 2; }
    used();
""")

# 获取覆盖率
coverage = session.send_command("Profiler.takePreciseCoverage")
# 显示 used() 被调用，unused() 未被调用
```

---

## 📊 功能对比矩阵

| 功能 | 实现难度 | 用户价值 | 对调试的帮助 | 推荐优先级 |
|------|---------|----------|-------------|-----------|
| 堆栈跟踪捕获 | ⭐ 简单 | ⭐⭐⭐⭐⭐ | 立即知道错误发生在哪 | 🔥 最高 |
| 获取当前堆栈 | ⭐ 简单 | ⭐⭐⭐⭐ | 运行时查看调用链 | 🔥 最高 |
| 堆快照导出 | ⭐ 简单 | ⭐⭐⭐⭐ | 分析内存泄漏 | 🔥 高 |
| 详细错误消息 | ⭐ 简单 | ⭐⭐⭐⭐⭐ | 精确定位错误位置 | 🔥 最高 |
| 消息监听器 | ⭐⭐ 中等 | ⭐⭐⭐⭐ | 全局错误捕获 | 🔥 高 |
| 精细 GC 控制 | ⭐⭐ 中等 | ⭐⭐⭐ | 内存调试 | 中 |
| Chrome DevTools | ⭐⭐⭐ 复杂 | ⭐⭐⭐⭐⭐ | 可视化调试体验 | 🔥 高 |
| 编程式断点 | ⭐⭐⭐ 复杂 | ⭐⭐⭐⭐ | 自动化调试 | 中 |
| CPU 性能分析 | ⭐⭐⭐ 复杂 | ⭐⭐⭐⭐ | 优化性能 | 中 |
| 堆内存分析 | ⭐⭐⭐ 复杂 | ⭐⭐⭐⭐ | 查找内存泄漏 | 中 |
| 代码覆盖率 | ⭐⭐⭐ 复杂 | ⭐⭐⭐ | 测试覆盖度 | 低 |

---

## 🎬 推荐实现路线图

### 第一阶段（1-2 天）- 立即改善调试体验

1. ✅ **启用堆栈跟踪捕获**
   - 修改 `Context::new()` 添加一行代码
   - 所有错误自动带完整堆栈

2. ✅ **添加堆快照导出**
   - 新增 `take_heap_snapshot(file_path)` 方法
   - 用 Chrome DevTools 分析内存

3. ✅ **增强错误消息**
   - 使用 `v8::Message` 提取源码行、位置
   - 错误信息包含具体代码上下文

### 第二阶段（3-5 天）- 高级调试功能

4. **添加消息监听器**
   - 全局捕获所有 JS 错误
   - 支持 Python 回调函数

5. **添加当前堆栈获取**
   - 新增 `get_current_stack()` 方法
   - JS 可以主动查询调用堆栈

6. **精细 GC 控制**
   - 添加 `gc_full()` 和 `gc_minor()` 方法

### 第三阶段（1-2 周）- Chrome DevTools 集成

7. **实现 DebugContext 类**
   - 启用 V8 Inspector
   - WebSocket 服务器
   - Chrome DevTools 可视化调试

8. **本地 Inspector Session**
   - 编程式断点控制
   - CDP 命令接口
   - 单步执行、变量检查

### 第四阶段（选项）- 性能分析工具

9. **CPU 性能分析**
10. **堆内存采样**
11. **代码覆盖率**

---

## 💡 使用场景示例

### 场景 1：调试加密算法错误

**当前方式（只有 console.log）：**
```python
ctx.evaluate("""
    function encrypt(data) {
        console.log('step 1');
        let key = generateKey();
        console.log('step 2, key=', key);
        let encrypted = xor(data, key);
        console.log('step 3, encrypted=', encrypted);
        return encrypted;
    }
""")
```

**改进后（完整堆栈 + 错误消息）：**
```python
try:
    ctx.evaluate("encrypt('test')")
except Exception as e:
    print(e)
    # 输出：
    # Error: xor is not defined
    #   at encrypt (eval:4:21)
    #   at <anonymous> (eval:1:1)
    # Source: let encrypted = xor(data, key);
    #                          ^^^
```

### 场景 2：查找内存泄漏

**当前方式：** 无法分析

**改进后：**
```python
ctx = never_jscore.Context()

# 运行可能泄漏的代码
for i in range(100):
    ctx.evaluate(f"processData({i})")

# 导出堆快照
ctx.take_heap_snapshot("leak.heapsnapshot")

# Chrome DevTools 加载分析：
# 1. 打开 Chrome -> DevTools -> Memory
# 2. Load Profile -> 选择 leak.heapsnapshot
# 3. 查看 "Summary" 找到占用最多的对象
# 4. 查看 "Containment" 找到引用路径
```

### 场景 3：性能优化

**当前方式：** 只能猜测哪里慢

**改进后（Chrome DevTools）：**
```python
ctx = never_jscore.DebugContext(inspector_port=9229)

# 1. Chrome 打开 chrome://inspect
# 2. 点击 "Configure" 添加 localhost:9229
# 3. 点击 "inspect" 打开 DevTools
# 4. 切换到 "Profiler" 标签
# 5. 点击 "Record"

ctx.evaluate("""
    function slow() {
        // 复杂的加密逻辑
    }
    slow();
""")

# 6. 点击 "Stop"
# 7. 查看火焰图，找到最耗时的函数
```

---

## 🚀 快速开始：最小实现

如果只想快速改善调试体验，只需修改 `src/context.rs` 添加以下代码：

```rust
// 在 Context::new() 的 runtime 创建后添加：
{
    let isolate = runtime.v8_isolate();

    // 启用堆栈跟踪捕获（只需一行！）
    isolate.set_capture_stack_trace_for_uncaught_exceptions(true, 50);
}
```

这一行代码就能让所有错误自动包含完整堆栈信息，立即改善调试体验！

---

## 📚 参考文档

- deno_core Inspector: https://docs.rs/deno_core/latest/deno_core/struct.JsRuntimeInspector.html
- rusty_v8 StackTrace: https://docs.rs/v8/latest/v8/struct.StackTrace.html
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
- V8 Inspector: https://v8.dev/docs/inspector
