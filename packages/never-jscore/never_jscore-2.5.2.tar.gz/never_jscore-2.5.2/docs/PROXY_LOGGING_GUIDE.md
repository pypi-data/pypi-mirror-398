# Proxy 日志系统使用指南

## 功能概述

never_jscore v2.4.2+ 新增了强大的 **Proxy 日志系统**，可以监控 JavaScript 对象的所有属性访问、函数调用和修改操作。这对于 JS 逆向工程非常有用。

## 核心功能

### 📊 监控能力

| 操作类型 | 说明 | 用途 |
|---------|------|------|
| `get` | 属性读取 | 追踪哪些属性被访问 |
| `set` | 属性设置 | 监控数据修改 |
| `call` | 函数调用 | 记录函数调用和参数 |
| `return` | 函数返回 | 捕获返回值 |
| `delete` | 属性删除 | 检测删除操作 |

### 🎯 适用场景

- ✅ 追踪加密算法的参数和密钥
- ✅ 监控 API 调用和请求签名生成
- ✅ 分析混淆代码的执行流程
- ✅ 检测反调试和指纹识别
- ✅ 提取动态生成的配置数据

---

## 快速开始

### 基本用法

```python
import never_jscore

ctx = never_jscore.Context()

result = ctx.evaluate("""
    // 1. 创建要监控的对象
    const config = {
        apiKey: 'secret_key_12345',
        endpoint: 'https://api.example.com'
    };

    // 2. 使用 $proxy() 包装对象
    const proxiedConfig = $proxy(config, { name: 'Config' });

    // 3. 正常使用对象（所有操作都会被记录）
    const key = proxiedConfig.apiKey;
    proxiedConfig.endpoint = 'https://api2.example.com';

    // 4. 获取日志
    $getProxyLogs();
""")

# 在 Python 侧分析日志
for log in result:
    print(f"[{log['type']}] {log['target']}.{log['property']}")
```

**输出：**
```
[get] Config.apiKey
[set] Config.endpoint
```

---

## API 参考

### `$proxy(target, options)`

创建代理对象。

**参数：**
- `target`: 要代理的对象
- `options`: 配置选项（可选）
  - `name`: 对象名称（用于日志，默认 `'Object'`）
  - `logGet`: 是否记录属性读取（默认 `true`）
  - `logSet`: 是否记录属性设置（默认 `true`）
  - `logCall`: 是否记录函数调用（默认 `true`）
  - `logDelete`: 是否记录属性删除（默认 `true`）
  - `filter`: 过滤函数（可选）

**返回：** Proxy 对象

**示例：**
```javascript
const api = { request(url) { return fetch(url); } };

// 只监控函数调用，不监控属性访问
const proxied = $proxy(api, {
    name: 'API',
    logGet: false,
    logCall: true
});
```

---

### `$getProxyLogs(filter)`

获取代理日志。

**参数：**
- `filter`: 过滤选项（可选）
  - `type`: 日志类型 (`'get'`, `'set'`, `'call'`, `'return'`, `'delete'`)
  - `target`: 目标对象名称
  - `property`: 属性名
  - `since`: 时间戳，只返回此时间之后的日志

**返回：** 日志数组

**示例：**
```javascript
// 获取所有日志
const allLogs = $getProxyLogs();

// 只获取函数调用
const calls = $getProxyLogs({ type: 'call' });

// 只获取特定对象的日志
const apiLogs = $getProxyLogs({ target: 'API' });

// 只获取特定属性的日志
const tokenLogs = $getProxyLogs({ property: 'token' });
```

---

### `$clearProxyLogs()`

清空所有日志。

**示例：**
```javascript
$clearProxyLogs();
```

---

### `$setProxyLogging(enabled)`

启用/禁用日志记录。

**参数：**
- `enabled`: `true` 启用，`false` 禁用

**示例：**
```javascript
// 禁用日志（临时）
$setProxyLogging(false);
obj.sensitiveOperation();

// 重新启用
$setProxyLogging(true);
```

