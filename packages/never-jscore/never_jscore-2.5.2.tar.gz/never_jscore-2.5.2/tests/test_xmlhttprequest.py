"""
测试 XMLHttpRequest 使用

展示如何使用内置的 XMLHttpRequest API

注意: 此测试需要 legacy_polyfill 功能，在 v2.5.0+ 中已移除。
当前版本使用 deno_web_api 模式，XMLHttpRequest 不可用（建议使用 fetch）。
"""

import sys
import os

import never_jscore


def check_xhr_available():
    """检查是否支持 XMLHttpRequest"""
    ctx = never_jscore.Context()
    try:
        result = ctx.evaluate("typeof XMLHttpRequest")
        if result == "undefined":
            print("⚠️  跳过测试: XMLHttpRequest 需要 legacy_polyfill 模式")
            print("    v2.5.0+ 已移除 legacy_polyfill 功能")
            print("    建议使用 fetch API 替代（参见 test_deno_web_api.py）")
            return False
        return True
    except:
        return False


def test_basic_xhr():
    """测试基本 XMLHttpRequest 使用"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            const xhr = new XMLHttpRequest();

            // 检查对象存在
            const exists = typeof XMLHttpRequest !== 'undefined';

            // 检查常量
            const constants = {
                UNSENT: xhr.UNSENT,
                OPENED: xhr.OPENED,
                HEADERS_RECEIVED: xhr.HEADERS_RECEIVED,
                LOADING: xhr.LOADING,
                DONE: xhr.DONE
            };

            return {
                exists,
                constants,
                initialState: xhr.readyState
            };
        })()
    """)

    assert result['exists'] == True
    assert result['constants']['UNSENT'] == 0
    assert result['constants']['DONE'] == 4
    assert result['initialState'] == 0

    print("✓ XMLHttpRequest 对象存在")
    print(f"  - 常量: {result['constants']}")


def test_xhr_open():
    """测试 xhr.open() 方法"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            const xhr = new XMLHttpRequest();

            // 打开请求
            xhr.open('GET', 'https://api.example.com/data');

            return {
                readyState: xhr.readyState,
                method: xhr._method,
                url: xhr._url
            };
        })()
    """)

    assert result['readyState'] == 1  # OPENED
    assert result['method'] == 'GET'
    assert 'api.example.com' in result['url']

    print("✓ xhr.open() 工作正常")


def test_xhr_set_request_header():
    """测试 xhr.setRequestHeader()"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', 'https://api.example.com/login');

            // 设置请求头
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('Authorization', 'Bearer token123');

            return {
                headers: xhr._headers
            };
        })()
    """)
    assert 'Content-Type' in result['headers']
    assert result['headers']['Content-Type'] == 'application/json'
    assert result['headers']['Authorization'] == 'Bearer token123'

    print("✓ setRequestHeader() 工作正常")
    print(f"  - 请求头: {result['headers']}")


def test_xhr_send_and_response():
    """测试 xhr.send() 和响应处理"""
    ctx = never_jscore.Context()

    # 注意：这会发起真实的网络请求
    # 使用一个公开的测试 API
    result = ctx.evaluate("""
        (async () => {
            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            resolve({
                                status: xhr.status,
                                statusText: xhr.statusText,
                                responseText: xhr.responseText.substring(0, 100),
                                readyState: xhr.readyState
                            });
                        } else {
                            reject(new Error('Request failed'));
                        }
                    }
                };

                xhr.open('GET', 'https://httpbin.org/get');
                xhr.send();
            });
        })()
    """)

    assert result['status'] == 200
    assert result['readyState'] == 4  # DONE

    print(f"✓ xhr.send() 成功")
    print(f"  - 状态: {result['status']} {result['statusText']}")
    print(f"  - 响应: {result['responseText']}...")


