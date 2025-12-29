# Awaitable Tools

This package provides utilities for working with awaitable objects in Python.

# Coroutines vs Awaitables

## Coroutines

Objects returned from the function declared with the `async def` syntax.
It is the standard way to create asynchronous programs.

```python
async def coroutine():
    pass
```

## Awaitable

Any object that implements `__await__()` for use in an `await` expression.

```python
class Awaitable:
    def __await__(self):
        yield
```

## Installation

```bash
pip install awaitable-tools
```

While most users work with coroutines, some advanced scenarios (like
protocol implementations or framework development) require working
directly with awaitables. This package fills that gap.

## Technical Background

### The Awaitable Protocol
An object is awaitable if its `__await__()` method returns an **generator** that:

1. **Only yields `None`** (any other value raises `RuntimeError`)
2. **Final value uses `return`** (not `yield`)
3. **May use `yield from`** with other compliant generators

```python
class ValidAwaitable:
    def __await__(self):
        yield None  # Valid suspension
        # coroutine also implements __await__()
        yield from asyncio.sleep(1).__await__()
        return True

class InvalidAwaitable:
    def __await__(self):
        # Only valid if marked as @types.coroutine
        yield from asyncio.sleep(1)  # TypeError!
        yield "foo"  # RuntimeError!
```

## About async/await
[April 18, 2020, From yield to async/await](https://mleue.com/posts/yield-to-async-await/)
