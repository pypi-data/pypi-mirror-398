# Concurio

**Concurio** is a tiny `asyncio`-based concurrency pool for running many **async** callables with:

- **Concurrency limiting** via a semaphore
- **Optional rate limiting** (max executions per minute)
- **Per-task timeouts** that return a `TimeoutedTask` record (instead of raising)
- **Streaming results** as tasks complete, with optional **`tqdm` progress**

Project status: **alpha** (API may change).

## Installation

If you’ve published this package to PyPI:

```bash
pip install concurio
```

From source (this repo):

```bash
pip install -e .
```

Python: **3.8+**. Dependency: **`tqdm`**.

## Quickstart (sync entrypoint)

Use `AsyncPoolExecutor.as_events()` when you’re in a normal (non-async) script and want Concurio to manage the event loop internally.

```python
import asyncio
from concurio import AsyncPoolExecutor, TqdmConfig, TimeoutedTask


async def fetch(i: int) -> int:
    await asyncio.sleep(0.1)
    return i * 2


def main() -> None:
    results: list[int] = []
    errors: list[Exception] = []
    timeouts: list[TimeoutedTask] = []

    with AsyncPoolExecutor(concurrency=10) as pool:
        for i in range(100):
            pool.submit(fetch, i, wait_timeout=2.0)

        pool.as_events(
            on_done=results.append,
            on_error=errors.append,
            on_timeout=timeouts.append,
            tqdm_config=TqdmConfig(desc="Fetching", total=100),
        )

    print(f"done={len(results)} errors={len(errors)} timeouts={len(timeouts)}")


if __name__ == "__main__":
    main()
```

## Usage inside an async app

If you’re already in an async context (FastAPI, async CLI, notebooks, etc.), use `async_as_events()` and **do not** call `as_events()` (because `as_events()` uses `asyncio.run()` internally).

```python
import asyncio
from concurio import AsyncPoolExecutor, TqdmConfig


async def work(i: int) -> int:
    await asyncio.sleep(0.05)
    return i


async def run() -> None:
    results: list[int] = []

    pool = AsyncPoolExecutor(concurrency=25)
    for i in range(500):
        pool.submit(work, i)

    await pool.async_as_events(
        on_done=results.append,
        on_error=lambda e: print("error:", repr(e)),
        on_timeout=lambda t: print("timeout:", t),
        tqdm_config=TqdmConfig(desc="Working"),
    )

    print("results:", len(results))


asyncio.run(run())
```

## Timeouts

Concurio supports two different timeout concepts:

- **Per-task timeout** (`wait_timeout` passed to `submit()`): if the task takes too long, the result is a **`TimeoutedTask`** instance (it does *not* raise).
- **Iteration timeout** (`timeout` passed to `as_events()` / `async_as_events()`): passed to `asyncio.as_completed(...)`. If it expires, iteration may stop early (and an exception may be surfaced through `on_error`).

## Rate limiting

Limit executions to a maximum number of task starts per minute:

```python
from concurio import AsyncPoolExecutor

pool = AsyncPoolExecutor(concurrency=20, max_executions_per_minute=120)  # 2/sec average
```

This is helpful for external APIs where you want both:

- **Parallelism** (concurrency), and
- **A global request rate cap** (rate limiter).

## Progress reporting

- If `tqdm_config` is provided and stdout is a TTY, Concurio uses `tqdm.asyncio.tqdm_asyncio.as_completed(...)`.
- If stdout is *not* a TTY (e.g. CI logs), it falls back to plain `asyncio.as_completed(...)` and logs progress periodically via `logging`.

## API overview

The public imports are exposed from `concurio`:

- **`AsyncPoolExecutor(concurrency: int | None = None, max_executions_per_minute: int | None = None)`**
  - `submit(func, *args, wait_timeout: float | None = None, **kwargs) -> Awaitable`
  - `as_events(on_done, on_error, on_timeout, timeout: float | None = None, tqdm_config: TqdmConfig | None = None) -> None`
  - `async_as_events(on_done, on_error, on_timeout, timeout: float | None = None, tqdm_config: TqdmConfig | None = None) -> None`
  - `count() -> int` (also `len(pool)`)
- **`TqdmConfig(desc: str = "Processing tasks", total: int | None = None, disable: bool = False)`**
- **`TimeoutedTask`** (dataclass with `func_name`, `timeout`, `args`, `kwargs`)

## Notes / gotchas

- **Async callables only**: `submit()` expects an `async def` function (i.e. returns an awaitable). If you need to run sync work, wrap it with `asyncio.to_thread(...)` in your own async wrapper.
- **Reuse**: `AsyncPoolExecutor` collects coroutines you submit; exiting the context manager clears the internal list.

## License

Apache-2.0. See `LICENSE`.
