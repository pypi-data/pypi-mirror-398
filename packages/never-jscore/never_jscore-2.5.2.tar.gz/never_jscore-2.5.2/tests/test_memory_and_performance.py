"""
测试内存监控和性能调优

展示如何监控内存使用、优化性能和调试问题
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import never_jscore
import time
import gc


def test_basic_memory_monitoring():
    """测试基本内存监控"""
    ctx = never_jscore.Context()

    # 执行一些操作
    for i in range(10):
        ctx.evaluate(f"var x{i} = new Array({i * 1000}).fill({i})")

    # 触发垃圾回收
    ctx.gc()

    print("✓ 手动触发 GC 成功")


def test_context_memory_leak_detection():
    """检测 Context 内存泄漏"""
    import tracemalloc

    # 启动内存跟踪
    tracemalloc.start()

    # 记录初始内存
    snapshot1 = tracemalloc.take_snapshot()

    # 创建并删除 100 个 Context（正确方式）
    for i in range(100):
        ctx = never_jscore.Context()
        ctx.evaluate("1 + 1")
        del ctx  # 正确清理

    # 强制 Python GC
    gc.collect()

    # 记录最终内存
    snapshot2 = tracemalloc.take_snapshot()

    # 计算内存增长
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    total_diff = sum(stat.size_diff for stat in top_stats)

    print(f"✓ 创建并清理 100 个 Context")
    print(f"  - 内存增长: {total_diff / 1024:.2f} KB")

    # 如果正确清理，内存增长应该很小
    assert total_diff < 10 * 1024 * 1024, "内存泄漏检测"

    tracemalloc.stop()


def test_large_data_processing():
    """测试大数据处理"""
    ctx = never_jscore.Context()

    # 创建大数组
    ctx.compile("""
        function createLargeArray(size) {
            const arr = [];
            for (let i = 0; i < size; i++) {
                arr.push({
                    id: i,
                    data: 'x'.repeat(100)
                });
            }
            return arr.length;
        }
    """)

    start = time.time()
    result = ctx.call("createLargeArray", [10000])
    elapsed = time.time() - start

    assert result == 10000

    print(f"✓ 处理大数据（10000 项）")
    print(f"  - 耗时: {elapsed*1000:.2f}ms")

    # 清理内存
    ctx.gc()
    del ctx


def test_batch_processing_with_gc():
    """批量处理 + 定期 GC"""
    ctx = never_jscore.Context()
    ctx.compile("""
        function processItem(item) {
            const result = [];
            for (let i = 0; i < 100; i++) {
                result.push(md5(String(item) + String(i)));
            }
            return result.length;
        }
    """)

    total_processed = 0
    batch_size = 100

    start = time.time()

    for batch in range(10):  # 10 批，每批 100 项
        for i in range(batch_size):
            ctx.call("processItem", [batch * batch_size + i])
            total_processed += 1

        # 每批处理完后触发 GC
        ctx.gc()

    elapsed = time.time() - start

    print(f"✓ 批量处理 + GC")
    print(f"  - 总计: {total_processed} 项")
    print(f"  - 耗时: {elapsed*1000:.2f}ms")
    print(f"  - 平均: {elapsed*1000/total_processed:.3f}ms/项")

    del ctx



def test_get_heap_statistics():
    """测试 V8 堆统计信息"""
    ctx = never_jscore.Context()

    # 创建一些对象占用内存
    ctx.evaluate("""
        const largeArray = [];
        for (let i = 0; i < 10000; i++) {
            largeArray.push({
                id: i,
                data: 'x'.repeat(100),
                nested: { value: i }
            });
        }
    """)

    # 获取堆统计信息
    heap_stats = ctx.get_heap_statistics()

    # 验证统计信息字段
    assert 'total_heap_size' in heap_stats
    assert 'used_heap_size' in heap_stats
    assert 'heap_size_limit' in heap_stats
    assert 'total_physical_size' in heap_stats
    assert 'malloced_memory' in heap_stats
    assert 'external_memory' in heap_stats
    assert 'number_of_native_contexts' in heap_stats

    print(f"\n=== V8 堆统计信息 ===")
    print(f"  总堆大小:       {heap_stats['total_heap_size'] / 1024 / 1024:.2f} MB")
    print(f"  已使用堆:       {heap_stats['used_heap_size'] / 1024 / 1024:.2f} MB")
    print(f"  堆大小限制:     {heap_stats['heap_size_limit'] / 1024 / 1024:.2f} MB")
    print(f"  物理内存大小:   {heap_stats['total_physical_size'] / 1024 / 1024:.2f} MB")
    print(f"  Malloc 内存:    {heap_stats['malloced_memory'] / 1024 / 1024:.2f} MB")
    print(f"  外部内存:       {heap_stats['external_memory'] / 1024:.2f} KB")
    print(f"  Native Context: {heap_stats['number_of_native_contexts']}")
    print(f"  使用率:         {heap_stats['used_heap_size'] / heap_stats['total_heap_size'] * 100:.1f}%")

    del ctx


def test_take_heap_snapshot():
    """测试 V8 堆快照导出"""
    import os

    ctx = never_jscore.Context()

    # 创建一些对象
    ctx.evaluate("""
        globalThis.testObjects = [];
        for (let i = 0; i < 1000; i++) {
            testObjects.push({
                id: i,
                name: `Object_${i}`,
                data: new Array(100).fill(i)
            });
        }
    """)

    # 导出堆快照
    snapshot_file = "heap_snapshot_test.heapsnapshot"

    try:
        ctx.take_heap_snapshot(snapshot_file)

        # 验证文件已创建
        assert os.path.exists(snapshot_file), "快照文件应该被创建"

        # 检查文件大小
        file_size = os.path.getsize(snapshot_file)
        assert file_size > 0, "快照文件不应该为空"

        print(f"\n=== 堆快照导出 ===")
        print(f"  文件名: {snapshot_file}")
        print(f"  大小:   {file_size / 1024:.2f} KB")
        print(f"  ✓ 快照已导出")
        print(f"\n  使用方法:")
        print(f"  1. 打开 Chrome DevTools")
        print(f"  2. 进入 Memory 标签")
        print(f"  3. 点击 'Load' 加载快照文件")
        print(f"  4. 分析内存使用情况")

    finally:
        # 清理测试文件
        if os.path.exists(snapshot_file):
            os.remove(snapshot_file)
        del ctx


def test_heap_snapshot_memory_leak_detection():
    """实战：使用堆快照检测内存泄漏"""
    import os

    ctx = never_jscore.Context()

    # 第一次快照（基准）
    snapshot1 = "snapshot_before.heapsnapshot"
    ctx.take_heap_snapshot(snapshot1)
    heap_before = ctx.get_heap_statistics()

    # 创建大量对象（模拟内存泄漏）
    ctx.evaluate("""
        globalThis.leakedObjects = [];
        for (let i = 0; i < 5000; i++) {
            leakedObjects.push({
                id: i,
                data: new Array(200).fill(i),
                circular: null
            });
        }
        // 创建循环引用
        leakedObjects.forEach((obj, i) => {
            obj.circular = leakedObjects[(i + 1) % leakedObjects.length];
        });
    """)

    # 第二次快照（泄漏后）
    snapshot2 = "snapshot_after.heapsnapshot"
    ctx.take_heap_snapshot(snapshot2)
    heap_after = ctx.get_heap_statistics()

    # 分析内存增长
    memory_growth = heap_after['used_heap_size'] - heap_before['used_heap_size']

    print(f"\n=== 内存泄漏检测 ===")
    print(f"  前: {heap_before['used_heap_size'] / 1024 / 1024:.2f} MB")
    print(f"  后: {heap_after['used_heap_size'] / 1024 / 1024:.2f} MB")
    print(f"  增长: {memory_growth / 1024 / 1024:.2f} MB")
    print(f"\n  快照对比:")
    print(f"  1. {snapshot1} ({os.path.getsize(snapshot1) / 1024:.2f} KB)")
    print(f"  2. {snapshot2} ({os.path.getsize(snapshot2) / 1024:.2f} KB)")
    print(f"\n  分析步骤:")
    print(f"  1. 在 Chrome DevTools 中加载两个快照")
    print(f"  2. 使用 'Comparison' 视图对比")
    print(f"  3. 查找 'leakedObjects' 相关对象")
    print(f"  4. 分析循环引用链")

    # 清理
    try:
        os.remove(snapshot1)
        os.remove(snapshot2)
    except:
        pass

    del ctx


def test_heap_statistics_monitoring():
    """实战：监控批量处理的内存使用"""
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

        function heavyComputation(n) {
            const temp = [];
            for (let i = 0; i < n; i++) {
                temp.push(simpleHash(String(i)));
            }
            return temp.length;
        }
    """)

    print(f"\n=== 批量处理内存监控 ===")

    batches = 5
    batch_size = 500

    for batch in range(batches):
        # 处理前统计
        before = ctx.get_heap_statistics()

        # 执行批量处理
        ctx.call("heavyComputation", [batch_size])

        # 处理后统计
        after = ctx.get_heap_statistics()

        growth = after['used_heap_size'] - before['used_heap_size']

        print(f"  批次 {batch + 1}:")
        print(f"    使用: {after['used_heap_size'] / 1024 / 1024:.2f} MB")
        print(f"    增长: {growth / 1024:.2f} KB")

        # 每 2 批触发 GC
        if batch % 2 == 1:
            ctx.gc()
            gc_after = ctx.get_heap_statistics()
            freed = after['used_heap_size'] - gc_after['used_heap_size']
            print(f"    GC 释放: {freed / 1024:.2f} KB")

    del ctx