---

### `$printProxyLogs(filter)`

格式化打印日志到 console。

**参数：**
- `filter`: 过滤选项（同 `$getProxyLogs`）

**示例：**
```javascript
$printProxyLogs();
$printProxyLogs({ type: 'call' });
```

---

### `$proxyGlobal(globalName, options)`

代理全局对象。

**参数：**
- `globalName`: 全局对象名称（字符串）
- `options`: 代理选项（同 `$proxy`）

**返回：** Proxy 对象

**示例：**
```javascript
// 创建全局对象
globalThis.myAPI = {
    token: '',
    call(endpoint) { return this.token + ':' + endpoint; }
};

// 代理全局对象
$proxyGlobal('myAPI');

// 之后所有对 myAPI 的操作都会被记录
myAPI.token = 'secret';
myAPI.call('/users');
```

---

## 高级用法

### 1. 自定义过滤器

只记录包含特定关键词的属性：

```python
ctx.evaluate("""
    const data = {
        publicInfo: 'visible',
        secretKey: 'hidden_key',
        apiToken: 'hidden_token',
        username: 'admin'
    };

    const filtered = $proxy(data, {
        name: 'Data',
        filter: (type, prop, value) => {
            // 只记录包含 'secret' 或 'token' 的属性
            return prop.toLowerCase().includes('secret') ||
                   prop.toLowerCase().includes('token');
        }
    });

    // 访问所有属性
    filtered.publicInfo;    // 不记录
    filtered.secretKey;     // 记录
    filtered.apiToken;      // 记录
    filtered.username;      // 不记录

    $getProxyLogs();
""")
```

---

### 2. 追踪函数调用链

监控加密函数的完整调用过程：

```python
ctx = never_jscore.Context()

ctx.compile("""
    const crypto = {
        init(salt) {
            this.key = this.generateKey(salt);
            return this.key;
        },
        generateKey(salt) {
            return md5('secret_' + salt);
        },
        encrypt(data) {
            const iv = this.generateIV();
            return btoa(data + this.key + iv);
        },
        generateIV() {
            return Math.random().toString(36);
        }
    };

    globalThis.encryptModule = crypto;
""")

# 代理加密模块
ctx.evaluate("$proxyGlobal('encryptModule')")
ctx.evaluate("$clearProxyLogs()")

# 执行加密
result = ctx.evaluate("""
    encryptModule.init('user123');
    encryptModule.encrypt('sensitive_data');
""")

# 分析调用链
logs = ctx.evaluate("$getProxyLogs({ type: 'call' })")

print("Function call chain:")
for log in logs:
    print(f"  → {log['property']}({log['arguments']})")
```

**输出：**
```
Function call chain:
  → init(['user123'])
  → generateKey(['user123'])
  → encrypt(['sensitive_data'])
  → generateIV([])
```

---

### 3. 提取加密密钥

配合 `$return()` 提前返回密钥：

```python
ctx = never_jscore.Context()

# 加载目标代码
ctx.compile(open('obfuscated_crypto.js').read())

# 代理加密对象
ctx.evaluate("$proxyGlobal('cryptoModule')")

# 执行并拦截
result = ctx.evaluate("""
    cryptoModule.encrypt('test_data');

    // 获取日志
    const logs = $getProxyLogs({ property: 'key' });

    // 如果找到密钥访问，提前返回
    if (logs.length > 0) {
        $return({ key: logs[0].value, logs: logs });
    }
""")

print(f"Extracted key: {result['key']}")
```

---

### 4. 监控动态属性生成

检测运行时动态创建的属性：

```python
ctx.evaluate("""
    const tracker = {};
    const proxied = $proxy(tracker, { name: 'Tracker' });

    // 动态生成属性
    for (let i = 0; i < 5; i++) {
        proxied['prop_' + i] = 'value_' + i;
    }

    // 查看所有设置操作
    const setOps = $getProxyLogs({ type: 'set' });
    setOps.map(log => log.property);
""")
# 输出: ['prop_0', 'prop_1', 'prop_2', 'prop_3', 'prop_4']
```

