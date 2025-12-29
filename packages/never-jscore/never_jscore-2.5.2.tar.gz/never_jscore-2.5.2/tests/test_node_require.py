#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Node.js require() 功能
"""

import sys
import io

# Set stdout to use UTF-8 encoding to avoid GBK encoding errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import never_jscore
import os
import sys
import tempfile
import json

def test_basic_require():
    """测试基础 require() 功能"""
    print("\n=== Test 1: Basic require() availability ===")

    ctx = never_jscore.Context(enable_node_compat=True)

    # 检查 require 是否存在
    result = ctx.evaluate("typeof require")
    print(f"typeof require: {result}")
    assert result == "function", "require should be a function"

    # 检查 module 是否存在
    result = ctx.evaluate("typeof module")
    print(f"typeof module: {result}")
    assert result == "object", "module should be an object"


    print("✓ Basic require() infrastructure is available")


def test_require_json():
    """测试 require() 加载 JSON 文件"""
    print("\n=== Test 2: Require JSON file ===")

    # 创建临时目录和 JSON 文件
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个 JSON 文件
        json_file = os.path.join(tmpdir, "test.json")
        test_data = {"name": "test-package", "version": "1.0.0", "value": 42}
        with open(json_file, "w") as f:
            json.dump(test_data, f)

        ctx = never_jscore.Context(enable_node_compat=True)

        # 尝试 require JSON 文件
        code = f"""
        const data = require('{json_file.replace(chr(92), '/')}');
        data;
        """

        result = ctx.evaluate(code)
        print(f"Loaded JSON: {result}")

        assert result["name"] == "test-package"
        assert result["version"] == "1.0.0"
        assert result["value"] == 42

        print("✓ JSON file require() works")


def test_require_js_module():
    """测试 require() 加载 JavaScript 模块"""
    print("\n=== Test 3: Require JavaScript module ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个简单的 JS 模块
        module_file = os.path.join(tmpdir, "math.js")
        with open(module_file, "w") as f:
            f.write("""
                exports.add = function(a, b) {
                    return a + b;
                };

                exports.multiply = function(a, b) {
                    return a * b;
                };

                exports.PI = 3.14159;
            """)

        ctx = never_jscore.Context(enable_node_compat=True)

        # Require 这个模块
        code = f"""
        const math = require('{module_file.replace(chr(92), '/')}');
        ({{
            add: math.add(10, 20),
            multiply: math.multiply(5, 6),
            PI: math.PI
        }})
        """

        result = ctx.evaluate(code)
        print(f"Module functions: {result}")

        assert result["add"] == 30
        assert result["multiply"] == 30
        assert result["PI"] == 3.14159

        print("✓ JavaScript module require() works")


def test_require_cache():
    """测试 require() 缓存机制"""
    print("\n=== Test 4: Require cache ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个带计数器的模块
        module_file = os.path.join(tmpdir, "counter.js")
        with open(module_file, "w") as f:
            f.write("""
                let count = 0;
                exports.getCount = function() {
                    return ++count;
                };
            """)

        ctx = never_jscore.Context(enable_node_compat=True)

        # 多次 require 同一个模块
        code = f"""
        const counter1 = require('{module_file.replace(chr(92), '/')}');
        const counter2 = require('{module_file.replace(chr(92), '/')}');

        ({{
            first: counter1.getCount(),
            second: counter1.getCount(),
            third: counter2.getCount(),
            sameObject: counter1 === counter2
        }})
        """

        result = ctx.evaluate(code)
        print(f"Cache test: {result}")

        # 由于缓存，counter1 和 counter2 是同一个对象
        assert result["sameObject"] == True
        # 计数器应该是连续的
        assert result["first"] == 1
        assert result["second"] == 2
        assert result["third"] == 3

        print("✓ require() cache works correctly")


def test_module_exports_pattern():
    """测试 module.exports 模式"""
    print("\n=== Test 5: module.exports pattern ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个使用 module.exports 的模块
        module_file = os.path.join(tmpdir, "calculator.js")
        with open(module_file, "w") as f:
            f.write("""
                module.exports = function Calculator() {
                    this.add = function(a, b) {
                        return a + b;
                    };

                    this.subtract = function(a, b) {
                        return a - b;
                    };
                };
            """)

        ctx = never_jscore.Context(enable_node_compat=True)

        # 使用构造函数模式
        code = f"""
        const Calculator = require('{module_file.replace(chr(92), '/')}');
        const calc = new Calculator();

        ({{
            add: calc.add(100, 50),
            subtract: calc.subtract(100, 50)
        }})
        """

        result = ctx.evaluate(code)
        print(f"Calculator: {result}")

        assert result["add"] == 150
        assert result["subtract"] == 50

        print("✓ module.exports pattern works")


def test_relative_require():
    """测试相对路径 require()"""
    print("\n=== Test 6: Relative path require() ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建目录结构
        subdir = os.path.join(tmpdir, "lib")
        os.makedirs(subdir)

        # 创建被依赖的模块
        util_file = os.path.join(subdir, "util.js")
        with open(util_file, "w") as f:
            f.write("""
                exports.formatName = function(first, last) {
                    return first + ' ' + last;
                };
            """)

        # 创建主模块，require 相对路径
        main_file = os.path.join(tmpdir, "main.js")
        with open(main_file, "w") as f:
            f.write("""
                const util = require('./lib/util.js');

                module.exports = {
                    greet: function(first, last) {
                        return 'Hello, ' + util.formatName(first, last);
                    }
                };
            """)

        ctx = never_jscore.Context(enable_node_compat=True)

        # Require 主模块
        code = f"""
        const main = require('{main_file.replace(chr(92), '/')}');
        main.greet('John', 'Doe');
        """

        result = ctx.evaluate(code)
        print(f"Greeting: {result}")

        assert result == "Hello, John Doe"

        print("✓ Relative path require() works")


def test_console_log_available():
    """测试 console.log 在 require 环境中是否可用"""
    print("\n=== Test 7: console.log availability ===")

    ctx = never_jscore.Context(enable_node_compat=True)

    # 检查 console.log 是否可用
    result = ctx.evaluate("""
        typeof console !== 'undefined' && typeof console.log === 'function'
    """)

    print(f"console.log available: {result}")
    assert result == True

    print("✓ console.log is available")


if __name__ == "__main__":
    print("=" * 60)
    print("Node.js require() System Tests")
    print("=" * 60)

    try:
        test_basic_require()
        test_require_json()
        test_require_js_module()
        test_require_cache()
        test_module_exports_pattern()
        test_relative_require()
        test_console_log_available()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
