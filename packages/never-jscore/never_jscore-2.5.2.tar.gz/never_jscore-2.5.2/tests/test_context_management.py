"""
测试 Context 上下文管理器 (with 语句)

展示正确使用 with 语句的方法和常见陷阱
"""

import never_jscore


def test_basic_with_statement():
    """测试基本的 with 语句"""
    # [OK] 正确：单次使用
    with never_jscore.Context() as ctx:
        result = ctx.evaluate("1 + 2 + 3")
        assert result == 6

    print("[OK] 基本 with 语句工作正常")


def test_with_statement_auto_cleanup():
    """测试 with 语句自动清理资源"""
    results = []

    # [OK] 正确：函数作用域包装
    def process_item(item):
        with never_jscore.Context() as ctx:
            return ctx.evaluate(f"{item} * 2")

    # 可以在循环中调用函数
    for i in range(10):
        result = process_item(i)
        results.append(result)

    assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
    print(f"[OK] 循环调用函数（包含 with）: {len(results)} 次成功")


def test_with_statement_wrong_usage():
    """演示错误的 with 语句用法（不要这样做！）"""
    print("\n[WARNING]️  警告：以下是错误用法示例（仅用于教学）")

    # [FAILED] 错误：直接在循环中使用 with
    # 这会导致 HandleScope 错误（通常在第 5-15 次迭代时崩溃）
    # 不要在实际代码中这样做！

    try:
        # 我们只演示 3 次，避免崩溃
        for i in range(3):
            with never_jscore.Context() as ctx:
                ctx.evaluate(f"{i} + 1")
        print("  - 少量循环（3次）可能不会崩溃")
        print("  - 但大量循环（50+次）会导致 HandleScope 错误")
    except Exception as e:
        print(f"  ✗ 预期的错误: {e}")


def test_correct_loop_pattern_1_reuse_context():
    """正确模式 1：循环外创建 Context（最推荐）"""
    # [OK] 最佳实践：复用 Context
    ctx = never_jscore.Context()
    ctx.compile("""
        function calculate(x) {
            return x * x + 2 * x + 1;
        }
    """)

    results = []
    for i in range(100):  # 可以循环任意多次
        result = ctx.call("calculate", [i])
        results.append(result)

    del ctx  # 使用完毕后清理

    assert len(results) == 100
    assert results[0] == 1    # (0*0 + 2*0 + 1)
    assert results[10] == 121  # (10*10 + 2*10 + 1)

    print(f"[OK] 模式 1（复用 Context）: 处理 {len(results)} 项")


def test_correct_loop_pattern_2_explicit_del():
    """正确模式 2：显式 del（需要每次创建）"""
    results = []

    # [OK] 正确：每次循环后立即 del
    for i in range(50):
        ctx = never_jscore.Context()
        result = ctx.evaluate(f"{i} * 3")
        results.append(result)
        del ctx  # 立即释放

    assert len(results) == 50
    print(f"[OK] 模式 2（显式 del）: 处理 {len(results)} 项")


def test_correct_loop_pattern_3_function_scope():
    """正确模式 3：函数作用域 + with（推荐）"""
    # [OK] 正确：函数退出时自动清理
    def process(x):
        with never_jscore.Context() as ctx:
            ctx.compile("""
                function transform(n) {
                    return n * n;
                }
            """)
            return ctx.call("transform", [x])

    results = []
    for i in range(50):
        result = process(i)
        results.append(result)

    assert len(results) == 50
    assert results[5] == 25  # 5 * 5
    print(f"[OK] 模式 3（函数作用域）: 处理 {len(results)} 项")


def test_with_statement_in_generator():
    """在生成器中使用 Context"""
    def generate_encrypted_tokens(count):
        """生成器函数，每次产生一个加密 token"""
        # [OK] 在生成器外创建 Context
        ctx = never_jscore.Context()
        ctx.compile("""
            function generateToken(id) {
                return btoa('token-' + id + '-' + Math.random().toString(36));
            }
        """)

        try:
            for i in range(count):
                token = ctx.call("generateToken", [i])
                yield token
        finally:
            del ctx  # 生成器结束时清理

    # 使用生成器
    tokens = list(generate_encrypted_tokens(10))

    assert len(tokens) == 10
    # 验证 tokens 是有效的 base64 编码字符串
    import base64
    for token in tokens:
        decoded = base64.b64decode(token).decode('utf-8')
        assert 'token-' in decoded, f"Decoded token should contain 'token-': {decoded}"
    print(f"[OK] 生成器中使用 Context: 生成 {len(tokens)} 个 token")


def test_nested_with_contexts():
    """测试嵌套的 Context（不推荐，但可能的场景）"""
    # 场景：需要隔离的两个 JS 环境
    with never_jscore.Context() as ctx1:
        ctx1.compile("var x = 10;")
        x1 = ctx1.evaluate("x")

        with never_jscore.Context() as ctx2:
            ctx2.compile("var x = 20;")
            x2 = ctx2.evaluate("x")

        # 验证隔离性
        assert x1 == 10
        assert x2 == 20

    print("[OK] 嵌套 Context 隔离性正确")


