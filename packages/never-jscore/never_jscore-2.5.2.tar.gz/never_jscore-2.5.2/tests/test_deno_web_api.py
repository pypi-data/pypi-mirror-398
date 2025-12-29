#!/usr/bin/env python3
"""
Test Deno Web API Integration

Tests the official Deno Web API functionality when using deno_web_api feature.
This requires building with: maturin develop --no-default-features --features deno_web_api
"""

import sys
import never_jscore


def test_url_api():
    """Test standard URL API"""
    print("\n=== Testing URL API ===")
    ctx = never_jscore.Context()

    # Test URL constructor
    result = ctx.evaluate("""
        const url = new URL('https://example.com:8080/path?key=value#hash');
        ({
            href: url.href,
            protocol: url.protocol,
            hostname: url.hostname,
            port: url.port,
            pathname: url.pathname,
            search: url.search,
            hash: url.hash
        })
    """)

    print(f"URL parsed: {result}")
    assert result['protocol'] == 'https:', f"Expected 'https:', got {result['protocol']}"
    assert result['hostname'] == 'example.com', f"Expected 'example.com', got {result['hostname']}"
    assert result['port'] == '8080', f"Expected '8080', got {result['port']}"
    assert result['pathname'] == '/path', f"Expected '/path', got {result['pathname']}"
    assert result['search'] == '?key=value', f"Expected '?key=value', got {result['search']}"
    assert result['hash'] == '#hash', f"Expected '#hash', got {result['hash']}"
    print("[OK] URL API working correctly")


def test_text_encoder_decoder():
    """Test TextEncoder and TextDecoder"""
    print("\n=== Testing TextEncoder/TextDecoder ===")
    ctx = never_jscore.Context()

    # Test TextEncoder
    result = ctx.evaluate("""
        const encoder = new TextEncoder();
        const encoded = encoder.encode('Hello 世界');
        Array.from(encoded)
    """)

    print(f"Encoded bytes: {result}")
    assert isinstance(result, list), "Expected array of bytes"
    assert len(result) > 5, "Expected encoded bytes"

    # Test TextDecoder
    result = ctx.evaluate("""
        const decoder = new TextDecoder();
        const bytes = new Uint8Array([72, 101, 108, 108, 111]);
        decoder.decode(bytes)
    """)

    print(f"Decoded text: {result}")
    assert result == "Hello", f"Expected 'Hello', got {result}"
    print("[OK] TextEncoder/TextDecoder working correctly")


def test_atob_btoa():
    """Test atob/btoa Base64 encoding"""
    print("\n=== Testing atob/btoa ===")
    ctx = never_jscore.Context()

    # Test btoa
    result = ctx.evaluate("btoa('Hello World')")
    print(f"btoa('Hello World'): {result}")
    assert result == "SGVsbG8gV29ybGQ=", f"Expected 'SGVsbG8gV29ybGQ=', got {result}"

    # Test atob
    result = ctx.evaluate("atob('SGVsbG8gV29ybGQ=')")
    print(f"atob('SGVsbG8gV29ybGQ='): {result}")
    assert result == "Hello World", f"Expected 'Hello World', got {result}"
    print("[OK] atob/btoa working correctly")


def test_console_api():
    """Test console API"""
    print("\n=== Testing console API ===")
    ctx = never_jscore.Context(enable_logging=True)

    # Test various console methods
    ctx.evaluate("""
        console.log('This is a log message');
        console.info('This is an info message');
        console.warn('This is a warning');
        console.error('This is an error');
        console.debug('This is debug info');
    """)

    print("[OK] console API working (check output above)")


def test_event_api():
    """Test Event and EventTarget API"""
    print("\n=== Testing Event API ===")
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        const target = new EventTarget();
        let eventFired = false;
        let eventData = null;

        target.addEventListener('custom', (e) => {
            eventFired = true;
            eventData = e.detail;
        });

        const event = new CustomEvent('custom', { detail: { message: 'test' } });
        target.dispatchEvent(event);

        ({ eventFired, eventData })
    """)

    print(f"Event test result: {result}")
    assert result['eventFired'] == True, "Event should have fired"
    assert result['eventData']['message'] == 'test', "Event data should be preserved"
    print("[OK] Event API working correctly")


def test_structured_clone():
    """Test structuredClone API"""
    print("\n=== Testing structuredClone ===")
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        const original = {
            name: 'test',
            nested: { value: 42 },
            array: [1, 2, 3]
        };

        const cloned = structuredClone(original);
        cloned.nested.value = 999;

        ({
            originalValue: original.nested.value,
            clonedValue: cloned.nested.value,
            isDeepClone: original.nested.value !== cloned.nested.value
        })
    """)

    print(f"StructuredClone result: {result}")
    assert result['originalValue'] == 42, "Original should not be modified"
    assert result['clonedValue'] == 999, "Clone should be modified"
    assert result['isDeepClone'] == True, "Should be a deep clone"
    print("[OK] structuredClone working correctly")


