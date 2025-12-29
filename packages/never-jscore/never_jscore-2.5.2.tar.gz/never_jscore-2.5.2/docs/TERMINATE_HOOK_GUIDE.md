# V8 terminate_execution Hook 拦截指南

## 概述

never_jscore v2.4.3+ 提供了增强的 Hook 拦截 API，使用 V8 的 `terminate_execution()` 实现**无法被 try-catch 捕获**的强制终止。

## 两种 Hook 方法对比

### 方法 1: `$return()` / `__neverjscore_return__()` （旧版本）

**实现原理：** 抛出特殊的 JavaScript Error

**特点：**
- ✅ 简单易用
- ❌ **可以被 try-catch 捕获**
- ❌ 目标代码可能恢复执行

**示例：**
```python
ctx.evaluate('''
    try {
        $return({ data: "intercepted" });
        console.log("不会执行");
    } catch (e) {
        // ⚠️ 可以捕获！目标代码可能绕过
        console.log("捕获到 Hook:", e);
        continueExecution();  // 目标代码恢复
    }
''')
```

### 方法 2: `$terminate()` / `__saveAndTerminate__()` （新版本，推荐）

**实现原理：** V8 `IsolateHandle::terminate_execution()`

**特点：**
- ✅ **无法被 try-catch 捕获**
- ✅ 强制终止整个 JavaScript 执行
- ✅ 适合对抗加固的目标代码
- ⚠️ 更强力，需谨慎使用

**示例：**
```python
ctx.evaluate('''
    try {
        $terminate({ data: "intercepted" });
        console.log("不会执行");  // ✅ 被跳过
    } catch (e) {
        console.log("不会执行");  // ✅ catch 块也被跳过
    } finally {
        console.log("不会执行");  // ✅ finally 也被跳过
    }
    console.log("不会执行");  // ✅ 后续所有代码都被跳过
''')
```

## 使用场景

### 场景 1: 对抗 try-catch 防护

许多加固的 JS 代码会用 try-catch 包裹所有逻辑：

```javascript
// 目标网站的加固代码
try {
    const encryptedData = encrypt(userData);
    xhr.send(encryptedData);
} catch (e) {
    // 吞掉所有错误，防止调试
    console.log("Error ignored");
}
```

**使用 $terminate 绕过：**

```python
import never_jscore
import json

ctx = never_jscore.Context()
ctx.clear_hook_data()

# 注入 Hook
ctx.compile('''
    const originalEncrypt = encrypt;
    encrypt = function(data) {
        const result = originalEncrypt(data);

        // ✅ 使用 $terminate 拦截，无法被 try-catch 捕获
        $terminate({
            plaintext: data,
            encrypted: result,
            key: this._key
        });

        return result;
    };
''')

# 执行目标代码
try:
    ctx.evaluate('doLogin("user", "pass");')
except Exception as e:
    print(f"JS 被终止: {e}")

# 获取拦截的数据
hook_data = ctx.get_hook_data()
if hook_data:
    data = json.loads(hook_data)
    print(f"密钥: {data['key']}")
    print(f"明文: {data['plaintext']}")
    print(f"密文: {data['encrypted']}")
```

### 场景 2: Hook XMLHttpRequest/fetch

```python
ctx = never_jscore.Context()
ctx.clear_hook_data()

# Hook XHR.send
ctx.compile('''
    XMLHttpRequest.prototype.send = function(body) {
        $terminate({
            type: "xhr",
            url: this._url,
            method: this._method,
            headers: this._headers,
            body: body
        });
    };
''')

# 或 Hook fetch
ctx.compile('''
    const originalFetch = fetch;
    fetch = async function(url, options) {
        $terminate({
            type: "fetch",
            url: url,
            method: options?.method,
            headers: options?.headers,
            body: options?.body
        });

        return originalFetch(url, options);
    };
''')

# 执行目标代码（会被拦截）
try:
    ctx.evaluate('''
        // 这段代码的网络请求会被拦截
        fetch('/api/data', {
            method: 'POST',
            body: JSON.stringify({ key: 'value' })
        });
    ''')
except:
    pass

# 获取拦截数据
data = json.loads(ctx.get_hook_data())
print(f"拦截到请求: {data['url']}")
print(f"请求体: {data['body']}")
```

### 场景 3: 提取加密算法的中间值

