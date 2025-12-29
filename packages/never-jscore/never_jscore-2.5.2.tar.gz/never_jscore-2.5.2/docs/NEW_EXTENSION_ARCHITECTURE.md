# 新模块化扩展架构 (New Modular Extension Architecture)

## 概述 (Overview)

never_jscore v2.5.0+ 引入了全新的模块化扩展架构，参考 [rustyscript](https://github.com/rscarson/rustyscript) 的设计理念，提供：
- **模块化设计**: 每个扩展独立管理，易于维护和扩展
- **统一接口**: `ExtensionTrait` 提供标准化的扩展加载接口
- **增强的API保护**: 完善的反检测工具集
- **更好的代码组织**: 清晰的目录结构和职责划分

## 架构对比 (Architecture Comparison)

### 旧架构 (Old)
```
src/ops/storage_ops.rs  # 所有 ops 集中在一个文件
src/ext/mod.rs          # 简单的扩展配置
```

### 新架构 (New)
```
src/ext/
├── mod.rs                    # 扩展系统核心（ExtensionTrait, ExtensionOptions）
├── core/
│   ├── mod.rs               # 核心扩展（$return, $exit, $storeResult）
│   └── init_core.js         # JavaScript 初始化代码
├── hook/
│   ├── mod.rs               # Hook 扩展（$terminate, $saveAndTerminate）
│   └── init_hook.js         # JavaScript 初始化代码
├── api_protection.js        # API 保护工具集（增强版）
├── init_fetch.js            # Fetch API 初始化
├── telemetry.ts             # Telemetry stub
└── util.ts                  # Utility functions
```

## 核心组件 (Core Components)

### 1. ExtensionTrait

统一的扩展接口，提供：
- `init(options)`: 初始化扩展
- `for_snapshot(ext)`: Snapshot 优化
- `build(options, is_snapshot)`: 构建扩展

```rust
pub trait ExtensionTrait<Options> {
    fn init(options: Options) -> Extension;

    fn for_snapshot(mut ext: Extension) -> Extension {
        ext.js_files = ::std::borrow::Cow::Borrowed(&[]);
        ext.esm_files = ::std::borrow::Cow::Borrowed(&[]);
        ext.esm_entry_point = ::std::option::Option::None;
        ext
    }

    fn build(options: Options, is_snapshot: bool) -> Extension {
        let ext = Self::init(options);
        if is_snapshot {
            Self::for_snapshot(ext)
        } else {
            ext
        }
    }
}
```

### 2. ExtensionOptions

集中管理所有扩展配置：

```rust
pub struct ExtensionOptions {
    pub enable_logging: bool,
    pub random_seed: Option<u64>,
    pub enable_extensions: bool,
    pub storage: std::rc::Rc<ResultStorage>,

    #[cfg(feature = "deno_web_api")]
    pub permissions: Option<PermissionsContainer>,

    #[cfg(feature = "deno_web_api")]
    pub blob_store: Option<Arc<deno_web::BlobStore>>,
}
```

### 3. Core Extension (核心扩展)

**位置**: `src/ext/core/`

**提供的 JavaScript 函数**:
- `$return(value)`: 早期返回（可被 try-catch 捕获）
- `$exit(value)`: `$return` 的别名
- `$storeResult(value)`: 存储结果到 Rust 端
- `__neverjscore_return__(value)`: 向后兼容的早期返回

**使用示例**:
```javascript
// 可被 try-catch 捕获的早期返回
function process(data) {
    if (data.intercepted) {
        $return({ key: data.intercepted });
    }
    return normalProcess(data);
}
```

### 4. Hook Extension (Hook 拦截扩展)

**位置**: `src/ext/hook/`

**提供的 JavaScript 函数**:
- `$terminate(data)`: 强制终止执行（**不能**被 try-catch 捕获）
- `__saveAndTerminate__(data)`: `$terminate` 的别名

**使用示例**:
```javascript
// Hook 加密函数，提取密钥（无法被 try-catch 阻止）
const original = CryptoLib.encrypt;
CryptoLib.encrypt = function(text, key) {
    $terminate({ text, key });  // 强制终止，uncatchable!
};

try {
    login('user', 'password');  // 触发加密
} catch (e) {
    // 这里不会执行 - terminate 绕过 try-catch
}
```

**Python 端获取数据**:
```python
ctx.clear_hook_data()
try:
    ctx.evaluate(hook_code)
except:
    pass  # Python 捕获 termination

# 获取拦截的数据
hook_data = ctx.get_hook_data()
if hook_data:
    data = json.loads(hook_data)
    print(f"Key: {data['key']}")
```

### 5. API Protection (API 保护增强)

**位置**: `src/ext/api_protection.js`

**新增功能**:

#### 基础工具
- `nonEnumerable(value)`: 创建不可枚举属性
- `readOnly(value)`: 创建只读属性
- `writeable(value)`: 创建可写属性
- `getterOnly(getter)`: 创建只读 getter 属性

#### 应用工具
- `applyToGlobal(properties)`: 应用到 globalThis
- `applyToDeno(properties)`: 应用到 Deno 命名空间

#### Native Code 模拟
- `makeNative(fn, name)`: 让函数看起来像原生代码
- `makeAllNative(obj)`: 批量处理对象中的所有函数
- `protectConstructor(constructor, name)`: 保护构造函数及其原型

#### 高级保护
- `hideProperty(obj, prop)`: 隐藏属性（不可枚举）
- `freezeProperty(obj, prop)`: 冻结属性（不可修改）
- `hideDeno()`: 隐藏 Deno 特征（提高浏览器兼容性）
- `createNativeProxy(target, handler)`: 创建原生外观的代理
- `deepProtect(obj, deep)`: 深度冻结对象
- `cleanStack(error, patterns)`: 清理错误堆栈中的内部信息

**使用示例**:
```javascript
import { makeNative, protectConstructor, hideDeno } from 'ext:api_protection/api_protection.js';

// 让自定义函数看起来像原生代码
function myFetch(url) { /* ... */ }
makeNative(myFetch, 'fetch');
console.log(myFetch.toString());  // "function fetch() { [native code] }"

// 保护构造函数
class MyError extends Error {}
protectConstructor(MyError, 'Error');

// 隐藏 Deno 特征
hideDeno();
console.log(Object.keys(globalThis).includes('Deno'));  // false
```

## 使用方式 (Usage)

### Python API (保持向后兼容)

```python
import never_jscore

# 创建 Context (自动加载所有扩展)
ctx = never_jscore.Context()

# 使用 $return (可被 try-catch 捕获)
result = ctx.evaluate("""
    try {
        $return({ data: 'intercepted' });
    } catch (e) {
        ({ caught: true });
    }
""")
print(result)  # {'caught': True}

# 使用 $terminate (不能被 try-catch 捕获)
ctx.clear_hook_data()
try:
    ctx.evaluate("""
        try {
            $terminate({ secret: 'key123' });
        } catch (e) {
            'this will not execute';
        }
    """)
except:
    pass

# 获取拦截的数据
hook_data = ctx.get_hook_data()
if hook_data:
    import json
    data = json.loads(hook_data)
    print(f"Secret: {data['secret']}")  # Secret: key123
```

### 实战场景: Hook 加密函数

```python
import never_jscore
import json

ctx = never_jscore.Context()

# 加载目标代码
ctx.compile("""
    const CryptoLib = {
        encrypt: function(text, key) {
            return btoa(text + key);  // 原始加密
        }
    };

    function login(username, password) {
        const encrypted = CryptoLib.encrypt(password, 'secret_key');
        return { username, encrypted };
    }
""")

# Hook encrypt 函数
ctx.clear_hook_data()
try:
    ctx.evaluate("""
        const original = CryptoLib.encrypt;
        CryptoLib.encrypt = function(text, key) {
            // 拦截参数并强制终止
            $terminate({ text, key, timestamp: Date.now() });
        };

        try {
            login('admin', 'mypassword');
        } catch (e) {
            // try-catch 无法阻止 terminate!
        }
    """)
except:
    pass  # Python 捕获

# 提取密钥
hook_data = ctx.get_hook_data()
if hook_data:
    data = json.loads(hook_data)
    print(f"密码: {data['text']}")  # mypassword
    print(f"密钥: {data['key']}")   # secret_key
```

## 扩展系统加载流程 (Extension Loading Flow)

1. **Context 创建时**:
   ```rust
   let ext_options = ExtensionOptions::new(storage)
       .with_logging(enable_logging)
       .with_random_seed(random_seed);

   let extensions = all_extensions(ext_options, false);
   ```

2. **首次执行时**:
   - 自动加载 `init_core.js` (核心函数)
   - 自动加载 `init_hook.js` (Hook 函数)
   - 后续执行直接使用已加载的函数

3. **运行时**:
   - JavaScript 调用 `$return()` / `$terminate()`
   - Rust ops 处理数据存储/终止
   - Python 获取结果

## 测试 (Testing)

```bash
# 运行新扩展系统测试
python tests/test_new_extension_system.py

# 测试覆盖:
# ✓ Core Extension - $return 功能
# ✓ Core Extension - $exit 功能
# ✓ Hook Extension - $terminate (uncatchable)
# ✓ Hook Interception 实战场景
# ✓ API Protection 功能
# ✓ Context 重用
```

## 与 Rustyscript 的对比 (Comparison with Rustyscript)

| 特性 | rustyscript | never_jscore |
|------|-------------|--------------|
| ExtensionTrait | ✓ | ✓ |
| 模块化扩展 | ✓ | ✓ |
| Snapshot 支持 | ✓ | ✓ |
| ESM 模块加载 | ✓ (esm_entry_point) | ✗ (运行时加载) |
| API 保护 | ✓ (基础) | ✓ (增强版) |
| Hook 拦截 | ✓ (terminate_js) | ✓ ($terminate + $return) |
| Python 绑定 | ✗ | ✓ (PyO3) |

## 未来改进 (Future Improvements)

1. **ESM 模块支持**: 升级 deno_core 以支持 `esm_entry_point`
2. **更多扩展**:
   - Timer 扩展 (定时器管理)
   - Storage 扩展 (localStorage/sessionStorage)
   - Crypto 扩展 (增强加密功能)
3. **Snapshot 优化**: 预编译常用扩展到 snapshot
4. **权限系统**: 细粒度权限控制 (参考 deno_permissions)
5. **插件系统**: 允许用户自定义扩展

## 参考资料 (References)

- [rustyscript 扩展系统](https://github.com/rscarson/rustyscript/tree/main/src/ext)
- [Deno Core Extensions](https://github.com/denoland/deno_core)
- [never_jscore 文档](../CLAUDE.md)

## 版本历史 (Version History)

- **v2.5.0**: 引入新模块化扩展架构
  - 创建 `ext/core` 和 `ext/hook` 模块
  - 增强 `api_protection.js`
  - 统一 `ExtensionTrait` 和 `ExtensionOptions`
  - 完整测试覆盖

---

**贡献者**: Claude Code + never_jscore team
**最后更新**: 2025-01-25
