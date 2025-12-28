# PyAsync

**Thread and Process-based parallelism for Python.** Simple, explicit API for running tasks in parallel.

- **Threads** for I/O-bound tasks (HTTP requests, file operations)
- **Processes** for CPU-bound tasks (computations, data processing)

No magic, just straightforward parallel execution.

## Installation

```bash
pip install python-async
```

## Quick Start

### I/O-Bound Tasks (Threads)

```python
import pyasync
import requests

def fetch(url):
    return requests.get(url).json()

# Run 3 requests in parallel - takes ~1 second, not ~3 seconds!
results = pyasync.parallel(
    lambda: fetch("https://api.example.com/users/1"),
    lambda: fetch("https://api.example.com/users/2"),
    lambda: fetch("https://api.example.com/users/3")
)
```

### CPU-Bound Tasks (Processes)

```python
import pyasync
from functools import partial

def heavy_compute(n):
    return sum(i * i for i in range(n))

# Run computations in parallel processes (bypasses GIL)
results = pyasync.cpu_parallel(
    partial(heavy_compute, 10_000_000),
    partial(heavy_compute, 20_000_000),
    partial(heavy_compute, 30_000_000),
    timeout=10.0  # Optional timeout
)
```

## API

### Thread-Based (I/O-Bound)

#### `parallel(*callables)`

Run multiple functions in parallel threads. Returns results in order.

```python
results = pyasync.parallel(
    lambda: requests.get("https://api1.com"),
    lambda: requests.get("https://api2.com"),
    lambda: requests.get("https://api3.com")
)
# All 3 run simultaneously!
```

#### `background(callable)`

Start a function in the background. Returns a Task.

```python
task = pyasync.background(lambda: slow_operation())

# Do other work while it runs...
print("Working...")

# Get result when ready
result = task.result()
```

#### `run(callable)`

Run a single function in the thread pool.

```python
result = pyasync.run(lambda: requests.get("https://api.com"))
```

---

### Process-Based (CPU-Bound)

> **Note:** Functions must be picklable. Use `functools.partial` instead of lambdas.

#### `cpu_parallel(*callables, timeout=None, max_workers=None)`

Run multiple functions in parallel processes with true parallelism.

```python
from functools import partial

def compute(n):
    return sum(i * i for i in range(n))

results = pyasync.cpu_parallel(
    partial(compute, 1_000_000),
    partial(compute, 2_000_000),
    partial(compute, 3_000_000),
    timeout=10.0,    # TimeoutError if exceeded
    max_workers=4    # Limit processes
)
```

#### `cpu_background(callable)`

Start a function in a background process. Returns a `CpuTask` with fine-grained control.

```python
task = pyasync.cpu_background(partial(heavy_compute, 100_000_000))

# Monitor status
print(f"Running: {task.running}")
print(f"Done: {task.done}")

# Wait with timeout
try:
    result = task.result(timeout=30.0)
except TimeoutError:
    print("Task took too long!")
    task.cancel()
```

#### `cpu_run(callable, timeout=None)`

Run a single function in a separate process and wait for result.

```python
try:
    result = pyasync.cpu_run(partial(compute, 100_000_000), timeout=10.0)
except TimeoutError:
    print("Computation took too long!")
```

---

### CpuTask Class

`CpuTask` provides fine-grained control over CPU-bound tasks:

| Property/Method | Description |
|-----------------|-------------|
| `.done` | `True` if task completed |
| `.running` | `True` if task is currently running |
| `.cancelled` | `True` if task was cancelled |
| `.result(timeout=None)` | Wait and get result (raises `TimeoutError`) |
| `.exception(timeout=None)` | Get exception if task failed |
| `.cancel()` | Attempt to cancel (only works if not started) |
| `.add_done_callback(fn)` | Add completion callback |

---

### CpuExecutor Context Manager

For advanced control over process pools:

```python
with pyasync.CpuExecutor(max_workers=4, timeout=30.0) as executor:
    # Submit individual tasks
    task1 = executor.submit(compute, 1_000_000)
    task2 = executor.submit(compute, 2_000_000)
    
    # Get results
    print(task1.result())
    print(task2.result())
    
    # Or wait for all
    results = executor.wait_all()
    
    # Batch processing with map
    results = list(executor.map(compute, [1_000_000, 2_000_000, 3_000_000]))
```

## Examples

### Parallel Tasks (Threads)

```
$ python examples/simple_parallel.py

=== Simple Parallel Tasks ===

[Task A] Starting...
[Task B] Starting...
[Task C] Starting...
[Task A] Done!
[Task C] Done!
[Task B] Done!

Results: ['Task A completed', 'Task B completed', 'Task C completed']
Total time: 2.01s (longest task was 2s)
```

### CPU-Bound Parallel Tasks (Processes)

```
$ python examples/cpu_parallel_tasks.py

============================================================
CPU-Bound Parallel Tasks Example
============================================================

1. Parallel Prime Counting
----------------------------------------
Ranges: [(1, 50000), (50000, 100000), (100000, 150000), (150000, 200000)]
Primes found: [5133, 4459, 4256, 4136]
Total primes: 17984

Sequential time: 0.11s
Parallel time:   0.10s
Speedup:         1.1x

2. Background Task with Monitoring
----------------------------------------
Task started...
  done: False
  cancelled: False

Task completed!
  done: True
  result: 9592 primes found
```

### Parallel API Calls

```
$ python examples/parallel_api_calls.py

=== Parallel API Calls ===

Fetching 3 users in parallel...
  - Leanne Graham (Sincere@april.biz)
  - Ervin Howell (Shanna@melissa.tv)
  - Clementine Bauch (Nathan@yesenia.net)
```

## When to Use

| Use Case | Function | Why |
|----------|----------|-----|
| Multiple HTTP requests | `parallel()` | I/O-bound, threads work great |
| File operations | `parallel()` | I/O-bound |
| Data processing | `cpu_parallel()` | CPU-bound, needs true parallelism |
| Image/video processing | `cpu_parallel()` | CPU-bound |
| Long computation with timeout | `cpu_run(fn, timeout=10)` | Fine-grained control |
| Background computation | `cpu_background()` | Monitor and cancel if needed |

## Testing

```bash
python -m unittest discover -s tests -v
```

## License

MIT

