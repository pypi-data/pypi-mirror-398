# 浏览器环境保护使用指南

## 功能概述

never_jscore v2.4.2+ 内置了完整的**浏览器环境保护系统**，自动隐藏 Deno/Node.js 特征，让 JavaScript 代码无法检测出运行在非浏览器环境中。

## 核心特性

### ✅ 自动保护（无需配置）

所有保护措施**开箱即用**，创建 Context 时自动激活：

```python
import never_jscore

ctx = never_jscore.Context()  # 自动启用所有保护
```

### 🔒 保护内容

| 保护项 | 说明 | 检测方法 |
|-------|------|---------|
| ✅ 隐藏 Deno 对象 | `Deno` 被设置为 `undefined` | `typeof Deno === 'undefined'` |
| ✅ 函数原生化 | 所有函数看起来像原生代码 | `btoa.toString()` 返回 `[native code]` |
| ✅ window 对象 | `window === globalThis` | `window === self === top` |
| ✅ chrome 对象 | 添加 Chrome 特有对象 | `typeof chrome === 'object'` |
| ✅ 属性描述符 | 符合浏览器标准 | `Object.getOwnPropertyDescriptor()` |
| ✅ 原型链 | 保持浏览器原型结构 | `Function.prototype.toString` |

---

## 验证保护效果

### 1. 检测 Deno 是否被隐藏

```python
import never_jscore

ctx = never_jscore.Context()

# 检查 1: typeof
assert ctx.evaluate('typeof Deno') == 'undefined'

# 检查 2: 严格相等
assert ctx.evaluate('Deno === undefined') == True

# 检查 3: 'in' 操作符
assert ctx.evaluate('"Deno" in window') == True  # 属性存在
assert ctx.evaluate('window.Deno === undefined') == True  # 但值是 undefined
```

### 2. 检测函数是否看起来原生

```python
# 所有函数的 toString() 都返回 [native code]
functions = [
    'btoa', 'atob', 'setTimeout', 'setInterval',
    'fetch', 'encodeURI', 'md5', 'sha256'
]

for func in functions:
    result = ctx.evaluate(f'{func}.toString()')
    assert '[native code]' in result, f'{func} not native-looking'
```

### 3. 检测浏览器对象

```python
# window, self, top 都指向 globalThis
assert ctx.evaluate('window === globalThis') == True
assert ctx.evaluate('self === globalThis') == True
assert ctx.evaluate('top === globalThis') == True

# chrome 对象存在
assert ctx.evaluate('typeof chrome') == 'object'
assert ctx.evaluate('typeof chrome.runtime') == 'object'
```

### 4. 使用内置环境检测

```python
# 使用 $checkEnvironment() 自动检测问题
issues = ctx.evaluate('$checkEnvironment()')

if len(issues) == 0:
    print('✓ 环境完美伪装')
else:
    print(f'✗ 发现 {len(issues)} 个问题:')
    for issue in issues:
        print(f'  - {issue}')
```

---

## 高级用法

### 自定义对象保护

使用 `$protect()` 保护你自己创建的对象：

```python
ctx.evaluate("""
    // 创建自定义加密模块
    const myCrypto = {
        version: '1.0',
        encrypt(data) {
            return btoa(data);
        },
        decrypt(data) {
            return atob(data);
        }
    };

    // 保护它，让所有方法看起来像原生函数
    $protect(myCrypto, 'myCrypto');

    // 验证
    console.log(myCrypto.encrypt.toString());
    // 输出: function encrypt() { [native code] }
""")
```

### 自定义函数原生化

使用 `$makeNative()` 让单个函数看起来原生：

```python
ctx.evaluate("""
    function myCustomFunction(x) {
        return x * 2;
    }

    // 让它看起来像原生函数
    $makeNative(myCustomFunction, 'myCustomFunction');

    console.log(myCustomFunction.toString());
    // 输出: function myCustomFunction() { [native code] }
""")
```

---

## 常见检测手段及对抗

### 检测 1: 直接检查 Deno/process

**攻击代码：**
```javascript
if (typeof Deno !== 'undefined') {
    console.log('检测到 Deno!');
}

if (typeof process !== 'undefined' && process.versions.node) {
    console.log('检测到 Node.js!');
}
```