---

### 5. 时间线分析

根据时间戳分析操作顺序：

```python
result = ctx.evaluate("""
    const obj = { x: 0 };
    const p = $proxy(obj, { name: 'Obj' });

    const start = Date.now();

    p.x = 1;
    // ... 一些操作
    p.x = 2;

    // 只获取最近的操作
    $getProxyLogs({ since: start });
""")

# 按时间排序
sorted_logs = sorted(result, key=lambda x: x['timestamp'])
for log in sorted_logs:
    print(f"{log['timestamp']}: {log['type']} {log['property']}")
```

---

## 逆向工程实战示例

### 场景 1：Akamai Sensor 分析

```python
import never_jscore

ctx = never_jscore.Context()

# 加载 Akamai 脚本
ctx.compile(open('akamai_sensor.js').read())

# 代理关键对象
ctx.evaluate("""
    // 假设 Akamai 使用全局对象 _cf
    if (typeof _cf !== 'undefined') {
        $proxyGlobal('_cf', {
            logGet: true,
            logCall: true,
            // 只记录看起来重要的属性
            filter: (type, prop) => {
                const important = ['sensor', 'token', 'key', 'hash', 'sign'];
                return important.some(k => prop.toLowerCase().includes(k));
            }
        });
    }
""")

# 触发 sensor 生成
sensor = ctx.call('generateSensor', [{'username': 'test'}])

# 分析日志
logs = ctx.evaluate("$getProxyLogs()")

print(f"Captured {len(logs)} operations")
print("\nKey operations:")
for log in logs:
    if log['type'] == 'call':
        print(f"  Function: {log['property']}")
```

---

### 场景 2：API 签名算法

```python
ctx = never_jscore.Context()

# 加载签名脚本
ctx.compile("""
    const SignModule = {
        secret: '',
        timestamp: 0,

        init() {
            this.secret = this.getSecret();
            this.timestamp = Date.now();
        },

        getSecret() {
            return md5('app_secret_' + navigator.userAgent);
        },

        sign(params) {
            const sorted = Object.keys(params).sort().join('&');
            return sha256(sorted + this.secret + this.timestamp);
        }
    };

    globalThis.SignModule = SignModule;
""")

# 代理签名模块
ctx.evaluate("$proxyGlobal('SignModule')")

# 清空历史日志
ctx.evaluate("$clearProxyLogs()")

# 执行签名
signature = ctx.call('SignModule.sign', [{'user': '123', 'action': 'login'}])

# 分析签名过程
logs = ctx.evaluate("$getProxyLogs()")

# 提取密钥
secret_logs = [log for log in logs if 'secret' in log.get('property', '').lower()]
if secret_logs:
    print(f"Secret key: {secret_logs[0]['value']}")

# 查看函数调用顺序
calls = [log for log in logs if log['type'] == 'call']
print(f"Signing process: {' -> '.join([c['property'] for c in calls])}")
```

---

### 场景 3：检测反调试

```python
ctx.evaluate("""
    // 代理常见的反调试检测对象
    const devtools = {
        isOpen: false,
        check() {
            // 模拟反调试检测
            return this.isOpen;
        }
    };

    globalThis.devtools = devtools;
    $proxyGlobal('devtools');

    // 执行可能包含反调试的代码
    // ...

    // 查看是否有反调试检测
    const checks = $getProxyLogs({ property: 'isOpen' });
    checks.length > 0;  // true 表示有反调试
""")
```

---

## 性能考虑

### 日志数量限制

大量日志会占用内存，建议：