def test_abort_controller():
    """Test AbortController and AbortSignal"""
    print("\n=== Testing AbortController ===")
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        const controller = new AbortController();
        const signal = controller.signal;

        let aborted = false;
        signal.addEventListener('abort', () => {
            aborted = true;
        });

        const wasAbortedBefore = signal.aborted;
        controller.abort();
        const wasAbortedAfter = signal.aborted;

        ({
            wasAbortedBefore,
            wasAbortedAfter,
            aborted,
            reason: signal.reason?.toString()
        })
    """)

    print(f"AbortController result: {result}")
    assert result['wasAbortedBefore'] == False, "Should not be aborted initially"
    assert result['wasAbortedAfter'] == True, "Should be aborted after abort()"
    assert result['aborted'] == True, "Event listener should fire"
    print("[OK] AbortController working correctly")


def test_crypto_random():
    """Test crypto.randomUUID and crypto.getRandomValues"""
    print("\n=== Testing crypto API ===")
    ctx = never_jscore.Context()

    # Test randomUUID
    result = ctx.evaluate("""
        const uuid = crypto.randomUUID();
        ({
            uuid,
            isValidUUID: /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(uuid)
        })
    """)

    print(f"UUID: {result['uuid']}")
    assert result['isValidUUID'] == True, "Should generate valid UUID v4"

    # Test getRandomValues
    result = ctx.evaluate("""
        const array = new Uint8Array(10);
        crypto.getRandomValues(array);
        Array.from(array)
    """)

    print(f"Random bytes: {result}")
    assert len(result) == 10, "Should fill array with 10 bytes"
    assert any(x > 0 for x in result), "Should have non-zero values"
    print("[OK] crypto API working correctly")


def test_timers():
    """Test setTimeout/setInterval"""
    print("\n=== Testing Timers ===")
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        let count = 0;
        const promise = new Promise(resolve => {
            setTimeout(() => {
                count++;
                resolve(count);
            }, 10);
        });
        promise
    """)

    print(f"Timer result: {result}")
    assert result == 1, "Timer should execute once"
    print("[OK] Timers working correctly")


def test_performance_api():
    """Test performance.now()"""
    print("\n=== Testing Performance API ===")
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        const start = performance.now();
        let sum = 0;
        for (let i = 0; i < 1000; i++) {
            sum += i;
        }
        const end = performance.now();
        ({
            duration: end - start,
            isPositive: (end - start) > 0,
            sum
        })
    """)

    print(f"Performance test: {result}")
    assert result['isPositive'] == True, "Duration should be positive"
    assert result['sum'] == 499500, "Sum should be correct"
    print("[OK] Performance API working correctly")


def test_streams_api():
    """Test ReadableStream and WritableStream"""
    print("\n=== Testing Streams API ===")
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        const stream = new ReadableStream({
            start(controller) {
                controller.enqueue('chunk1');
                controller.enqueue('chunk2');
                controller.close();
            }
        });

        const reader = stream.getReader();
        const chunks = [];

        async function readStream() {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                chunks.push(value);
            }
            return chunks;
        }

        readStream()
    """)

    print(f"Stream chunks: {result}")
    assert result == ['chunk1', 'chunk2'], "Should read all chunks"
    print("[OK] Streams API working correctly")


def test_never_jscore_specific_apis():
    """Test never_jscore specific APIs still work with deno_web"""
    print("\n=== Testing never_jscore Specific APIs ===")
    ctx = never_jscore.Context()

    # Test $return
    result = ctx.evaluate("""
        function test() {
            $return({ intercepted: true, value: 42 });
            return 'should not reach here';
        }
        test()
    """)

    print(f"$return result: {result}")
    assert result['intercepted'] == True, "$return should intercept execution"
    assert result['value'] == 42, "$return should pass data"

    # Test $terminate
    ctx.clear_hook_data()
    try:
        ctx.evaluate("""
            $terminate({ key: 'secret' });
            'should not reach here'
        """)
    except:
        pass

    hook_data = ctx.get_hook_data()
    print(f"$terminate hook_data: {hook_data}")
    assert hook_data is not None, "$terminate should save data"

    print("[OK] never_jscore specific APIs still working")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing Deno Web API Integration")
    print("=" * 60)

    tests = [
        ("URL API", test_url_api),
        ("TextEncoder/TextDecoder", test_text_encoder_decoder),
        ("atob/btoa", test_atob_btoa),
        ("console API", test_console_api),
        ("Event API", test_event_api),
        ("structuredClone", test_structured_clone),
        ("AbortController", test_abort_controller),
        ("crypto API", test_crypto_random),
        ("Timers", test_timers),
        ("Performance API", test_performance_api),
        ("Streams API", test_streams_api),
        ("never_jscore APIs", test_never_jscore_specific_apis),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
