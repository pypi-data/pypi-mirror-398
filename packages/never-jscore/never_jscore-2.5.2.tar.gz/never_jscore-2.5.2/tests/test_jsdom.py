#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 jsdom 包的兼容性
"""

import sys
import io

import never_jscore
import os


def test_jsdom_basic():
    """测试基础 jsdom 功能"""
    print("\n=== Test 1: Basic jsdom import and JSDOM creation ===")

    ctx = never_jscore.Context(enable_node_compat=True)

    # 尝试 require jsdom
    code = """
    const { JSDOM } = require('jsdom');

    // 创建一个简单的 DOM
    const dom = new JSDOM('<!DOCTYPE html><html><body><h1>Hello World</h1></body></html>');

    // 获取 document
    const document = dom.window.document;

    // 测试 querySelector
    const h1 = document.querySelector('h1');

    ({
        tagName: h1.tagName,
        textContent: h1.textContent,
        innerHTML: document.body.innerHTML
    })
    """

    try:
        result = ctx.evaluate(code)
        print(f"JSDOM result: {result}")

        assert result['tagName'] == 'H1'
        assert result['textContent'] == 'Hello World'
        assert 'Hello World' in result['innerHTML']

        print("✓ Basic jsdom import and DOM creation works")
        return True
    except Exception as e:
        print(f"✗ Basic jsdom test failed: {e}")
        return False


def test_jsdom_dom_manipulation():
    """测试 DOM 操作"""
    print("\n=== Test 2: DOM manipulation with jsdom ===")

    ctx = never_jscore.Context(enable_node_compat=True)

    code = """
    const { JSDOM } = require('jsdom');

    const dom = new JSDOM('<!DOCTYPE html><html><body><div id="container"></div></body></html>');
    const document = dom.window.document;

    // 创建新元素
    const p = document.createElement('p');
    p.textContent = 'This is a paragraph';
    p.className = 'test-class';

    // 添加到容器
    const container = document.getElementById('container');
    container.appendChild(p);

    ({
        containerHTML: container.innerHTML,
        pTagName: p.tagName,
        pText: p.textContent,
        pClass: p.className
    })
    """

    try:
        result = ctx.evaluate(code)
        print(f"DOM manipulation result: {result}")

        assert 'This is a paragraph' in result['containerHTML']
        assert result['pTagName'] == 'P'
        assert result['pText'] == 'This is a paragraph'
        assert result['pClass'] == 'test-class'

        print("✓ DOM manipulation works")
        return True
    except Exception as e:
        print(f"✗ DOM manipulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_jsdom_query_selector():
    """测试 querySelector 和 querySelectorAll"""
    print("\n=== Test 3: querySelector and querySelectorAll ===")

    ctx = never_jscore.Context(enable_node_compat=True)

    code = """
    const { JSDOM } = require('jsdom');

    const html = `
        <!DOCTYPE html>
        <html>
        <body>
            <ul class="list">
                <li class="item">Item 1</li>
                <li class="item">Item 2</li>
                <li class="item">Item 3</li>
            </ul>
        </body>
        </html>
    `;

    const dom = new JSDOM(html);
    const document = dom.window.document;

    const items = document.querySelectorAll('.item');
    const firstItem = document.querySelector('.item');

    ({
        itemCount: items.length,
        firstItemText: firstItem.textContent.trim(),
        allItems: Array.from(items).map(item => item.textContent.trim())
    })
    """

    try:
        result = ctx.evaluate(code)
        print(f"querySelector result: {result}")

        assert result['itemCount'] == 3
        assert result['firstItemText'] == 'Item 1'
        assert result['allItems'] == ['Item 1', 'Item 2', 'Item 3']

        print("✓ querySelector and querySelectorAll work")
        return True
    except Exception as e:
        print(f"✗ querySelector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_jsdom_events():
    """测试事件系统"""
    print("\n=== Test 4: Event system ===")

    ctx = never_jscore.Context(enable_node_compat=True)

    code = """
    const { JSDOM } = require('jsdom');

    const dom = new JSDOM('<!DOCTYPE html><html><body><button id="btn">Click me</button></body></html>');
    const document = dom.window.document;

    let clickCount = 0;
    const button = document.getElementById('btn');

    button.addEventListener('click', () => {
        clickCount++;
    });

    // 手动触发事件
    const event = new dom.window.Event('click');
    button.dispatchEvent(event);
    button.dispatchEvent(event);
    button.dispatchEvent(event);

    clickCount
    """

    try:
        result = ctx.evaluate(code)
        print(f"Event system result: {result}")

        assert result == 3

        print("✓ Event system works")
        return True
    except Exception as e:
        print(f"✗ Event system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_jsdom_attributes():
    """测试属性操作"""
    print("\n=== Test 5: Attribute manipulation ===")

    ctx = never_jscore.Context(enable_node_compat=True)

    code = """
    const { JSDOM } = require('jsdom');

    const dom = new JSDOM('<!DOCTYPE html><html><body><div></div></body></html>');
    const document = dom.window.document;

    const div = document.querySelector('div');

    // 设置属性
    div.setAttribute('data-value', '123');
    div.setAttribute('title', 'Test Title');
    div.id = 'test-id';

    ({
        dataValue: div.getAttribute('data-value'),
        title: div.getAttribute('title'),
        id: div.id,
        hasDataAttr: div.hasAttribute('data-value')
    })
    """

    try:
        result = ctx.evaluate(code)
        print(f"Attribute manipulation result: {result}")

        assert result['dataValue'] == '123'
        assert result['title'] == 'Test Title'
        assert result['id'] == 'test-id'
        assert result['hasDataAttr'] == True

        print("✓ Attribute manipulation works")
        return True
    except Exception as e:
        print(f"✗ Attribute manipulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("JSDOM Compatibility Tests")
    print("=" * 60)

    results = []

    results.append(test_jsdom_basic())

    if results[0]:  # 只有基础测试通过才继续
        results.append(test_jsdom_dom_manipulation())
        results.append(test_jsdom_query_selector())
        results.append(test_jsdom_events())
        results.append(test_jsdom_attributes())

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All JSDOM tests passed!")
    else:
        print(f"✗ {total - passed} test(s) failed")
    print("=" * 60)

    sys.exit(0 if passed == total else 1)
