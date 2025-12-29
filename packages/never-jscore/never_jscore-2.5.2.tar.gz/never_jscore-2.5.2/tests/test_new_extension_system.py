"""
Test the new modular extension system
Tests core and hook extensions functionality
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import never_jscore
import json

def test_core_extension_return():
    """Test core extension's $return function"""
    print("\n=== Test 1: Core Extension - $return ===")

    ctx = never_jscore.Context()

    # Test $return function (can be caught by try-catch)
    try:
        result = ctx.evaluate("""
            try {
                $return({ key: 'intercepted' });
            } catch (e) {
                ({ caught: true, message: e.message });
            }
        """)
        print(f"✓ $return test passed: {result}")
        assert result['caught'] == True
        assert '[NEVER_JSCORE_EARLY_RETURN]' in result['message']
    except Exception as e:
        print(f"✗ Test failed: {e}")
        raise

def test_core_extension_exit():
    """Test core extension's $exit function (alias for $return)"""
    print("\n=== Test 2: Core Extension - $exit ===")

    ctx = never_jscore.Context()

    try:
        result = ctx.evaluate("""
            try {
                $exit({ status: 'exited' });
            } catch (e) {
                ({ caught: true, message: e.message });
            }
        """)
        print(f"✓ $exit test passed: {result}")
        assert result['caught'] == True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        raise

def test_hook_extension_terminate():
    """Test hook extension's $terminate function (uncatchable)"""
    print("\n=== Test 3: Hook Extension - $terminate (uncatchable) ===")

    ctx = never_jscore.Context()
    ctx.clear_hook_data()

    try:
        # $terminate cannot be caught by try-catch
        ctx.evaluate("""
            try {
                $terminate({ secret: 'cannot catch this!' });
                'should not reach here';
            } catch (e) {
                'caught in JS';  // This won't execute
            }
        """)
        print("✗ Should have thrown an exception")
        assert False
    except Exception as e:
        # Python catches the termination
        print(f"✓ Caught termination in Python: {type(e).__name__}")

        # Check if hook data was saved
        hook_data = ctx.get_hook_data()
        if hook_data:
            data = json.loads(hook_data)
            print(f"✓ Hook data retrieved: {data}")
            assert data['secret'] == 'cannot catch this!'
        else:
            print("✗ No hook data found")
            assert False

def test_hook_interception_scenario():
    """Test realistic hook interception scenario"""
    print("\n=== Test 4: Hook Interception Scenario ===")

    ctx = never_jscore.Context()
    ctx.clear_hook_data()

    # Simulate hooking an encryption function
    ctx.compile("""
        const CryptoLib = {
            encrypt: function(text, key) {
                // Original implementation
                return btoa(text + key);
            }
        };

        function login(username, password) {
            const encryptedPassword = CryptoLib.encrypt(password, 'secret_key_123');
            return { username, encryptedPassword };
        }
    """)

    # Hook the encrypt function to intercept parameters
    try:
        ctx.evaluate("""
            const original = CryptoLib.encrypt;
            CryptoLib.encrypt = function(text, key) {
                // Intercept and terminate
                $terminate({ text, key, timestamp: Date.now() });
            };

            try {
                login('user123', 'mypassword');
            } catch (e) {
                // Try-catch won't help!
            }
        """)
        print("✗ Should have terminated")
        assert False
    except Exception:
        hook_data = ctx.get_hook_data()
        if hook_data:
            data = json.loads(hook_data)
            print(f"✓ Intercepted encryption parameters:")
            print(f"  - Text: {data['text']}")
            print(f"  - Key: {data['key']}")
            assert data['text'] == 'mypassword'
            assert data['key'] == 'secret_key_123'
        else:
            print("✗ No hook data found")
            assert False

def test_api_protection_functions():
    """Test API protection utilities"""
    print("\n=== Test 5: API Protection Functions ===")

    ctx = never_jscore.Context()

    # Note: api_protection module is loaded via deno_web_api feature
    # Check if protection functions are available
    try:
        result = ctx.evaluate("""
            // Test if we have Deno object and protection utilities would be available
            typeof Deno !== 'undefined'
        """)
        print(f"✓ Deno object available: {result}")

        # Test some basic Web APIs
        result = ctx.evaluate("""
            ({
                hasURL: typeof URL !== 'undefined',
                hasTextEncoder: typeof TextEncoder !== 'undefined',
                hasCrypto: typeof crypto !== 'undefined',
                hasFetch: typeof fetch !== 'undefined'
            })
        """)
        print(f"✓ Web APIs available: {result}")

    except Exception as e:
        print(f"Note: {e}")

def test_context_reuse():
    """Test that context can be reused after hook interception"""
    print("\n=== Test 6: Context Reuse After Hook ===")

    ctx = never_jscore.Context()

    # First interception
    ctx.clear_hook_data()
    try:
        ctx.evaluate('$terminate({ test: 1 })')
    except:
        pass

    data1 = ctx.get_hook_data()
    assert data1 is not None
    print(f"✓ First interception: {data1}")

    # Clear and try again
    ctx.clear_hook_data()
    try:
        ctx.evaluate('$terminate({ test: 2 })')
    except:
        pass

    data2 = ctx.get_hook_data()
    assert data2 is not None
    print(f"✓ Second interception: {data2}")

    # Verify they're different
    assert json.loads(data1)['test'] != json.loads(data2)['test']
    print("✓ Context successfully reused")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing New Modular Extension System")
    print("=" * 60)

    tests = [
        test_core_extension_return,
        test_core_extension_exit,
        test_hook_extension_terminate,
        test_hook_interception_scenario,
        test_api_protection_functions,
        test_context_reuse,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test {test.__name__} failed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