def test_xhr_post_json():
    """测试 POST JSON 数据"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.onload = function() {
                    const response = JSON.parse(xhr.responseText);
                    resolve({
                        status: xhr.status,
                        sentData: response.json,  // httpbin.org 会回显我们发送的数据
                        headers: response.headers
                    });
                };

                xhr.onerror = function() {
                    reject(new Error('Network error'));
                };

                xhr.open('POST', 'https://httpbin.org/post');
                xhr.setRequestHeader('Content-Type', 'application/json');

                const data = {
                    username: 'testuser',
                    password: 'testpass',
                    timestamp: Date.now()
                };

                xhr.send(JSON.stringify(data));
            });
        })()
    """)

    assert result['status'] == 200
    assert result['sentData']['username'] == 'testuser'

    print(f"✓ POST JSON 成功")
    print(f"  - 发送的数据: {result['sentData']}")


def test_xhr_event_handlers():
    """测试 XHR 事件处理器"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            const events = [];

            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.onloadstart = () => events.push('loadstart');
                xhr.onprogress = () => events.push('progress');
                xhr.onload = () => {
                    events.push('load');
                    resolve({
                        events,
                        status: xhr.status
                    });
                };
                xhr.onloadend = () => events.push('loadend');
                xhr.onerror = () => {
                    events.push('error');
                    reject(new Error('XHR error'));
                };

                xhr.open('GET', 'https://httpbin.org/get');
                xhr.send();
            });
        })()
    """)

    assert 'loadstart' in result['events']
    assert 'load' in result['events']

    print(f"✓ 事件处理器触发")
    print(f"  - 事件序列: {result['events']}")


def test_xhr_abort():
    """测试 xhr.abort()"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', 'https://httpbin.org/delay/5');  // 延迟 5 秒的请求

            let aborted = false;
            xhr.onabort = () => {
                aborted = true;
            };

            xhr.send();

            // 立即中止
            xhr.abort();

            // 等待一下确保事件触发
            await new Promise(r => setTimeout(r, 100));

            return {
                aborted,
                readyState: xhr.readyState
            };
        })()
    """)

    assert result['aborted'] == True
    assert result['readyState'] == 4  # DONE

    print("✓ xhr.abort() 工作正常")


def test_xhr_get_response_header():
    """测试获取响应头"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            return new Promise((resolve) => {
                const xhr = new XMLHttpRequest();

                xhr.onload = function() {
                    const contentType = xhr.getResponseHeader('Content-Type');
                    const allHeaders = xhr.getAllResponseHeaders();

                    resolve({
                        contentType,
                        hasHeaders: allHeaders.length > 0
                    });
                };

                xhr.open('GET', 'https://httpbin.org/get');
                xhr.send();
            });
        })()
    """)

    assert result['contentType'] is not None
    assert result['hasHeaders'] == True

    print(f"✓ 响应头获取成功")
    print(f"  - Content-Type: {result['contentType']}")


def test_xhr_hook_interception():
    """实战：Hook XMLHttpRequest 拦截请求"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        // Hook XMLHttpRequest.send
        const originalSend = XMLHttpRequest.prototype.send;
        const interceptedRequests = [];

        XMLHttpRequest.prototype.send = function(body) {
            // 拦截请求信息
            interceptedRequests.push({
                method: this._method,
                url: this._url,
                headers: this._headers,
                body: body
            });

            // 如果我们想提前返回（不发送真实请求）
            if (this._url.includes('block-this')) {
                $return({
                    hooked: true,
                    intercepted: interceptedRequests
                });
            }

            // 否则继续发送
            return originalSend.call(this, body);
        };

        // 模拟多个请求
        const xhr1 = new XMLHttpRequest();
        xhr1.open('POST', 'https://api.example.com/login');
        xhr1.setRequestHeader('Content-Type', 'application/json');
        xhr1.send(JSON.stringify({ user: 'admin' }));

        const xhr2 = new XMLHttpRequest();
        xhr2.open('GET', 'https://api.example.com/block-this');
        xhr2.send();  // 这个会被拦截
    """)

    assert result['hooked'] == True
    assert len(result['intercepted']) >= 2
    assert result['intercepted'][0]['method'] == 'POST'

    print(f"\n=== Hook XHR 拦截 ===")
    print(f"✓ 拦截到 {len(result['intercepted'])} 个请求")
    for i, req in enumerate(result['intercepted']):
        print(f"  {i+1}. {req['method']} {req['url']}")


