# retrymax

Tiny retry decorator for Python, works for **sync and async functions**, with optional verbose output and callback hooks.

---

## Installation

```bash
pip install retrymax
```

---

## Features

* Retry synchronous or asynchronous functions
* Optional exponential backoff
* Optional verbose output to see retry attempts
* Optional callback hook for custom actions on retry
* Safe handling of exceptions, only retries specified exceptions

---

## Usage

### Synchronous example

```python
from retrymax import retry

@retry(times=3, delay=1, verbose=True)
def fetch_data():
    print("Trying to fetch data...")
    raise ValueError("Failed!")

try:
    fetch_data()
except ValueError:
    print("All retries failed!")
```

**Output:**

```
Trying to fetch data...
[retrymax] Attempt 1 failed: Failed!
Trying to fetch data...
[retrymax] Attempt 2 failed: Failed!
Trying to fetch data...
[retrymax] Attempt 3 failed: Failed!
All retries failed!
```

---

### Asynchronous example

```python
import asyncio
from retrymax import retry

@retry(times=3, delay=0.5, verbose=True)
async def fetch_async():
    print("Trying async fetch...")
    raise ValueError("Async fail!")

async def main():
    try:
        await fetch_async()
    except ValueError:
        print("All async retries failed!")

asyncio.run(main())
```

**Output:**

```
Trying async fetch...
[retrymax] Attempt 1 failed: Async fail!
Trying async fetch...
[retrymax] Attempt 2 failed: Async fail!
Trying async fetch...
[retrymax] Attempt 3 failed: Async fail!
All async retries failed!
```

---

### Using a callback hook

```python
from retrymax import retry

def my_callback(exception, attempt):
    print(f"[callback] Retry {attempt} failed: {exception}")

@retry(times=3, delay=0.5, verbose=True, on_retry=my_callback)
def fetch_with_callback():
    print("Attempting fetch with callback...")
    raise ValueError("Failed again!")

try:
    fetch_with_callback()
except ValueError:
    print("All retries failed with callback!")
```

**Output:**

```
Attempting fetch with callback...
[retrymax] Attempt 1 failed: Failed again!
[callback] Retry 1 failed: Failed again!
Attempting fetch with callback...
[retrymax] Attempt 2 failed: Failed again!
[callback] Retry 2 failed: Failed again!
Attempting fetch with callback...
[retrymax] Attempt 3 failed: Failed again!
[callback] Retry 3 failed: Failed again!
All retries failed with callback!
```

---

## Parameters

* `times` (int): Number of retry attempts (default: 3)
* `delay` (float): Delay between retries in seconds (default: 0)
* `backoff` (str or None): `"exp"` for exponential backoff (default: None)
* `exceptions` (tuple): Exceptions to catch and retry (default: `(Exception,)`)
* `verbose` (bool): Print retry attempts (default: False)
* `on_retry` (callable): Optional callback called on each retry with `(exception, attempt)`

---

## License

MIT License

---

## Notes

* Works with Python 3.8+
* Supports both synchronous and asynchronous functions
* Safe and consistent retry behavior
* Perfect for network calls, flaky APIs, or any operation that may fail intermittently