def test_performance_profiling():
    """性能分析"""
    ctx = never_jscore.Context()

    # 测试不同操作的性能
    operations = {
        "简单计算": lambda: ctx.evaluate("1 + 1"),
        "字符串操作": lambda: ctx.evaluate("'hello'.toUpperCase()"),
        "数组操作": lambda: ctx.evaluate("[1,2,3,4,5].map(x => x * 2)"),
        "对象操作": lambda: ctx.evaluate("({a: 1, b: 2, c: 3})"),
        "MD5 哈希": lambda: ctx.evaluate("md5('hello')"),
        "Base64 编码": lambda: ctx.evaluate("btoa('hello')"),
    }

    print(f"\n=== 性能分析（各操作 1000 次）===")

    for name, operation in operations.items():
        start = time.time()
        for _ in range(1000):
            operation()
        elapsed = time.time() - start

        print(f"  {name:12} {elapsed*1000:7.2f}ms ({elapsed*1000000/1000:6.2f}μs/次)")

    del ctx


def test_context_creation_overhead():
    """测试 Context 创建开销"""
    iterations = 50

    # 测试创建 + 删除的开销
    start = time.time()
    for _ in range(iterations):
        ctx = never_jscore.Context()
        del ctx
    create_time = time.time() - start

    # 测试复用的性能
    ctx = never_jscore.Context()
    start = time.time()
    for _ in range(iterations):
        ctx.evaluate("1 + 1")
    reuse_time = time.time() - start
    del ctx

    print(f"\n=== Context 开销分析（{iterations} 次）===")
    print(f"  创建+删除: {create_time*1000:.2f}ms ({create_time*1000/iterations:.2f}ms/次)")
    print(f"  复用执行:  {reuse_time*1000:.2f}ms ({reuse_time*1000/iterations:.2f}ms/次)")
    print(f"  速度提升:  {create_time/reuse_time:.1f}x")


