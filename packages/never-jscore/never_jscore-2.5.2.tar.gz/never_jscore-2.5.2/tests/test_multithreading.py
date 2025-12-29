"""
测试多线程使用

展示如何在多线程环境中安全使用 never-jscore
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import never_jscore
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def test_basic_multithreading():
    """测试基本的多线程使用"""
    results = []
    lock = threading.Lock()

    def worker(thread_id):
        # ✅ 每个线程创建自己的 Context
        ctx = never_jscore.Context()
        ctx.compile(f"""
            function process(x) {{
                return x * {thread_id};
            }}
        """)

        result = ctx.call("process", [10])
        del ctx

        with lock:
            results.append((thread_id, result))

    # 创建 4 个线程
    threads = []
    for i in range(1, 5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    assert len(results) == 4
    print(f"✓ 基本多线程: {len(results)} 个线程成功执行")


def test_threadpoolexecutor():
    """测试使用 ThreadPoolExecutor"""
    def process_item(item_id):
        # 每个任务创建独立的 Context
        ctx = never_jscore.Context()
        ctx.compile("""
            function encrypt(data) {
                return btoa(JSON.stringify(data));
            }
        """)

        result = ctx.call("encrypt", [{"id": item_id, "value": item_id * 2}])
        del ctx
        return (item_id, result)

    # 使用 4 个线程处理 20 个任务
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_item, i) for i in range(20)]

        results = []
        for future in as_completed(futures):
            results.append(future.result())

    assert len(results) == 20
    print(f"✓ ThreadPoolExecutor: 处理 {len(results)} 个任务")


def test_threadlocal_context():
    """测试使用 ThreadLocal 复用 Context（推荐模式）"""
    thread_local = threading.local()

    def get_context():
        """获取线程本地的 Context（每线程一个，可复用）"""
        if not hasattr(thread_local, 'ctx'):
            thread_local.ctx = never_jscore.Context()
            thread_local.ctx.compile("""
                function simpleHash(str) {
                    let hash = 0;
                    for (let i = 0; i < str.length; i++) {
                        hash = ((hash << 5) - hash) + str.charCodeAt(i);
                        hash = hash & hash;
                    }
                    return Math.abs(hash).toString(16).padStart(8, '0');
                }

                function hash(data) {
                    return simpleHash(String(data));
                }
            """)
        return thread_local.ctx

    def worker(items):
        """处理一批数据"""
        ctx = get_context()  # 获取线程本地 Context
        results = []

        for item in items:
            result = ctx.call("hash", [item])
            results.append(result)

        return results

    # 准备数据（每个线程处理 25 个）
    data_chunks = [
        list(range(0, 25)),
        list(range(25, 50)),
        list(range(50, 75)),
        list(range(75, 100))
    ]

    # 使用 4 个线程并行处理
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker, chunk) for chunk in data_chunks]

        all_results = []
        for future in as_completed(futures):
            all_results.extend(future.result())

    assert len(all_results) == 100
    print(f"✓ ThreadLocal 复用: 处理 {len(all_results)} 项（4 个线程）")


def test_performance_comparison():
    """性能对比：单线程 vs 多线程"""
    def process_with_context(item_id):
        ctx = never_jscore.Context()
        ctx.compile("""
            function calculate(x) {
                let sum = 0;
                for (let i = 0; i < 100; i++) {
                    sum += Math.sqrt(x * i);
                }
                return sum;
            }
        """)
        result = ctx.call("calculate", [item_id])
        del ctx
        return result

    iterations = 50

    # 单线程
    start = time.time()
    results_single = [process_with_context(i) for i in range(iterations)]
    single_time = time.time() - start

    # 多线程（4 个线程）
    start = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        results_multi = list(executor.map(process_with_context, range(iterations)))
    multi_time = time.time() - start

    print(f"\n=== 性能对比（{iterations} 次计算）===")
    print(f"✓ 单线程: {single_time*1000:.2f}ms")
    print(f"✓ 多线程（4核）: {multi_time*1000:.2f}ms")
    print(f"✓ 速度提升: {single_time/multi_time:.2f}x")

    assert len(results_single) == iterations
    assert len(results_multi) == iterations


def test_thread_safety_isolation():
    """测试线程隔离性"""
    results = {}
    lock = threading.Lock()

    def worker(thread_id):
        # 每个线程有自己的 Context 和变量
        ctx = never_jscore.Context()
        ctx.compile(f"var threadVar = {thread_id * 100};")

        # 读取自己的变量
        value = ctx.evaluate("threadVar")
        del ctx

        with lock:
            results[thread_id] = value

    # 启动多个线程
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 验证每个线程的值是独立的
    assert results[0] == 0
    assert results[1] == 100
    assert results[2] == 200
    assert results[3] == 300
    assert results[4] == 400

    print(f"✓ 线程隔离性: {len(results)} 个线程互不干扰")


def test_concurrent_encryption():
    """实战场景：并发加密多个数据"""
    # 准备要加密的数据
    sensitive_data = [
        {"user": f"user{i}", "token": f"token-{i}"}
        for i in range(50)
    ]

    def encrypt_data(data):
        ctx = never_jscore.Context()
        ctx.compile("""
            function simpleHash(str) {
                let hash = 0;
                for (let i = 0; i < str.length; i++) {
                    hash = ((hash << 5) - hash) + str.charCodeAt(i);
                    hash = hash & hash;
                }
                return Math.abs(hash).toString(16).padStart(8, '0');
            }

            function secureEncrypt(obj) {
                const json = JSON.stringify(obj);
                const hash = simpleHash(json);
                const encrypted = btoa(json + ':' + hash);
                return {
                    data: encrypted,
                    hash: hash,
                    timestamp: Date.now()
                };
            }
        """)

        result = ctx.call("secureEncrypt", [data])
        del ctx
        return result

    # 使用 8 个线程并发加密
    start = time.time()
    with ThreadPoolExecutor(max_workers=8) as executor:
        encrypted_results = list(executor.map(encrypt_data, sensitive_data))
    elapsed = time.time() - start

    assert len(encrypted_results) == 50
    assert all('hash' in r for r in encrypted_results)

    print(f"\n=== 并发加密场景 ===")
    print(f"✓ 加密 {len(encrypted_results)} 条数据")
    print(f"✓ 耗时: {elapsed*1000:.2f}ms")
    print(f"✓ 平均: {elapsed*1000/len(encrypted_results):.2f}ms/条")


def test_thread_pool_with_reused_contexts():
    """使用线程池 + Context 复用（最佳性能）"""
    thread_local = threading.local()

    def get_or_create_context():
        if not hasattr(thread_local, 'ctx'):
            thread_local.ctx = never_jscore.Context()
            thread_local.ctx.compile("""
                function simpleHash(str) {
                    let hash = 0;
                    for (let i = 0; i < str.length; i++) {
                        hash = ((hash << 5) - hash) + str.charCodeAt(i);
                        hash = hash & hash;
                    }
                    return Math.abs(hash).toString(16).padStart(8, '0');
                }

                function sign(data, secret) {
                    return simpleHash(data + secret);
                }
            """)
        return thread_local.ctx

    def process_batch(batch):
        """处理一批数据（复用 Context）"""
        ctx = get_or_create_context()
        results = []

        for item in batch:
            signature = ctx.call("sign", [item, "SECRET_KEY"])
            results.append({"data": item, "signature": signature})

        return results

    # 将 100 个任务分成 10 批
    batches = [list(range(i*10, (i+1)*10)) for i in range(10)]

    # 使用 4 个线程处理（每个线程复用 Context）
    start = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_batch, batch) for batch in batches]

        all_results = []
        for future in as_completed(futures):
            all_results.extend(future.result())

    elapsed = time.time() - start

    assert len(all_results) == 100

    print(f"\n=== Context 复用优化 ===")
    print(f"✓ 处理 {len(all_results)} 项")
    print(f"✓ 耗时: {elapsed*1000:.2f}ms")
    print(f"✓ 4 个线程，每个线程复用 1 个 Context")


def test_error_handling_in_threads():
    """测试多线程中的错误处理"""
    def worker_with_error(item_id):
        ctx = never_jscore.Context()

        try:
            if item_id == 5:
                # 故意引发错误
                ctx.evaluate("throw new Error('Test error in thread')")
            else:
                result = ctx.evaluate(f"{item_id} * 2")
                return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e), "item": item_id}
        finally:
            del ctx

    # 处理 10 个任务（其中一个会出错）
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(worker_with_error, range(10)))

    errors = [r for r in results if not r.get('success')]
    successes = [r for r in results if r.get('success')]

    assert len(errors) == 1
    assert errors[0]['item'] == 5
    assert len(successes) == 9

    print(f"✓ 错误处理: {len(successes)} 成功, {len(errors)} 失败（符合预期）")


def test_best_practices_summary():
    """多线程最佳实践总结"""
    print("\n" + "=" * 60)
    print("多线程使用最佳实践")
    print("=" * 60)

    print("\n✅ 推荐做法：")
    print("1. ThreadLocal + Context 复用（最佳性能）")
    print("   thread_local = threading.local()")
    print("   def get_context():")
    print("       if not hasattr(thread_local, 'ctx'):")
    print("           thread_local.ctx = never_jscore.Context()")
    print("       return thread_local.ctx")

    print("\n2. 每个任务创建独立 Context（隔离性强）")
    print("   def worker(data):")
    print("       ctx = never_jscore.Context()")
    print("       result = ctx.call('func', [data])")
    print("       del ctx  # 记得清理")
    print("       return result")

    print("\n3. 使用 ThreadPoolExecutor（推荐）")
    print("   with ThreadPoolExecutor(max_workers=4) as executor:")
    print("       results = executor.map(worker, data_list)")

    print("\n❌ 错误做法：")
    print("1. 跨线程共享 Context（会崩溃！）")
    print("   ctx = never_jscore.Context()  # ❌ 全局 Context")
    print("   def worker():")
    print("       ctx.evaluate(...)  # ❌ 多个线程使用同一个 Context")

    print("\n2. 忘记清理 Context")
    print("   def worker():")
    print("       ctx = never_jscore.Context()")
    print("       return ctx.evaluate(...)")
    print("       # ❌ 忘记 del ctx，会内存泄漏")


if __name__ == "__main__":
    print("=" * 60)
    print("测试多线程使用")
    print("=" * 60)

    test_basic_multithreading()
    test_threadpoolexecutor()
    test_threadlocal_context()
    test_performance_comparison()
    test_thread_safety_isolation()
    test_concurrent_encryption()
    test_thread_pool_with_reused_contexts()
    test_error_handling_in_threads()
    test_best_practices_summary()

    print("\n" + "=" * 60)
    print("✅ 所有多线程测试通过！")
    print("=" * 60)
    print("\n💡 关键要点：")
    print("   1. Context 不是线程安全的，不能跨线程共享")
    print("   2. 每个线程创建自己的 Context")
    print("   3. 使用 ThreadLocal 可以在同一线程内复用 Context")
    print("   4. ThreadPoolExecutor 是推荐的并发模式")
