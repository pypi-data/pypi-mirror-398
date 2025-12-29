"""
never_jscore - 基于 Deno Core 的 JavaScript 运行时

完整支持 Promise 和 async/await，适合 JS 逆向分析。
py_mini_racer 风格的实例化 API。
"""

from typing import Any, List, Union, Optional

class Context:
    """
    JavaScript 执行上下文（支持异步）

    每个 Context 包含一个独立的 V8 isolate 和 JavaScript 运行时环境。
    默认自动等待 Promise，可以无缝调用异步 JavaScript 函数。

    ⚠️ 重要限制:
    - 创建第二个 Context 后，不能再使用第一个 Context
    - 多个 Context 必须按 LIFO 顺序删除（后创建先删除）
    - 推荐使用单 Context 模式，将所有函数定义在一个 Context 中

    🆕 扩展功能 (enable_extensions=True 时自动加载):
    - Web APIs: fetch, URL, TextEncoder/Decoder, crypto, Blob, FormData
    - 定时器: setTimeout, setInterval, clearTimeout, clearInterval
    - 存储: localStorage, sessionStorage
    - 事件: AbortController, Event, EventTarget
    - 流: ReadableStream, WritableStream, TransformStream

    🆕 Node.js 兼容 (enable_node_compat=True 时启用):
    - require() 函数加载 npm 包
    - Node.js 内置模块: path, fs, crypto, buffer, etc.
    - 支持 jsdom 等复杂 npm 包

    Example:
        >>> # 基本用法（默认启用 Web API 扩展）
        >>> ctx = Context()
        >>> ctx.compile("function add(a, b) { return a + b; }")
        >>> result = ctx.call("add", [1, 2])
        >>> print(result)
        3

        >>> # 使用 Web API
        >>> ctx = Context()
        >>> result = ctx.evaluate("btoa('hello')")
        >>> print(result)
        aGVsbG8=

        >>> # 使用 Node.js 兼容模式加载 npm 包
        >>> ctx = Context(enable_node_compat=True)
        >>> result = ctx.evaluate('''
        ...     const { JSDOM } = require('jsdom');
        ...     const dom = new JSDOM('<h1>Hello</h1>');
        ...     dom.window.document.querySelector('h1').textContent
        ... ''')
        >>> print(result)
        Hello

        >>> # 纯净 V8 环境（不加载扩展）
        >>> ctx = Context(enable_extensions=False)
        >>> # 只有 ECMAScript 标准 API
    """

    def __init__(
        self,
        enable_extensions: bool = True,
        enable_logging: bool = False,
        random_seed: Optional[int] = None,
        enable_node_compat: bool = False  # Default False - only enable when you need require()
    ) -> None:
        """
        创建一个新的 JavaScript 执行上下文

        Args:
            enable_extensions: 是否启用 Web API 扩展，默认 True
                             - True: 加载 Deno Web API（fetch, URL, crypto 等）
                             - False: 纯净 V8 环境，只包含 ECMAScript 标准 API
            enable_logging: 是否启用操作日志输出，默认 False
                           - True: 输出所有扩展操作的日志（用于调试）
                           - False: 不输出日志（推荐生产环境）
            random_seed: 随机数种子（可选），用于确定性随机数生成
                        - None: 使用系统随机数（非确定性）
                        - int: 使用固定种子（确定性）
                          所有随机数 API（Math.random、crypto.getRandomValues 等）
                          将基于此种子生成，方便调试和算法对比
            enable_node_compat: 是否启用 Node.js 兼容模式，默认 False
                               - True: 启用 require() 和 Node.js 内置模块
                                 可以加载 npm 包如 jsdom、lodash 等
                               - False: 不加载 Node.js 兼容层

        Example:
            >>> # 使用固定随机数种子
            >>> ctx = Context(random_seed=12345)
            >>> r1 = ctx.evaluate("Math.random()")  # 确定性随机数
            >>> r2 = ctx.evaluate("Math.random()")  # 下一个确定性随机数
            >>>
            >>> # 另一个相同种子的上下文将产生相同的随机数序列
            >>> ctx2 = Context(random_seed=12345)
            >>> r3 = ctx2.evaluate("Math.random()")  # r3 == r1

            >>> # 使用 Node.js 兼容模式
            >>> ctx = Context(enable_node_compat=True)
            >>> ctx.evaluate("const path = require('path'); path.join('a', 'b')")
            'a/b'
        """
        ...

    def compile(self, code: str) -> None:
        """
        编译 JavaScript 代码并加入全局作用域

        Args:
            code: JavaScript 代码字符串

        Raises:
            Exception: 当代码编译失败时

        Example:
            >>> ctx = Context()
            >>> ctx.compile('''
            ...     function add(a, b) { return a + b; }
            ...     function multiply(a, b) { return a * b; }
            ... ''')
            >>> ctx.call("add", [1, 2])
            3
        """
        ...

    def eval(
        self,
        code: str,
        return_value: bool = True,
        auto_await: Optional[bool] = None
    ) -> Any:
        """
        执行代码并将其加入全局作用域

        Args:
            code: JavaScript 代码字符串
            return_value: 是否返回最后一个表达式的值（默认 False）
            auto_await: 是否自动等待 Promise（默认 True）

        Returns:
            如果 return_value=True，返回最后表达式的值；否则返回 None

        Raises:
            Exception: 当代码执行失败时

        Example:
            >>> ctx = Context()
            >>> ctx.eval("var x = 10;")  # 添加到全局作用域
            >>> result = ctx.eval("x * 2", return_value=True)
            >>> print(result)
            20
        """
        ...

    def evaluate(self, code: str, auto_await: Optional[bool] = None) -> Any:
        """
        执行代码并返回结果（不影响全局作用域）

        Args:
            code: JavaScript 代码字符串
            auto_await: 是否自动等待 Promise（默认 True）

        Returns:
            表达式的值，自动转换为 Python 对象

        Raises:
            Exception: 当代码执行失败时

        Example:
            >>> ctx = Context()
            >>> result = ctx.evaluate("1 + 2 + 3")
            >>> print(result)
            6

            >>> # Promise（自动等待）
            >>> result = ctx.evaluate("Promise.resolve(42)")
            >>> print(result)
            42
        """
        ...

    def call(
        self,
        name: str,
        args: List[Any] = [],
        auto_await: Optional[bool] = None
    ) -> Any:
        """
        调用 JavaScript 函数（支持 Promise）

        Args:
            name: 函数名称
            args: 参数列表
            auto_await: 是否自动等待 Promise（默认 True）

        Returns:
            函数返回值，自动转换为 Python 对象

        Raises:
            Exception: 当函数调用失败时

        Example:
            >>> ctx = Context()
            >>> ctx.compile("async function decrypt(data) { return data.split('').reverse().join(''); }")
            >>> result = ctx.call("decrypt", ["olleh"])
            >>> print(result)
            hello
        """
        ...

    def gc(self) -> None:
        """
        请求 V8 垃圾回收

        注意：这只是向 V8 发送 GC 请求，V8 会根据自己的策略决定是否执行。
        在大多数情况下，V8 的自动 GC 已经足够好，无需手动调用。
        """
        ...

    def get_stats(self) -> dict[str, int]:
        """
        获取执行统计信息

        Returns:
            包含各类操作计数的字典:
            - evaluate_count: evaluate() 调用次数
            - compile_count: compile() 调用次数
            - call_count: call() 调用次数

        Example:
            >>> ctx = Context()
            >>> ctx.evaluate("1 + 1")
            >>> ctx.compile("function test() {}")
            >>> ctx.call("test", [])
            >>> stats = ctx.get_stats()
            >>> print(stats)
            {'evaluate_count': 1, 'compile_count': 1, 'call_count': 1}
        """
        ...

    def reset_stats(self) -> None:
        """
        重置统计信息
        """
        ...

    def get_heap_statistics(self) -> dict[str, int]:
        """
        获取 V8 堆内存统计信息

        Returns:
            包含 V8 堆内存统计的字典:
            - total_heap_size: V8 堆总大小（字节），包括未使用空间
            - used_heap_size: 已使用的堆内存（字节）
            - heap_size_limit: V8 堆大小上限（字节）
            - total_physical_size: 实际物理内存占用（字节）
            - malloced_memory: 通过 malloc 分配的内存（字节）
            - external_memory: 外部对象占用的内存（字节）
            - number_of_native_contexts: 原生上下文数量

        Example:
            >>> ctx = Context()
            >>> ctx.evaluate("const arr = []; for(let i=0; i<10000; i++) arr.push({id:i})")
            >>> heap = ctx.get_heap_statistics()
            >>> print(f"Total: {heap['total_heap_size'] / 1024 / 1024:.2f} MB")
            >>> print(f"Used: {heap['used_heap_size'] / 1024 / 1024:.2f} MB")
            >>> print(f"Usage: {heap['used_heap_size'] / heap['total_heap_size'] * 100:.1f}%")
        """
        ...

    def take_heap_snapshot(self, file_path: str) -> None:
        """
        导出 V8 堆快照到文件（Chrome DevTools 格式）

        导出的 .heapsnapshot 文件可以在 Chrome DevTools 中分析:
        1. 打开 Chrome -> F12 -> Memory 标签
        2. 点击 "Load" 按钮加载快照文件
        3. 查看对象分配、内存泄漏、循环引用等

        Args:
            file_path: 快照文件保存路径（通常以 .heapsnapshot 结尾）

        Raises:
            Exception: 文件创建失败或写入失败时

        Example:
            >>> ctx = Context()
            >>> # 执行一些代码
            >>> ctx.evaluate("globalThis.data = []; for(let i=0; i<5000; i++) data.push({id:i})")
            >>> # 导出堆快照
            >>> ctx.take_heap_snapshot("heap_snapshot.heapsnapshot")
            >>> # 在 Chrome DevTools 中分析内存使用

            >>> # 内存泄漏检测示例
            >>> ctx.take_heap_snapshot("before.heapsnapshot")
            >>> ctx.evaluate("globalThis.leaked = []; for(let i=0; i<10000; i++) leaked.push({data: new Array(100).fill(i)})")
            >>> ctx.take_heap_snapshot("after.heapsnapshot")
            >>> # 在 Chrome DevTools 中对比两个快照找出泄漏对象
        """
        ...

    def get_hook_data(self) -> Optional[str]:
        """
        获取 Hook 拦截的数据

        当 JavaScript 调用 __saveAndTerminate__() 或 $terminate() 时，
        数据会保存到全局存储中。使用此方法可以在 JS 被终止后获取保存的数据。

        ⚠️ 重要特性：
        - Hook 数据会一直保留，直到被手动清空或被新的 $terminate() 覆盖
        - 可以多次调用 get_hook_data() 读取同一个数据
        - 如果需要执行新的 hook，建议先调用 clear_hook_data() 清空旧数据

        Returns:
            Optional[str]: 如果有保存的数据则返回 JSON 字符串，否则返回 None

        Example:
            >>> import never_jscore
            >>> import json
            >>>
            >>> ctx = never_jscore.Context()
            >>>
            >>> # 第一次拦截
            >>> try:
            ...     ctx.evaluate('$terminate({ n: 1 });')
            ... except:
            ...     pass
            >>> data1 = ctx.get_hook_data()  # {"n": 1}
            >>>
            >>> # 第二次拦截 - 自动清空了第一次的数据
            >>> try:
            ...     ctx.evaluate('$terminate({ n: 2 });')
            ... except:
            ...     pass
            >>> data2 = ctx.get_hook_data()  # {"n": 2} ✅ 正确
            >>>
            >>> # 如果需要保留第一次的数据，必须在第二次执行前保存：
            >>> # saved = ctx.get_hook_data()  # 在下一次 evaluate() 前保存
        """
        ...

    def clear_hook_data(self) -> None:
        """
        清空保存的 Hook 数据

        建议在执行新的 hook 之前调用此方法，以确保不会读到旧的 hook 数据。

        Example:
            >>> ctx = never_jscore.Context()
            >>>
            >>> # 第一次 hook
            >>> try:
            ...     ctx.evaluate('$terminate({ n: 1 });')
            ... except:
            ...     pass
            >>> data1 = ctx.get_hook_data()  # {"n": 1}
            >>>
            >>> # 清空旧数据，准备下一次 hook
            >>> ctx.clear_hook_data()
            >>>
            >>> # 第二次 hook
            >>> try:
            ...     ctx.evaluate('$terminate({ n: 2 });')
            ... except:
            ...     pass
            >>> data2 = ctx.get_hook_data()  # {"n": 2}
        """
        ...


# 类型别名
JSValue = Union[None, bool, int, float, str, List[Any], dict[str, Any]]
"""JavaScript 值的 Python 类型表示"""

__version__: str = "2.5.0"
"""模块版本号"""

__all__ = [
    "Context",
    "JSValue",
]
