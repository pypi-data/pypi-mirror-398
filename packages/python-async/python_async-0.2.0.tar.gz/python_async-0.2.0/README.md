# PyAsync

**Thread-based parallelism for Python.** Simple, explicit API for running tasks in parallel.

No magic, just straightforward parallel execution using threads.

## Installation

```bash
pip install python-async
```

## Quick Start

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

## API

### `parallel(*callables)`

Run multiple functions in parallel threads. Returns results in order.

```python
results = pyasync.parallel(
    lambda: requests.get("https://api1.com"),
    lambda: requests.get("https://api2.com"),
    lambda: requests.get("https://api3.com")
)
# All 3 run simultaneously!
```

### `background(callable)`

Start a function in the background. Returns a Task.

```python
task = pyasync.background(lambda: slow_operation())

# Do other work while it runs...
print("Working...")

# Get result when ready
result = task.result()
```

### `run(callable)`

Run a single function in the thread pool.

```python
result = pyasync.run(lambda: requests.get("https://api.com"))
```

## Examples

### Parallel Tasks

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

### Parallel API Calls

```
$ python examples/parallel_api_calls.py

=== Parallel API Calls ===

Fetching 3 users in parallel...
  - Leanne Graham (Sincere@april.biz)
  - Ervin Howell (Shanna@melissa.tv)
  - Clementine Bauch (Nathan@yesenia.net)

Fetching posts for each user...
  - Leanne Graham: 10 posts
  - Ervin Howell: 10 posts
  - Clementine Bauch: 10 posts
```

### Parallel File Processing

```
$ python examples/parallel_files.py

=== Parallel File Processing ===

Processing 2 files in parallel...

File                 Size       Hash      
----------------------------------------
__init__.py          587        8c137857  
runtime.py           3363       0bca3ba5
```

### Web Scraping

```
$ python examples/web_scraping.py

Scraping 5 URLs in parallel...

Total time:                    0.69s
Sequential would take:         1.23s
Speedup:                       1.8x faster
```

## When to Use

**Good for:**
- Scripts making multiple HTTP requests
- Batch processing I/O operations
- Parallel file operations

**Not for:**
- Thousands of concurrent connections (use asyncio)
- CPU-bound tasks (use multiprocessing)

## Testing

```bash
python -m unittest discover -s tests -v
```

## License

MIT