def test_enable_logging():
    """测试启用日志调试"""
    print(f"\n=== 启用调试日志 ===")

    # 创建带日志的 Context
    ctx = never_jscore.Context(enable_logging=True)

    print("  执行操作（会输出 Rust 日志）:")
    ctx.evaluate("console.log('Hello from JS')")
    ctx.compile("function add(a, b) { return a + b; }")
    ctx.call("add", [1, 2])

    del ctx

    print("✓ 日志功能正常")


def test_memory_efficient_large_dataset():
    """内存高效的大数据集处理"""
    def process_chunk(chunk_id, chunk_size):
        """处理单个数据块"""
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

            function processData(start, count) {
                const results = [];
                for (let i = start; i < start + count; i++) {
                    results.push(simpleHash(String(i)));
                }
                return results.length;
            }
        """)

        result = ctx.call("processData", [chunk_id * chunk_size, chunk_size])
        del ctx  # 立即释放
        return result

    # 处理 10 个块，每块 100 项
    chunks = 10
    chunk_size = 100
    total = 0

    start = time.time()

    for i in range(chunks):
        processed = process_chunk(i, chunk_size)
        total += processed

        # 强制 Python GC
        if i % 3 == 0:
            gc.collect()

    elapsed = time.time() - start

    print(f"\n=== 内存高效处理 ===")
    print(f"  处理: {total} 项")
    print(f"  耗时: {elapsed*1000:.2f}ms")
    print(f"  策略: 分块处理 + 即时释放 Context")


if __name__ == "__main__":
    print("=" * 60)
    print("测试内存监控和性能调优")
    print("=" * 60)

    test_get_heap_statistics()
    test_take_heap_snapshot()
    test_heap_snapshot_memory_leak_detection()
    test_heap_statistics_monitoring()
    test_memory_efficient_large_dataset()

    print("\n" + "=" * 60)
    print("✅ 所有内存和性能测试通过！")
    print("=" * 60)
    print("\n💡 关键要点：")
    print("   1. 使用 get_heap_statistics() 监控 V8 堆内存")
    print("   2. 使用 take_heap_snapshot() 导出快照到 Chrome DevTools")
    print("   3. 定期调用 ctx.gc() 清理内存")
    print("   4. 优先复用 Context 而不是重复创建")
    print("   5. 使用 ThreadPoolExecutor 进行并行处理")
    print("   6. 启用日志 (enable_logging=True) 进行调试")