```python
ctx = never_jscore.Context()
ctx.clear_hook_data()

# 在关键位置插入 Hook
ctx.compile('''
    const originalAES = CryptoJS.AES;
    CryptoJS.AES = {
        encrypt: function(plaintext, key) {
            // 拦截加密参数
            $terminate({
                algorithm: "AES",
                plaintext: plaintext.toString(),
                key: key.toString(),
                timestamp: Date.now()
            });

            return originalAES.encrypt(plaintext, key);
        }
    };
''')

# 执行目标加密代码
try:
    ctx.evaluate('const encrypted = CryptoJS.AES.encrypt("secret", "password123");')
except:
    pass

# 获取密钥
data = json.loads(ctx.get_hook_data())
print(f"算法: {data['algorithm']}")
print(f"密钥: {data['key']}")
print(f"明文: {data['plaintext']}")
```

## 完整 API 参考

### JavaScript API

#### `__saveAndTerminate__(data)`
**别名：** `$terminate(data)`

保存数据到 Rust 全局存储，然后调用 V8 `terminate_execution()` 强制终止。

**参数：**
- `data`: 任意 JavaScript 值（会被 JSON.stringify）

**特性：**
- ✅ 无法被 try-catch 捕获
- ✅ 跳过 finally 块
- ✅ 立即终止整个 isolate

**示例：**
```javascript
// 完整函数名
__saveAndTerminate__({ key: "value" });

// 简短别名（推荐）
$terminate({ key: "value" });
```

#### `__neverjscore_return__(data)`
**别名：** `$return(data)`, `$exit(data)`

使用 throw Error 方式的旧版 Hook API（可以被 try-catch 捕获）。

### Python API

#### `Context.get_hook_data() -> Optional[str]`

获取保存的 Hook 数据（JSON 字符串）。

**返回值：**
- `str`: 如果有数据，返回 JSON 字符串
- `None`: 如果没有数据

**重要说明：**
- ✅ **自动清空：** 每次 `evaluate()`、`call()`、`eval()` 执行前会**自动清空** hook 数据
- ✅ 这意味着每次执行都有干净的状态，不会读到上一次的旧值
- ✅ `get_hook_data()` 可以多次调用，返回相同的值（不会清空）
- ⚠️ 如果需要保留上一次的数据，必须在下一次执行前先调用 `get_hook_data()` 读取

**示例：**
```python
ctx = never_jscore.Context()

# 第一次执行
try:
    ctx.evaluate('$terminate({ value: 1 });')
except:
    pass

data1 = ctx.get_hook_data()  # {"value": 1}
data1_again = ctx.get_hook_data()  # {"value": 1} - 可以多次读取

# ⚠️ 第二次执行会自动清空之前的数据
try:
    ctx.evaluate('$terminate({ value: 2 });')
except:
    pass

data2 = ctx.get_hook_data()  # {"value": 2} - 新数据

# ❌ 如果想保留第一次的数据，应该这样：
# saved_data = ctx.get_hook_data()  # 在第二次执行前保存
```

#### `Context.clear_hook_data() -> None`

清空保存的 Hook 数据。

**使用时机：**
- 在开始新的 Hook 拦截前调用
- 避免读取到上一次的旧数据

**示例：**
```python
ctx.clear_hook_data()  # 清空旧数据

try:
    ctx.evaluate('...')  # 执行新的代码
except:
    pass

data = ctx.get_hook_data()  # 获取新数据
```

## 最佳实践

### 1. 自动清空机制（v2.4.3+）

✅ **好消息：** 从 v2.4.3 开始，每次 `evaluate()`、`call()`、`eval()` 执行前会**自动清空** hook 数据！

**这意味着：**
- ✅ 不需要手动调用 `clear_hook_data()`
- ✅ 每次执行都有干净的状态
- ✅ 不会读到上一次的旧值

```python
ctx = never_jscore.Context()

# 第一次拦截
try:
    ctx.evaluate('$terminate({ n: 1 });')
except:
    pass
data1 = ctx.get_hook_data()  # {"n": 1}

# 第二次拦截 - 自动清空了第一次的数据
try:
    ctx.evaluate('$terminate({ n: 2 });')
except:
    pass
data2 = ctx.get_hook_data()  # {"n": 2} ✅ 正确

# ⚠️ 如果需要保留第一次的数据：
# saved = ctx.get_hook_data()  # 在第二次执行前保存
```

### 2. 错误处理

`$terminate()` 会导致 Python 端抛出异常：