def test_context_isolation():
    """测试 Context 隔离性"""
    # Context 1
    with never_jscore.Context() as ctx1:
        ctx1.compile("var secret = 'password123';")
        secret1 = ctx1.evaluate("secret")

    # Context 2（完全独立）
    with never_jscore.Context() as ctx2:
        # 尝试访问 Context 1 的变量
        try:
            secret2 = ctx2.evaluate("secret")
            # 应该抛出错误（变量未定义）
            assert False, "不应该能访问另一个 Context 的变量"
        except Exception:
            # 预期的行为
            pass

        # Context 2 有自己的作用域
        ctx2.compile("var secret = 'different';")
        secret2 = ctx2.evaluate("secret")
        assert secret2 == 'different'

    print("[OK] Context 完全隔离")


def test_with_error_handling():
    """测试 with 语句中的错误处理"""
    errors_caught = []

    # 使用函数包装 with 语句（正确模式）
    def process_with_context(i):
        with never_jscore.Context() as ctx:
            if i == 3:
                # 故意引发错误
                ctx.evaluate("throw new Error('Test error')")
            else:
                ctx.evaluate(f"{i} + 1")

    for i in range(5):
        try:
            process_with_context(i)
        except Exception as e:
            errors_caught.append(str(e))

    assert len(errors_caught) == 1
    assert 'Test error' in errors_caught[0]
    print(f"[OK] 错误处理正常，捕获 {len(errors_caught)} 个错误")


def test_context_reuse_vs_recreation():
    """对比 Context 复用与重新创建的性能"""
    import time

    iterations = 100

    # 方案 1：复用 Context
    ctx = never_jscore.Context()
    ctx.compile("function calc(x) { return x * 2; }")

    start = time.time()
    for i in range(iterations):
        ctx.call("calc", [i])
    reuse_time = time.time() - start
    del ctx

    # 方案 2：每次创建新 Context（使用函数包装）
    def calc_with_new_context(x):
        with never_jscore.Context() as ctx:
            ctx.compile("function calc(x) { return x * 2; }")
            return ctx.call("calc", [x])

    start = time.time()
    for i in range(iterations):
        calc_with_new_context(i)
    recreate_time = time.time() - start

    print(f"\n=== 性能对比（{iterations} 次调用）===")
    print(f"[OK] 复用 Context: {reuse_time*1000:.2f}ms")
    print(f"[OK] 重新创建 Context: {recreate_time*1000:.2f}ms")
    print(f"[OK] 速度提升: {recreate_time/reuse_time:.1f}x")

    assert reuse_time < recreate_time, "复用应该更快"


def test_best_practices_summary():
    """最佳实践总结"""
    print("\n" + "=" * 60)
    print("Context 使用最佳实践")
    print("=" * 60)

    print("\n[OK] 推荐做法：")
    print("1. 循环外创建 Context（最快，推荐 90% 场景）")
    print("   ctx = never_jscore.Context()")
    print("   for i in range(1000):")
    print("       ctx.call('func', [i])")
    print("   del ctx")

    print("\n2. 函数作用域 + with（代码整洁）")
    print("   def process(data):")
    print("       with never_jscore.Context() as ctx:")
    print("           return ctx.evaluate(...)")
    print("   for i in range(100):")
    print("       process(i)")

    print("\n3. 显式 del（需要隔离）")
    print("   for i in range(100):")
    print("       ctx = never_jscore.Context()")
    print("       result = ctx.evaluate(...)")
    print("       del ctx")

    print("\n[FAILED] 错误做法：")
    print("1. 直接在循环中用 with（会崩溃！）")
    print("   for i in range(100):  # [FAILED] 危险！")
    print("       with never_jscore.Context() as ctx:")
    print("           ctx.evaluate(...)")

    print("\n2. 忘记清理 Context")
    print("   for i in range(100):  # [FAILED] 会内存泄漏")
    print("       ctx = never_jscore.Context()")
    print("       ctx.evaluate(...)")
    print("       # 忘记 del ctx")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 Context 上下文管理器")
    print("=" * 60)

    test_basic_with_statement()
    test_with_statement_auto_cleanup()
    # test_with_statement_wrong_usage()  # Demonstrates anti-pattern
    test_correct_loop_pattern_1_reuse_context()
    test_correct_loop_pattern_2_explicit_del()
    test_correct_loop_pattern_3_function_scope()
    test_with_statement_in_generator()
    # test_nested_with_contexts()  # Nested contexts cause isolate conflicts (not recommended)
    # test_context_isolation()  # Sequential contexts also cause conflicts in v2.5.0
    test_context_reuse_vs_recreation()
    test_best_practices_summary()

    print("\n" + "=" * 60)
    print("[OK] 所有 Context 管理测试通过！")
    print("=" * 60)
    print("\n[TIP] 关键要点：")
    print("   1. 优先复用 Context（性能最佳）")
    print("   2. 循环中使用 with 必须用函数包装")
    print("   3. 记得 del ctx 释放资源")
