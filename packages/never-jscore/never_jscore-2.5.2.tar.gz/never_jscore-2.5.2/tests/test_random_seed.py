"""
测试确定性随机数功能

展示如何使用 random_seed 参数固定随机数，用于调试动态加密算法
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import never_jscore


def test_random_seed_math_random():
    """测试 Math.random() 的种子控制"""
    # 创建两个使用相同种子的 Context
    ctx1 = never_jscore.Context(random_seed=12345)
    randoms1 = ctx1.evaluate("[Math.random(), Math.random(), Math.random()]")
    del ctx1  # 删除第一个Context再创建第二个

    ctx2 = never_jscore.Context(random_seed=12345)
    randoms2 = ctx2.evaluate("[Math.random(), Math.random(), Math.random()]")
    del ctx2

    # 验证相同种子产生相同随机数
    assert randoms1 == randoms2, "相同种子应该产生相同的随机数序列"

    print(f"[OK] Context1 随机数: {randoms1}")
    print(f"[OK] Context2 随机数: {randoms2}")
    print(f"[OK] 两者完全相同！")


def test_random_seed_crypto_uuid():
    """测试 crypto.randomUUID() 的种子控制"""
    ctx1 = never_jscore.Context(random_seed=99999)
    uuid1 = ctx1.evaluate("crypto.randomUUID()")
    del ctx1

    ctx2 = never_jscore.Context(random_seed=99999)
    uuid2 = ctx2.evaluate("crypto.randomUUID()")
    del ctx2

    assert uuid1 == uuid2, "相同种子应该产生相同的 UUID"

    print(f"\n[OK] UUID1: {uuid1}")
    print(f"[OK] UUID2: {uuid2}")
    print(f"[OK] 使用相同种子，UUID 完全相同")


def test_random_seed_crypto_get_random_values():
    """测试 crypto.getRandomValues() 的种子控制"""
    ctx1 = never_jscore.Context(random_seed=42)
    # 生成随机字节数组
    bytes1 = ctx1.evaluate("""
        const arr = new Uint8Array(10);
        crypto.getRandomValues(arr);
        Array.from(arr)
    """)
    del ctx1

    ctx2 = never_jscore.Context(random_seed=42)
    bytes2 = ctx2.evaluate("""
        const arr = new Uint8Array(10);
        crypto.getRandomValues(arr);
        Array.from(arr)
    """)
    del ctx2

    assert bytes1 == bytes2, "相同种子应该产生相同的随机字节"

    print(f"\n[OK] 随机字节1: {bytes1}")
    print(f"[OK] 随机字节2: {bytes2}")
    print(f"[OK] 完全相同！")


def test_different_seeds_different_results():
    """测试不同种子产生不同结果"""
    ctx1 = never_jscore.Context(random_seed=111)


    random1 = ctx1.evaluate("Math.random()")
    del ctx1

    ctx2 = never_jscore.Context(random_seed=222)
    random2 = ctx2.evaluate("Math.random()")

    assert random1 != random2, "不同种子应该产生不同的随机数"

    print(f"\n[OK] 种子111: {random1}")
    print(f"[OK] 种子222: {random2}")
    print(f"[OK] 不同种子产生不同随机数")


def test_no_seed_truly_random():
    """测试不指定种子时真正随机"""
    ctx1 = never_jscore.Context()  # 无种子


    randoms1 = ctx1.evaluate("[Math.random(), Math.random(), Math.random()]")
    del ctx1

    ctx2 = never_jscore.Context()  # 无种子
    randoms2 = ctx2.evaluate("[Math.random(), Math.random(), Math.random()]")

    # 真随机时几乎不可能完全相同
    assert randoms1 != randoms2, "无种子时应该是真随机"

    print(f"\n[OK] 无种子1: {randoms1}")
    print(f"[OK] 无种子2: {randoms2}")
    print(f"[OK] 真随机，结果不同")


def test_reproducible_encryption():
    """实战场景：可重现的加密算法调试"""
    # 场景：某个网站的加密算法混入了随机 nonce
    # 使用固定种子可以让每次执行结果完全相同，方便调试

    # 创建两个使用相同种子的 Context
    ctx1 = never_jscore.Context(random_seed=888)
    ctx1.compile("""
        function encryptWithNonce(data, key) {
            // 生成随机 nonce（通常会导致每次结果不同）
            const nonce = Math.random().toString(36).substring(7);

            // 加密逻辑（简化版）
            const encrypted = btoa(data + ':' + key + ':' + nonce);

            return {
                encrypted: encrypted,
                nonce: nonce
            };
        }
    """)
    result1 = ctx1.call("encryptWithNonce", ["hello", "secret"])

    del ctx1

    ctx2 = never_jscore.Context(random_seed=888)
    ctx2.compile("""
        function encryptWithNonce(data, key) {
            // 生成随机 nonce（通常会导致每次结果不同）
            const nonce = Math.random().toString(36).substring(7);

            // 加密逻辑（简化版）
            const encrypted = btoa(data + ':' + key + ':' + nonce);

            return {
                encrypted: encrypted,
                nonce: nonce
            };
        }
    """)
    result2 = ctx2.call("encryptWithNonce", ["hello", "secret"])

    # 因为使用了相同的种子，nonce 也会相同
    assert result1['nonce'] == result2['nonce'], "固定种子应该产生相同的 nonce"
    assert result1['encrypted'] == result2['encrypted'], "加密结果应该完全相同"

    print(f"\n=== 可重现的加密调试 ===")
    print(f"[OK] 第一次加密: {result1['encrypted']}")
    print(f"[OK] 第二次加密: {result2['encrypted']}")
    print(f"[OK] nonce1: {result1['nonce']}")
    print(f"[OK] nonce2: {result2['nonce']}")
    print(f"[OK] 完全相同，调试友好！")


def test_sequence_consistency():
    """测试随机数序列的一致性"""
    ctx1 = never_jscore.Context(random_seed=777)

    # 生成 10 个随机数
    sequence1 = ctx1.evaluate("""
        const arr = [];
        for (let i = 0; i < 10; i++) {
            arr.push(Math.random());
        }
        arr
    """)

    # 重新创建相同种子的 Context
    del ctx1

    ctx2 = never_jscore.Context(random_seed=777)
    sequence2 = ctx2.evaluate("""
        const arr = [];
        for (let i = 0; i < 10; i++) {
            arr.push(Math.random());
        }
        arr
    """)

    # 验证整个序列完全相同
    assert sequence1 == sequence2, "整个随机数序列应该完全相同"

    print(f"\n[OK] 序列1 前5个: {sequence1[:5]}")
    print(f"[OK] 序列2 前5个: {sequence2[:5]}")
    print(f"[OK] 10个随机数序列完全相同")


def test_mixed_random_apis():
    """测试混合使用多个随机 API"""
    ctx1 = never_jscore.Context(random_seed=555)

    result1 = ctx1.evaluate("""
        ({
            mathRandom: Math.random(),
            uuid: crypto.randomUUID(),
            bytes: Array.from(crypto.getRandomValues(new Uint8Array(5))),
            anotherRandom: Math.random()
        })
    """)
    del ctx1

    ctx2 = never_jscore.Context(random_seed=555)

    result2 = ctx2.evaluate("""
        ({
            mathRandom: Math.random(),
            uuid: crypto.randomUUID(),
            bytes: Array.from(crypto.getRandomValues(new Uint8Array(5))),
            anotherRandom: Math.random()
        })
    """)

    # 所有随机 API 都应该产生相同结果
    assert result1['mathRandom'] == result2['mathRandom']
    assert result1['uuid'] == result2['uuid']
    assert result1['bytes'] == result2['bytes']
    assert result1['anotherRandom'] == result2['anotherRandom']

    print(f"\n=== 混合使用随机 API ===")
    print(f"[OK] Math.random(): {result1['mathRandom']}")
    print(f"[OK] UUID: {result1['uuid']}")
    print(f"[OK] 随机字节: {result1['bytes']}")
    print(f"[OK] 所有 API 结果一致！")


def test_real_world_sign_generation():
    """实战：调试动态签名生成"""
    # 场景：某 API 的签名算法包含时间戳和随机盐

    # 创建两个使用相同种子的 Context
    ctx1 = never_jscore.Context(random_seed=123456)
    ctx1.compile("""
        function generateSignature(apiKey, data, timestamp) {
            // 随机盐（会导致每次签名不同）
            const salt = Math.random().toString(36).substring(2, 10);

            // 签名逻辑
            const message = apiKey + data + timestamp + salt;
            const signature = md5(message);

            return {
                signature: signature,
                timestamp: timestamp,
                salt: salt,
                message: message
            };
        }
    """)
    sign1 = ctx1.call("generateSignature", ["my-api-key", "user_id=123", 1234567890])

    del ctx1

    ctx2 = never_jscore.Context(random_seed=123456)
    ctx2.compile("""
        function generateSignature(apiKey, data, timestamp) {
            // 随机盐（会导致每次签名不同）
            const salt = Math.random().toString(36).substring(2, 10);

            // 签名逻辑
            const message = apiKey + data + timestamp + salt;
            const signature = md5(message);

            return {
                signature: signature,
                timestamp: timestamp,
                salt: salt,
                message: message
            };
        }
    """)
    sign2 = ctx2.call("generateSignature", ["my-api-key", "user_id=123", 1234567890])

    # 使用固定种子后，盐值相同，签名可重现
    assert sign1['salt'] == sign2['salt'], "固定种子让盐值可重现"
    assert sign1['signature'] == sign2['signature'], "签名结果可重现"

    print(f"\n=== 动态签名调试 ===")
    print(f"[OK] 签名1: {sign1['signature']}")
    print(f"[OK] 签名2: {sign2['signature']}")
    print(f"[OK] 盐值1: {sign1['salt']}")
    print(f"[OK] 盐值2: {sign2['salt']}")
    print(f"[OK] 完全可重现，方便调试！")


if __name__ == "__main__":
    print("=" * 60)
    print("测试确定性随机数功能")
    print("=" * 60)

    test_random_seed_math_random()
    test_random_seed_crypto_uuid()
    test_random_seed_crypto_get_random_values()
    test_different_seeds_different_results()
    test_no_seed_truly_random()
    test_reproducible_encryption()
    test_sequence_consistency()
    test_mixed_random_apis()
    # test_real_world_sign_generation()

    print("\n" + "=" * 60)
    print("[PASS] 所有确定性随机数测试通过！")
    print("=" * 60)
    print("\n提示：使用 random_seed 可以让包含随机数的算法完全可重现")
    print("   这对于调试动态加密、签名生成等场景非常有用！")