```python
try:
    ctx.evaluate('''
        $terminate({ data: "test" });
    ''')
except Exception as e:
    # ✅ 预期的异常，表示 JS 被终止
    print(f"JS terminated (expected): {e}")

# 获取数据
data = ctx.get_hook_data()
```

### 3. 多 Context 注意事项

⚠️ **Hook 数据使用全局存储，多个 Context 会共享！**

```python
ctx1 = never_jscore.Context()
ctx2 = never_jscore.Context()

# Context 1 保存数据
try:
    ctx1.evaluate('$terminate({ ctx: 1 });')
except:
    pass

# Context 2 保存数据（会覆盖 Context 1 的数据！）
try:
    ctx2.evaluate('$terminate({ ctx: 2 });')
except:
    pass

# 只能获取到最后一个
data = ctx2.get_hook_data()  # { ctx: 2 }
```

**推荐模式：** 在单个 Context 内完成 Hook -> 执行 -> 获取 的完整流程。

### 4. 性能考虑

`terminate_execution()` 会终止整个 isolate：

```python
# ❌ 不推荐：每次都创建新 Context
for i in range(100):
    ctx = never_jscore.Context()
    ctx.clear_hook_data()
    try:
        ctx.evaluate('$terminate({ i });')
    except:
        pass
    data = ctx.get_hook_data()
    del ctx  # 必须删除

# ✅ 推荐：复用 Context，使用 $return 代替
ctx = never_jscore.Context()
for i in range(100):
    try:
        result = ctx.evaluate(f'$return({{ i: {i} }});')
    except:
        pass
```

## 调试技巧

### 查看 V8 terminate 错误

```python
try:
    ctx.evaluate('$terminate({ debug: true });')
except Exception as e:
    print(f"异常类型: {type(e).__name__}")
    print(f"异常消息: {str(e)}")
    # 通常包含 "execution terminated" 字样
```

### 对比两种方法

```python
# 测试 $return (可以被捕获)
ctx1 = never_jscore.Context()
result = ctx1.evaluate('''
    try {
        $return({ method: "$return" });
    } catch (e) {
        "caught";  // ✅ 会执行
    }
''')
print(f"$return 结果: {result}")  # "caught"

# 测试 $terminate (无法被捕获)
ctx2 = never_jscore.Context()
ctx2.clear_hook_data()
try:
    ctx2.evaluate('''
        try {
            $terminate({ method: "$terminate" });
        } catch (e) {
            "caught";  // ❌ 不会执行
        }
    ''')
except:
    pass

data = json.loads(ctx2.get_hook_data())
print(f"$terminate 数据: {data}")  # { method: "$terminate" }
```

## 常见问题

### Q: 何时使用 $terminate，何时使用 $return？

**使用 $terminate：**
- 目标代码有 try-catch 防护
- 需要强制终止，不给目标代码恢复机会
- 逆向分析加固的商业代码

**使用 $return：**
- 简单的 Hook 场景
- 需要在同一个 Context 中执行多次
- 性能敏感的场景

### Q: $terminate 会影响后续代码执行吗？

不会。`terminate_execution()` 只终止当前这次 `evaluate()/call()`，Context 仍然可用：

```python
ctx = never_jscore.Context()

# 第一次执行被终止
try:
    ctx.evaluate('$terminate({ n: 1 });')
except:
    pass

# Context 仍然可用
result = ctx.evaluate('1 + 1')  # ✅ 正常工作
print(result)  # 2
```

### Q: 数据大小有限制吗？

建议不超过 10MB。超大数据应该分批处理：

```javascript
// ❌ 不推荐：一次性保存大数据
$terminate({ data: largeArray });

// ✅ 推荐：保存关键信息
$terminate({
    dataLength: largeArray.length,
    firstItem: largeArray[0],
    lastItem: largeArray[largeArray.length - 1]
});
```

## 版本历史

- **v2.4.3+**: 新增 `__saveAndTerminate__()` / `$terminate()` API
- **v2.4.2**: 原有 `$return()` / `__neverjscore_return__()` API

## 参考

- [V8 API: IsolateHandle::terminate_execution()](https://v8.github.io/api/head/classv8_1_1Isolate.html#a9f07c9e0ff21d5e9f7c77daef8f96d0d)
- [Deno Core 文档](https://docs.deno.com/runtime/manual/runtime/deno_core)
- [rustyscript 参考实现](https://github.com/rscarson/rustyscript)
