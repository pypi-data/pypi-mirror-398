#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同扩展模式下的内存占用和性能对比

对比三种模式：
1. 纯净模式 (enable_extensions=False)
2. Web API 模式 (默认，enable_extensions=True)
3. Node.js 兼容模式 (enable_node_compat=True)

测试指标：
- 初始化时间
- 初始化后内存占用
- 执行性能
- 内存稳定性
"""

import sys
import io
import time
import gc as python_gc

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import never_jscore


def format_bytes(bytes_val):
    """格式化字节数为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def test_mode(mode_name, create_context_fn, iterations=100):
    """测试单个模式的性能和内存"""
    print(f"\n{'=' * 70}")
    print(f"测试模式: {mode_name}")
    print('=' * 70)

    # 强制 Python GC
    python_gc.collect()
    time.sleep(0.1)

    # 1. 初始化时间测试
    print("\n[1] 初始化性能测试")
    print('-' * 70)

    init_times = []
    for i in range(5):
        start = time.perf_counter()
        ctx = create_context_fn()
        elapsed = (time.perf_counter() - start) * 1000
        init_times.append(elapsed)
        del ctx
        python_gc.collect()
        time.sleep(0.05)

    avg_init_time = sum(init_times) / len(init_times)
    min_init_time = min(init_times)
    max_init_time = max(init_times)

    print(f"  初始化时间 (5次平均): {avg_init_time:.2f} ms")
    print(f"  最快: {min_init_time:.2f} ms | 最慢: {max_init_time:.2f} ms")

    # 2. 初始化后内存占用
    print("\n[2] 初始化后内存占用")
    print('-' * 70)

    ctx = create_context_fn()

    # 等待 V8 稳定
    ctx.evaluate("1 + 1")
    time.sleep(0.1)

    heap_stats = ctx.get_heap_statistics()

    total_heap = heap_stats['total_heap_size']
    used_heap = heap_stats['used_heap_size']
    heap_limit = heap_stats['heap_size_limit']
    external_memory = heap_stats.get('external_memory', 0)

    print(f"  总堆大小:     {format_bytes(total_heap)}")
    print(f"  已使用堆:     {format_bytes(used_heap)}")
    print(f"  外部内存:     {format_bytes(external_memory)}")
    print(f"  堆大小限制:   {format_bytes(heap_limit)}")
    print(f"  使用率:       {used_heap / total_heap * 100:.1f}%")

    # 3. 简单计算性能
    print("\n[3] 简单计算性能 (1000次)")
    print('-' * 70)

    # 预热
    ctx.evaluate("1 + 1")

    start = time.perf_counter()
    for _ in range(1000):
        ctx.evaluate("1 + 2 + 3 + 4 + 5")
    calc_time = (time.perf_counter() - start) * 1000

    print(f"  总耗时: {calc_time:.2f} ms")
    print(f"  平均:   {calc_time / 1000:.4f} ms/次")

    # 4. 字符串操作性能
    print("\n[4] 字符串操作性能 (500次)")
    print('-' * 70)

    string_code = """
    let s = 'hello';
    for(let i=0; i<50; i++) s += 'world';
    s.length
    """

    start = time.perf_counter()
    for _ in range(500):
        ctx.evaluate(string_code)
    string_time = (time.perf_counter() - start) * 1000

    print(f"  总耗时: {string_time:.2f} ms")
    print(f"  平均:   {string_time / 500:.4f} ms/次")

    # 5. 对象操作性能
    print("\n[5] 对象操作性能 (500次)")
    print('-' * 70)

    object_code = """
    const obj = {};
    for(let i=0; i<50; i++) obj['key'+i] = i;
    Object.keys(obj).length
    """

    start = time.perf_counter()
    for _ in range(500):
        ctx.evaluate(object_code)
    object_time = (time.perf_counter() - start) * 1000

    print(f"  总耗时: {object_time:.2f} ms")
    print(f"  平均:   {object_time / 500:.4f} ms/次")

    # 6. 批量执行后的内存变化
    print("\n[6] 批量执行后内存变化")
    print('-' * 70)

    # 执行大量操作
    for _ in range(iterations):
        ctx.evaluate("""
            const arr = [];
            for(let i=0; i<100; i++) arr.push({value: i, data: 'test' + i});
            arr.length
        """)

    heap_stats_after = ctx.get_heap_statistics()

    total_heap_after = heap_stats_after['total_heap_size']
    used_heap_after = heap_stats_after['used_heap_size']

    print(f"  执行前堆大小: {format_bytes(total_heap)}")
    print(f"  执行后堆大小: {format_bytes(total_heap_after)}")
    print(f"  堆增长:       {format_bytes(total_heap_after - total_heap)}")
    print(f"  执行前已用:   {format_bytes(used_heap)}")
    print(f"  执行后已用:   {format_bytes(used_heap_after)}")
    print(f"  内存增长:     {format_bytes(used_heap_after - used_heap)}")

    # 7. GC 效果测试
    print("\n[7] GC 效果测试")
    print('-' * 70)

    print("  执行 GC 前:")
    print(f"    已使用: {format_bytes(used_heap_after)}")

    ctx.gc()
    time.sleep(0.1)

    heap_stats_gc = ctx.get_heap_statistics()
    used_heap_gc = heap_stats_gc['used_heap_size']

    print("  执行 GC 后:")
    print(f"    已使用: {format_bytes(used_heap_gc)}")
    print(f"    回收:   {format_bytes(used_heap_after - used_heap_gc)}")

    del ctx
    python_gc.collect()

    # 返回测试结果
    return {
        'mode': mode_name,
        'avg_init_time': avg_init_time,
        'min_init_time': min_init_time,
        'max_init_time': max_init_time,
        'initial_heap_total': total_heap,
        'initial_heap_used': used_heap,
        'calc_time': calc_time,
        'string_time': string_time,
        'object_time': object_time,
        'heap_growth': total_heap_after - total_heap,
        'memory_growth': used_heap_after - used_heap,
        'gc_freed': used_heap_after - used_heap_gc,
    }