**never_jscore 防御：**
- ✅ `Deno` 被设置为 `undefined`
- ✅ `process` 存在但伪装成浏览器环境的 polyfill

**验证：**
```python
ctx.evaluate("""
    console.log(typeof Deno);  // 'undefined'
    console.log(typeof process);  // 'object' (伪造的)
""")
```

---

### 检测 2: 检查函数 toString

**攻击代码：**
```javascript
if (!btoa.toString().includes('[native code]')) {
    console.log('btoa 不是原生函数!');
}

if (Function.prototype.toString.toString() !== 'function toString() { [native code] }') {
    console.log('Function.prototype.toString 被修改!');
}
```

**never_jscore 防御：**
- ✅ 所有函数的 `toString()` 返回 `[native code]`
- ✅ `Function.prototype.toString` 本身也被保护

**验证：**
```python
result = ctx.evaluate("""
    const checks = [
        btoa.toString().includes('[native code]'),
        atob.toString().includes('[native code]'),
        setTimeout.toString().includes('[native code]'),
        Function.prototype.toString.toString().includes('[native code]')
    ];
    checks.every(x => x);  // 全部通过
""")
assert result == True
```

---

### 检测 3: 检查 window 对象

**攻击代码：**
```javascript
if (typeof window === 'undefined') {
    console.log('不是浏览器环境!');
}

if (window !== globalThis || window !== self) {
    console.log('window 对象不正常!');
}
```

**never_jscore 防御：**
- ✅ `window` 存在且等于 `globalThis`
- ✅ `self`, `top`, `parent` 都正确指向

**验证：**
```python
assert ctx.evaluate('typeof window') == 'object'
assert ctx.evaluate('window === globalThis') == True
assert ctx.evaluate('window === self') == True
```

---

### 检测 4: 检查 navigator/chrome

**攻击代码：**
```javascript
if (typeof navigator === 'undefined') {
    console.log('缺少 navigator!');
}

if (typeof chrome === 'undefined') {
    console.log('不是 Chrome 浏览器!');
}

if (!navigator.userAgent.includes('Chrome')) {
    console.log('User-Agent 不正常!');
}
```

**never_jscore 防御：**
- ✅ `navigator` 对象完整（UA, platform, language...）
- ✅ `chrome` 对象存在（runtime, app, loadTimes...）
- ✅ User-Agent 伪装成 Chrome 120

**验证：**
```python
assert ctx.evaluate('typeof navigator') == 'object'
assert ctx.evaluate('typeof chrome') == 'object'
ua = ctx.evaluate('navigator.userAgent')
assert 'Chrome' in ua
assert 'Deno' not in ua
```

---

### 检测 5: 属性描述符检查

**攻击代码：**
```javascript
const desc = Object.getOwnPropertyDescriptor(window, 'navigator');
if (desc.configurable) {
    console.log('navigator 可以被修改，不正常!');
}
```

**never_jscore 防御：**
- ✅ 关键属性设置为不可配置
- ✅ 符合浏览器标准

**验证：**
```python
result = ctx.evaluate("""
    const desc = Object.getOwnPropertyDescriptor(window, 'navigator');
    desc.configurable === false;
""")
assert result == True
```

---

## 实战示例

### 示例 1：绕过 Akamai 环境检测

```python
import never_jscore

ctx = never_jscore.Context()

# Akamai 可能会检测这些特征
ctx.evaluate("""
    // 1. 检查 Deno
    if (typeof Deno !== 'undefined') {
        throw new Error('Detected Deno');
    }

    // 2. 检查函数原生性
    if (!btoa.toString().includes('[native code]')) {
        throw new Error('btoa is not native');
    }

    // 3. 检查 window
    if (window !== globalThis) {
        throw new Error('window mismatch');
    }

    // 4. 检查 chrome
    if (typeof chrome === 'undefined') {
        throw new Error('Not Chrome');
    }

    console.log('✓ All checks passed!');
""")
```

### 示例 2：分析混淆代码的环境检测

