import asyncio
import pytest
from retrymax import retry


def test_retry_succeeds_after_failures():
    calls = 0

    @retry(times=3)
    def func():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("fail")
        return "ok"

    result = func()
    assert result == "ok"
    assert calls == 3


def test_retry_fails_after_max_attempts():
    calls = 0

    @retry(times=3)
    def func():
        nonlocal calls
        calls += 1
        raise ValueError("always fails")

    with pytest.raises(ValueError):
        func()

    assert calls == 3


def test_retry_calls_callback():
    calls = 0
    callback_calls = []

    def on_retry(exception, attempt):
        callback_calls.append((attempt, str(exception)))

    @retry(times=3, on_retry=on_retry)
    def func():
        nonlocal calls
        calls += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        func()

    assert calls == 3
    assert len(callback_calls) == 3
    assert callback_calls[0][0] == 1


@pytest.mark.asyncio
async def test_async_retry():
    calls = 0

    @retry(times=3)
    async def func():
        nonlocal calls
        calls += 1
        raise ValueError("async fail")

    with pytest.raises(ValueError):
        await func()

    assert calls == 3
