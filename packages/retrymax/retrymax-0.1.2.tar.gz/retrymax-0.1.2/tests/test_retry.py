import asyncio
from retrymax import retry


def assert_equal(a, b, msg=""):
    if a != b:
        raise AssertionError(f"{a} != {b}. {msg}")


def test_retry_succeeds_after_failures():
    print("\n[test] retry succeeds after failures")
    calls = 0

    @retry(times=3, verbose=True)
    def func():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("fail")
        return "ok"

    result = func()
    assert_equal(result, "ok")
    assert_equal(calls, 3)
    print("[test] PASSED")


def test_retry_fails_after_max_attempts():
    print("\n[test] retry fails after max attempts")
    calls = 0

    @retry(times=3, verbose=True)
    def func():
        nonlocal calls
        calls += 1
        raise ValueError("always fails")

    try:
        func()
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass

    assert_equal(calls, 3)
    print("[test] PASSED")


def test_retry_calls_callback():
    print("\n[test] retry calls callback")
    calls = 0
    callback_calls = []

    def on_retry(exception, attempt):
        callback_calls.append((attempt, str(exception)))
        print(f"[callback] attempt {attempt}")

    @retry(times=3, on_retry=on_retry, verbose=True)
    def func():
        nonlocal calls
        calls += 1
        raise RuntimeError("boom")

    try:
        func()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError:
        pass

    assert_equal(calls, 3)
    assert_equal(len(callback_calls), 3)
    assert_equal(callback_calls[0][0], 1)
    print("[test] PASSED")


async def test_async_retry():
    print("\n[test] async retry")
    calls = 0

    @retry(times=3, verbose=True)
    async def func():
        nonlocal calls
        calls += 1
        raise ValueError("async fail")

    try:
        await func()
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass

    assert_equal(calls, 3)
    print("[test] PASSED")


def main():
    test_retry_succeeds_after_failures()
    test_retry_fails_after_max_attempts()
    test_retry_calls_callback()
    asyncio.run(test_async_retry())
    print("\nALL TESTS PASSED 🎉")


if __name__ == "__main__":
    main()