def test_xhr_with_timeout():
    """测试 XHR 超时"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.timeout = 100;  // 100ms 超时

                xhr.ontimeout = () => {
                    resolve({
                        timedOut: true,
                        readyState: xhr.readyState
                    });
                };

                xhr.onload = () => {
                    resolve({
                        timedOut: false,
                        status: xhr.status
                    });
                };

                // 请求一个会延迟的端点
                xhr.open('GET', 'https://httpbin.org/delay/1');  // 延迟 1 秒
                xhr.send();
            });
        })()
    """)

    # 可能超时也可能成功（取决于网络速度）
    print(f"✓ 超时测试: {'超时' if result.get('timedOut') else '成功'}")


def test_xhr_response_types():
    """测试不同的响应类型"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            return new Promise((resolve) => {
                const xhr = new XMLHttpRequest();

                xhr.responseType = 'json';  // 设置响应类型为 JSON

                xhr.onload = function() {
                    resolve({
                        responseType: xhr.responseType,
                        response: xhr.response,
                        hasResponseText: xhr.responseText.length > 0
                    });
                };

                xhr.open('GET', 'https://httpbin.org/json');
                xhr.send();
            });
        })()
    """)

    assert result['responseType'] == 'json'
    assert isinstance(result['response'], dict)

    print(f"✓ 响应类型处理")
    print(f"  - responseType: {result['responseType']}")
    print(f"  - response: {str(result['response'])[:100]}...")


def test_real_world_api_call():
    """实战：调用真实 API"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        (async () => {
            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.onload = function() {
                    if (xhr.status === 200) {
                        const data = JSON.parse(xhr.responseText);
                        resolve({
                            success: true,
                            origin: data.origin,
                            headers: data.headers,
                            userAgent: data.headers['User-Agent']
                        });
                    } else {
                        reject(new Error('API call failed'));
                    }
                };

                xhr.onerror = () => reject(new Error('Network error'));

                xhr.open('GET', 'https://httpbin.org/get');
                xhr.setRequestHeader('X-Custom-Header', 'test-value');
                xhr.send();
            });
        })()
    """)

    assert result['success'] == True
    assert 'origin' in result
    assert 'userAgent' in result

    print(f"\n=== 真实 API 调用 ===")
    print(f"✓ 请求成功")
    print(f"  - 客户端 IP: {result['origin']}")
    print(f"  - User-Agent: {result['userAgent'][:60]}...")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 XMLHttpRequest")
    print("=" * 60)

    # 检查是否支持 XMLHttpRequest
    if not check_xhr_available():
        print("\n" + "=" * 60)
        print("⚠️  测试已跳过（XMLHttpRequest 需要 legacy_polyfill）")
        print("=" * 60)
        sys.exit(0)

    test_basic_xhr()
    test_xhr_open()
    test_xhr_set_request_header()
    test_xhr_send_and_response()
    test_xhr_post_json()
    test_xhr_event_handlers()
    test_xhr_abort()
    test_xhr_get_response_header()
    test_xhr_hook_interception()
    test_xhr_with_timeout()
    test_xhr_response_types()
    test_real_world_api_call()

    print("\n" + "=" * 60)
    print("✅ 所有 XMLHttpRequest 测试通过！")
    print("=" * 60)
    print("\n💡 提示：XMLHttpRequest 完全兼容浏览器 API")
    print("   可以用于发送真实的 HTTP 请求和拦截请求数据")
