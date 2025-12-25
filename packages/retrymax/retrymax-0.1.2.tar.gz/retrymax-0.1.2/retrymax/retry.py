import functools
import time
import asyncio
import inspect

def retry(
    times=3,
    delay=0,
    backoff=None,
    exceptions=(Exception,),
    verbose=False,
    on_retry=None
):
    def decorator(func):
        if inspect.iscoroutinefunction(func):  # Async function
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                current_delay = delay
                last_exception = None

                for attempt in range(times):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if verbose:
                            print(f"[retrymax] Attempt {attempt + 1} failed: {e}")
                        if on_retry:
                            try:
                                on_retry(e, attempt + 1)
                            except Exception as hook_error:
                                print(f"[retrymax] on_retry callback error: {hook_error}")

                        if attempt < times - 1:
                            if current_delay > 0:
                                await asyncio.sleep(current_delay)
                            if backoff == "exp":
                                current_delay *= 2

                raise last_exception

            return async_wrapper

        else:  # Sync function
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                current_delay = delay
                last_exception = None

                for attempt in range(times):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if verbose:
                            print(f"[retrymax] Attempt {attempt + 1} failed: {e}")
                        if on_retry:
                            try:
                                on_retry(e, attempt + 1)
                            except Exception as hook_error:
                                print(f"[retrymax] on_retry callback error: {hook_error}")

                        if attempt < times - 1:
                            if current_delay > 0:
                                time.sleep(current_delay)
                            if backoff == "exp":
                                current_delay *= 2

                raise last_exception

            return sync_wrapper

    return decorator