def main():
    print("=" * 70)
    print("never-jscore 扩展模式性能与内存对比测试")
    print("=" * 70)
    print(f"\nPython: {sys.version}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # 测试 1: 纯净模式（无扩展）
    results.append(test_mode(
        "纯净模式 (无扩展)",
        lambda: never_jscore.Context(enable_extensions=False)
    ))

    time.sleep(1)

    # 测试 2: Web API 模式（默认）
    results.append(test_mode(
        "Web API 模式 (默认)",
        lambda: never_jscore.Context(enable_extensions=True)
    ))

    time.sleep(1)

    # 测试 3: Node.js 兼容模式
    results.append(test_mode(
        "Node.js 兼容模式",
        lambda: never_jscore.Context(enable_node_compat=True)
    ))

    # 对比总结
    print("\n" + "=" * 70)
    print("对比总结")
    print("=" * 70)

    print("\n[初始化时间对比]")
    print('-' * 70)
    for r in results:
        print(f"{r['mode']:30s} {r['avg_init_time']:8.2f} ms")

    base_init = results[0]['avg_init_time']
    print(f"\nWeb API 模式相比纯净模式: {results[1]['avg_init_time'] / base_init:.1f}x 慢")
    print(f"Node.js 模式相比纯净模式: {results[2]['avg_init_time'] / base_init:.1f}x 慢")
    print(f"Node.js 模式相比 Web API:  {results[2]['avg_init_time'] / results[1]['avg_init_time']:.1f}x 慢")

    print("\n[初始化后内存占用对比]")
    print('-' * 70)
    for r in results:
        print(f"{r['mode']:30s} {format_bytes(r['initial_heap_used']):>12s}")

    base_mem = results[0]['initial_heap_used']
    print(f"\nWeb API 模式相比纯净模式: +{format_bytes(results[1]['initial_heap_used'] - base_mem)}")
    print(f"Node.js 模式相比纯净模式: +{format_bytes(results[2]['initial_heap_used'] - base_mem)}")
    print(f"Node.js 模式相比 Web API:  +{format_bytes(results[2]['initial_heap_used'] - results[1]['initial_heap_used'])}")

    print("\n[执行性能对比 - 简单计算]")
    print('-' * 70)
    for r in results:
        avg = r['calc_time'] / 1000
        print(f"{r['mode']:30s} {avg:8.4f} ms/次")

    base_calc = results[0]['calc_time']
    diff_web = abs(results[1]['calc_time'] - base_calc) / base_calc * 100
    diff_node = abs(results[2]['calc_time'] - base_calc) / base_calc * 100

    print(f"\nWeb API 模式性能差异: {diff_web:.1f}%")
    print(f"Node.js 模式性能差异: {diff_node:.1f}%")

    print("\n[内存增长对比 (100次批量操作)]")
    print('-' * 70)
    for r in results:
        print(f"{r['mode']:30s} {format_bytes(r['memory_growth']):>12s}")

    print("\n[GC 回收效果对比]")
    print('-' * 70)
    for r in results:
        print(f"{r['mode']:30s} {format_bytes(r['gc_freed']):>12s}")

    print("\n" + "=" * 70)
    print("结论")
    print("=" * 70)

    print("\n1. 初始化开销:")
    print(f"   - 纯净模式最快 ({results[0]['avg_init_time']:.1f} ms)")
    print(f"   - Web API 模式中等 ({results[1]['avg_init_time']:.1f} ms, {results[1]['avg_init_time']/results[0]['avg_init_time']:.1f}x)")
    print(f"   - Node.js 模式最慢 ({results[2]['avg_init_time']:.1f} ms, {results[2]['avg_init_time']/results[0]['avg_init_time']:.1f}x)")

    print("\n2. 内存占用:")
    print(f"   - 纯净模式最小 ({format_bytes(results[0]['initial_heap_used'])})")
    print(f"   - Web API 模式 +{format_bytes(results[1]['initial_heap_used'] - results[0]['initial_heap_used'])}")
    print(f"   - Node.js 模式 +{format_bytes(results[2]['initial_heap_used'] - results[0]['initial_heap_used'])}")

    print("\n3. 运行时性能:")
    print(f"   - 三种模式运行时性能差异在 {max(diff_web, diff_node):.1f}% 以内")
    print("   - 扩展加载仅影响初始化，不影响执行速度")

    print("\n4. 建议:")
    print("   - 如果不需要 Web API: 使用纯净模式 (enable_extensions=False)")
    print("   - 需要 fetch/crypto 等: 使用 Web API 模式 (默认)")
    print("   - 需要 require(): 使用 Node.js 模式 (enable_node_compat=True)")
    print("   - 所有模式都支持 Promise/async/await")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