```python
ctx = never_jscore.Context()

# 加载目标混淆代码
ctx.compile(open('obfuscated.js').read())

# 使用 Proxy 监控环境检测
ctx.evaluate("""
    // 代理 window 对象，监控属性访问
    const originalWindow = window;
    window = $proxy(originalWindow, {
        name: 'window',
        filter: (type, prop) => {
            // 只记录可疑的检测行为
            const suspiciousProps = ['Deno', 'process', '__dirname', 'require'];
            return suspiciousProps.includes(prop);
        }
    });

    // 执行可能包含检测的代码
    // ...

    // 查看检测日志
    const logs = $getProxyLogs();
    if (logs.length > 0) {
        console.log('检测到环境检测行为:');
        logs.forEach(log => {
            console.log(`  - 访问了 ${log.property}`);
        });
    }
""")
```

### 示例 3：完整的反检测工作流

```python
import never_jscore

def test_anti_detection():
    """测试目标 JS 是否能检测出环境"""
    ctx = never_jscore.Context()

    # 步骤 1: 检查基础环境
    issues = ctx.evaluate('$checkEnvironment()')
    if issues:
        print(f'[警告] 发现 {len(issues)} 个问题')
        return False

    # 步骤 2: 加载目标代码
    ctx.compile(open('target.js').read())

    # 步骤 3: Hook console.error 捕获检测警告
    ctx.evaluate("""
        const errors = [];
        const originalError = console.error;
        console.error = function(...args) {
            errors.push(args.join(' '));
            originalError.apply(console, args);
        };
        globalThis.__getErrors = () => errors;
    """)

    # 步骤 4: 执行目标函数
    try:
        result = ctx.call('targetFunction', ['test'])
        print(f'[成功] 函数执行成功: {result}')
    except Exception as e:
        print(f'[失败] 函数抛出错误: {e}')
        return False

    # 步骤 5: 检查是否有检测警告
    errors = ctx.evaluate('__getErrors()')
    if errors:
        print(f'[警告] 捕获到 {len(errors)} 个 console.error:')
        for err in errors:
            print(f'  - {err}')
        return False

    print('[成功] 完全绕过检测!')
    return True

if __name__ == '__main__':
    test_anti_detection()
```

---

## 常见问题

### Q: 保护会影响性能吗？

A: 几乎无影响。保护只在初始化时执行一次，运行时零开销。

### Q: 可以自定义 User-Agent 吗？

A: 可以，在创建 Context 后修改：

```python
ctx.evaluate("""
    Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (Custom UA)',
        writable: false,
        enumerable: true,
        configurable: false
    });
""")
```

### Q: 如果目标代码检测到伪造怎么办？

A: 使用 `$proxy()` 监控哪些属性被检测了，然后针对性加强保护：

```python
ctx.evaluate("""
    // 监控 navigator 访问
    navigator = $proxy(navigator, { name: 'navigator' });

    // 执行目标代码
    // ...

    // 查看访问了哪些属性
    const logs = $getProxyLogs({ target: 'navigator' });
    console.log('Navigator 属性访问:', logs.map(l => l.property));
""")
```

### Q: $protect() 和 $makeNative() 有什么区别？

A:
- `$protect(obj, name)`: 保护整个对象及其所有方法
- `$makeNative(func, name)`: 只保护单个函数

### Q: 内部还能访问 Deno API 吗？

A: 可以，使用 `__getDeno()`：

```python
ctx.evaluate("""
    // 外部看不到 Deno
    console.log(typeof Deno);  // 'undefined'

    // 但内部可以访问（仅用于 polyfill 内部）
    const deno = __getDeno();
    console.log(deno.core.ops);  // 可以访问
""")
```

⚠️ **警告**：不要在用户代码中暴露 `__getDeno()`，否则保护失效。

---

## 总结

### ✅ 自动保护（开箱即用）

- 隐藏 Deno 对象
- 函数原生化
- 浏览器对象完整
- 属性描述符符合标准

### 🛠 手动工具

- `$checkEnvironment()` - 检测保护效果
- `$protect(obj, name)` - 保护自定义对象
- `$makeNative(func, name)` - 原生化函数
- `$proxy(obj, options)` - 监控访问（配合使用）

### 🎯 适用场景

- 绕过 JS 逆向中的环境检测
- 运行 Akamai/PerimeterX 等反爬代码
- 测试混淆代码的检测机制
- 确保 JS 代码认为运行在浏览器中

**配合 never_jscore 的其他功能（Proxy 日志、Hook 系统、堆快照），构成完整的 JS 逆向工程解决方案！**