```javascript
// 方式 1: 定期清理
setInterval(() => {
    const logs = $getProxyLogs();
    if (logs.length > 10000) {
        // 保存到 Python 侧
        $return({ savedLogs: logs });
        $clearProxyLogs();
    }
}, 1000);

// 方式 2: 只记录关键操作
const proxied = $proxy(obj, {
    filter: (type, prop) => {
        // 只记录包含 'key', 'token', 'secret' 的属性
        return /key|token|secret/i.test(prop);
    }
});

// 方式 3: 临时禁用
$setProxyLogging(false);
// 执行不需要监控的代码
obj.heavyOperation();
$setProxyLogging(true);
```

---

## 与现有功能结合

### 配合 Hook 系统

```python
result = ctx.evaluate("""
    const api = { token: '' };
    const p = $proxy(api, { name: 'API' });

    p.token = 'secret_123';

    // 获取日志并提前返回
    const logs = $getProxyLogs();
    $return({ token: p.token, logs: logs });
""")

print(f"Token: {result['token']}")
print(f"Operations: {len(result['logs'])}")
```

### 配合确定性随机数

```python
# 使用固定种子，确保每次运行日志相同
ctx = never_jscore.Context(random_seed=12345)

ctx.evaluate("""
    const rng = { generate() { return Math.random(); } };
    const p = $proxy(rng, { name: 'RNG' });

    p.generate();
    p.generate();

    $getProxyLogs();
""")
# 每次运行，日志顺序和内容都相同
```

---

## 最佳实践

### ✅ 推荐做法

1. **明确命名代理对象**
   ```javascript
   $proxy(obj, { name: 'CryptoModule' });  // 好
   $proxy(obj);  // 可以，但不够清晰
   ```

2. **使用过滤器减少噪音**
   ```javascript
   $proxy(obj, {
       filter: (type, prop) => !prop.startsWith('_')  // 忽略私有属性
   });
   ```

3. **定期清理日志**
   ```javascript
   $clearProxyLogs();  // 在关键操作前清理
   ```

4. **结合 Python 分析**
   ```python
   logs = ctx.evaluate("$getProxyLogs()")
   # 在 Python 侧做复杂分析
   import pandas as pd
   df = pd.DataFrame(logs)
   ```

### ❌ 避免的做法

1. **不要代理大型对象**
   ```javascript
   $proxy(document);  // ❌ 会产生大量日志
   ```

2. **不要在循环中代理**
   ```javascript
   for (let i = 0; i < 1000; i++) {
       $proxy({});  // ❌ 性能差
   }
   ```

3. **不要忘记清理**
   ```javascript
   // ❌ 日志无限增长
   while (true) {
       proxied.value++;
   }
   ```

---

## 常见问题

### Q: 代理会影响性能吗？

A: 有轻微影响。Proxy 本身性能很好，但日志记录会增加开销。建议：
- 只代理关键对象
- 使用 `filter` 减少日志量
- 定期清理日志

### Q: 可以代理内置对象吗（如 Math, JSON）？

A: 可以，但要小心：
```javascript
const originalMath = Math;
Math = $proxy(originalMath, { name: 'Math' });
```

### Q: 日志中的 value 是引用还是副本？

A: 是引用。如果对象被修改，日志中的 value 也会变化。如果需要快照：
```javascript
filter: (type, prop, value) => {
    if (typeof value === 'object') {
        value = JSON.parse(JSON.stringify(value));  // 深拷贝
    }
    return true;
}
```

### Q: 如何保存日志到文件？

A: 在 Python 侧处理：
```python
import json

logs = ctx.evaluate("$getProxyLogs()")

with open('proxy_logs.json', 'w') as f:
    json.dump(logs, f, indent=2)
```

---

## 总结

Proxy 日志系统提供了强大的对象监控能力，特别适合：

- 🔍 **逆向工程**：追踪加密算法和 API 签名
- 🐛 **调试分析**：理解复杂代码的执行流程
- 🔒 **安全研究**：检测反调试和指纹识别
- 📊 **数据提取**：捕获动态生成的配置和密钥

配合 never_jscore 的其他功能（Hook 系统、确定性随机数、堆快照），构成完整的 JS 逆向工程工具链！
