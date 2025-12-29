"""
测试增强的 Hook 拦截功能 - V8 terminate_execution

展示 never_jscore v2.5.0 的新扩展架构 Hook API:
- $terminate() - 新推荐的 API (更简洁)
- __saveAndTerminate__() - 向后兼容的 API

两者都使用 V8 的 terminate_execution() 实现无法被 try-catch 捕获的 Hook 拦截。
基于新的 Hook Extension (src/ext/hook/)
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import never_jscore
import json


def test_basic_terminate_new_api():
    """测试新的 $terminate() API (v2.5.0+)"""
    print("\n" + "=" * 60)
    print("测试 1: 新的 $terminate() API (推荐)")
    print("=" * 60)

    ctx = never_jscore.Context()
    ctx.clear_hook_data()  # 清空之前的数据

    # 简单测试：使用新的 $terminate API
    try:
        ctx.evaluate('''
            const data = {
                message: "Hello from JS",
                timestamp: Date.now(),
                value: 42
            };
            $terminate(data);  // ⭐ 新的简洁 API

            // ❌ 下面的代码不会执行（被 terminate 阻止）
            console.log("This should not print");
        ''')
        print("❌ JS 正常结束（不应该发生）")
    except Exception as e:
        print(f"✅ JS 被 terminate 终止: {type(e).__name__}")

    # 获取保存的数据
    hook_data = ctx.get_hook_data()
    if hook_data:
        data = json.loads(hook_data)
        print(f"✅ 成功获取保存的数据:")
        print(f"   - message: {data['message']}")
        print(f"   - value: {data['value']}")
        assert data['message'] == "Hello from JS"
        assert data['value'] == 42
    else:
        print("❌ 没有获取到数据")


def test_basic_save_and_terminate():
    """测试旧的 __saveAndTerminate__ API (向后兼容)"""
    print("\n" + "=" * 60)
    print("测试 2: 旧的 __saveAndTerminate__ API (向后兼容)")
    print("=" * 60)

    ctx = never_jscore.Context()
    ctx.clear_hook_data()  # 清空之前的数据

    # 简单测试：直接调用 __saveAndTerminate__
    try:
        ctx.evaluate('''
            const data = {
                message: "Legacy API",
                timestamp: Date.now(),
                value: 99
            };
            __saveAndTerminate__(data);  // 旧 API

            // ❌ 下面的代码不会执行（被 terminate 阻止）
            console.log("This should not print");
        ''')
        print("❌ JS 正常结束（不应该发生）")
    except Exception as e:
        print(f"✅ JS 被 terminate 终止: {type(e).__name__}")

    # 获取保存的数据
    hook_data = ctx.get_hook_data()
    if hook_data:
        data = json.loads(hook_data)
        print(f"✅ 成功获取保存的数据:")
        print(f"   - message: {data['message']}")
        print(f"   - value: {data['value']}")
        assert data['message'] == "Legacy API"
        assert data['value'] == 99
    else:
        print("❌ 没有获取到数据")


def test_hook_xhr_with_terminate():
    """测试 Hook XMLHttpRequest.send 使用 $terminate"""
    print("\n" + "=" * 60)
    print("测试 3: Hook XMLHttpRequest.send (使用新 $terminate API)")
    print("=" * 60)

    ctx = never_jscore.Context()
    ctx.clear_hook_data()

    # 1. 注入 Hook
    hook_code = '''
        XMLHttpRequest.prototype.send = function(body) {
            console.log("🎯 Hook 触发! 拦截到 XHR 请求");

            // 构造要保存的数据
            const hookData = {
                type: "xhr_send",
                url: this._url || "unknown",
                method: this._method || "unknown",
                body: body,
                timestamp: Date.now()
            };

            // ✅ 使用新的 $terminate API 保存并终止
            $terminate(hookData);  // ⭐ 新 API，更简洁

            // ⚠️ 下面的代码永远不会执行
            console.log("这行不会输出");
        };

        console.log("✅ Hook 已注入");
    '''
    ctx.compile(hook_code)

    # 2. 执行目标 JS（会触发 Hook）
    target_js = '''
        console.log("开始执行目标 JS...");

        function generateSign(data) {
            // 模拟加密算法
            return "sign_" + btoa(data) + "_encrypted";
        }

        function sendEncryptedRequest() {
            try {
                const data = "sensitive_user_data_12345";
                const sign = generateSign(data);

                console.log("生成的签名:", sign);

                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/api/secure-endpoint');
                xhr.setRequestHeader('Content-Type', 'application/json');

                // 这里会触发 Hook
                xhr.send(JSON.stringify({
                    data: data,
                    sign: sign
                }));

                // ❌ 下面的代码不会执行
                console.log("❌ 请求发送成功 (不会看到)");
                return "success";

            } catch (e) {
                // ❌ try-catch 无法捕获 terminate
                console.log("❌ 捕获到错误 (不会进入):", e.message);
                return "error_caught";
            }
        }

        const result = sendEncryptedRequest();
        console.log("❌ 函数返回值 (不会看到):", result);
    '''

    for i in range(2):
        try:
            ctx.evaluate(target_js)
            print("❌ JS 正常结束（不应该发生）")
        except Exception as e:
            print(f"✅ JS 被 terminate 终止: {type(e).__name__}")
            print(f"   错误消息: {str(e)[:100]}...")

        # 3. 获取 Hook 拦截的数据
        hook_data = ctx.get_hook_data()
        if hook_data:
            data = json.loads(hook_data)
            print(f"\n✅ 成功获取拦截数据:")
            print(f"   - 类型: {data['type']}")
            print(f"   - URL: {data['url']}")
            print(f"   - 方法: {data['method']}")

            # 解析 body
            body_obj = json.loads(data['body'])
            print(f"   - Body:")
            print(f"     - data: {body_obj['data']}")
            print(f"     - sign: {body_obj['sign']}")

            assert data['type'] == 'xhr_send'
            assert data['url'] == '/api/secure-endpoint'
        else:
            print("❌ 没有获取到数据")


def test_bypass_try_catch():
    """测试 __saveAndTerminate__ 可以绕过 try-catch"""
    print("\n" + "=" * 60)
    print("测试 3: 绕过 try-catch (关键特性!)")
    print("=" * 60)

    ctx = never_jscore.Context()
    ctx.clear_hook_data()

    code = '''
        try {
            console.log("进入 try 块");

            // 调用 __saveAndTerminate__
            __saveAndTerminate__({
                message: "Escaped from try-catch!",
                success: true
            });

            // ❌ 下面的代码不会执行
            console.log("❌ 这行不会输出");

        } catch (e) {
            // ❌ try-catch 无法捕获 terminate
            console.log("❌ catch 块不会执行:", e.message);
        } finally {
            // ❌ finally 也不会执行（V8 terminate 会跳过）
            console.log("❌ finally 块不会执行");
        }

        console.log("❌ try-catch 外部的代码也不会执行");
    '''

    try:
        ctx.evaluate(code)
        print("❌ JS 正常结束（不应该发生）")
    except Exception as e:
        print(f"✅ JS 被 terminate 终止，try-catch 无法捕获!")
        print(f"   异常类型: {type(e).__name__}")

    hook_data = ctx.get_hook_data()
    if hook_data:
        data = json.loads(hook_data)
        print(f"✅ 成功逃离 try-catch 并获取数据:")
        print(f"   - message: {data['message']}")
        print(f"   - success: {data['success']}")
        assert data['message'] == "Escaped from try-catch!"
    else:
        print("❌ 没有获取到数据")


def test_short_alias():
    """测试简短别名 $terminate"""
    print("\n" + "=" * 60)
    print("测试 4: 简短别名 $terminate")
    print("=" * 60)

    ctx = never_jscore.Context()
    ctx.clear_hook_data()

    try:
        ctx.evaluate('''
            // 使用简短别名 $terminate
            $terminate({
                alias: "$terminate",
                working: true
            });
        ''')
    except Exception as e:
        print(f"✅ JS 被终止: {type(e).__name__}")

    hook_data = ctx.get_hook_data()
    if hook_data:
        data = json.loads(hook_data)
        print(f"✅ $terminate 别名工作正常:")
        print(f"   - alias: {data['alias']}")
        print(f"   - working: {data['working']}")
        assert data['alias'] == "$terminate"
    else:
        print("❌ 没有获取到数据")


def test_comparison_with_return():
    """测试 $return vs __saveAndTerminate__ 的区别"""
    print("\n" + "=" * 60)
    print("测试 5: $return vs __saveAndTerminate__ 对比")
    print("=" * 60)

    # 测试 $return (可以被 try-catch 捕获)
    print("\n--- 5.1: $return (可以被 try-catch 捕获) ---")
    ctx1 = never_jscore.Context()

    result1 = ctx1.evaluate('''
        try {
            $return({ from: "$return", value: 100 });
            "not reached";
        } catch (e) {
            // ✅ try-catch 可以捕获 $return 的错误
            "caught_by_try_catch";
        }
    ''')
    print(f"✅ $return 被 try-catch 捕获，返回: {result1}")

    # 测试 __saveAndTerminate__ (无法被 try-catch 捕获)
    print("\n--- 5.2: __saveAndTerminate__ (无法被 try-catch 捕获) ---")
    ctx2 = never_jscore.Context()
    ctx2.clear_hook_data()

    try:
        ctx2.evaluate('''
            try {
                __saveAndTerminate__({ from: "__saveAndTerminate__", value: 200 });
                "not reached";
            } catch (e) {
                // ❌ try-catch 无法捕获 terminate
                "should_not_reach_here";
            }
        ''')
        print("❌ __saveAndTerminate__ 没有终止（不应该发生）")
    except Exception as e:
        print(f"✅ __saveAndTerminate__ 终止了 JS，try-catch 无法捕获")

    hook_data = ctx2.get_hook_data()
    if hook_data:
        data = json.loads(hook_data)
        print(f"✅ 数据已保存: from={data['from']}, value={data['value']}")


def test_multiple_contexts():
    """测试多个 Context 的 Hook 数据隔离"""
    print("\n" + "=" * 60)
    print("测试 6: 多个 Context 的数据隔离")
    print("=" * 60)

    ctx1 = never_jscore.Context()
    ctx2 = never_jscore.Context()

    # Context 1 保存数据
    ctx1.clear_hook_data()
    try:
        ctx1.evaluate('__saveAndTerminate__({ context: "ctx1", value: 111 });')
    except:
        pass

    data1 = ctx1.get_hook_data()
    print(f"Context 1 数据: {json.loads(data1) if data1 else None}")

    # Context 2 保存数据（会覆盖全局数据）
    ctx2.clear_hook_data()
    try:
        ctx2.evaluate('__saveAndTerminate__({ context: "ctx2", value: 222 });')
    except:
        pass

    data2 = ctx2.get_hook_data()
    print(f"Context 2 数据: {json.loads(data2) if data2 else None}")

    # 注意：由于使用全局存储，Context 2 会覆盖 Context 1 的数据
    print("\n⚠️ 注意: Hook 数据使用全局存储，后执行的 Context 会覆盖之前的数据")
    print("   建议：在单个 Context 内完成 Hook -> 执行 -> 获取数据 的流程")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("V8 terminate_execution Hook 拦截测试套件")
    print("=" * 60)

    tests = [
        # ("基本功能", test_basic_save_and_terminate),
        # ("Hook XHR", test_hook_xhr_with_terminate),
        ("绕过 try-catch", test_bypass_try_catch),
        # ("简短别名", test_short_alias),
        # ("对比 $return", test_comparison_with_return),
        # ("多 Context 隔离", test_multiple_contexts),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ [{name}] 测试通过\n")
        except Exception as e:
            failed += 1
            print(f"❌ [{name}] 测试失败: {e}\n")

    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败")


    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
