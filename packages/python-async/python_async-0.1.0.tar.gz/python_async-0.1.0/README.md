# PyAsync

A **minimalist Python library** for async execution. No event loops, no complex setup - just simple, elegant and intuitive Python code. As Python is intended to be 😉

## Why?

I was tired of writing wrappers for my async functions, so I created this library to make async execution transparent. I don't want to handle the event loop, I don't my code to be a mess, I am a Pythonista, I just want to execute my async functions and get the result. 😜

## Installation

```bash
git clone https://github.com/marciobbj/pyasync.git
cd pyasync
pip install -e .
```

## Quick Start

```python
import pyasync

async def fetch_data():
    await pyasync.sleep(1)
    return {"message": "Hello, World!"}

# No wrapper needed! Just call it directly.
data = fetch_data()
print(data)  # {'message': 'Hello, World!'}
```

## Using with Sync Libraries

`await` works on **any** expression, not just coroutines:

```python
import pyasync
import requests  # sync library!

async def get_user():
    response = await requests.get("https://api.github.com/users/marciobbj")
    return response.json()

user = get_user()
print(user["login"])  # marciobbj
```

## Real Concurrency

PyAsync provides **real parallel execution** using threads:

```python
import pyasync
import requests

async def fetch(url):
    response = await requests.get(url)
    return response.status_code

# All 3 requests run in PARALLEL!
results = pyasync.gather(
    fetch("https://httpbin.org/delay/1"),
    fetch("https://httpbin.org/delay/1"),
    fetch("https://httpbin.org/delay/1")
)
# Takes ~1 second, not ~3 seconds!
```

### Web Scraping Example

```
$ python examples/web_scraping.py

Scraping 5 URLs in parallel...

URL                            Status   Size         Time    
------------------------------------------------------------
google.com                     200      18185        0.22s
github.com                     200      562266       0.17s
python.org                     200      49639        0.08s
wikipedia.org                  403      126          0.07s
httpbin.org/get                200      307          0.69s

Total time:                    0.69s
Sequential would take:         1.23s
Speedup:                       1.8x faster
```

### Background Tasks

```python
import pyasync

async def slow_operation():
    await pyasync.sleep(5)
    return "done!"

# Start in background
task = pyasync.spawn(slow_operation())

# Do other things while it runs...
print("Working...")

# Get result when ready
result = task.result()
```

## API

| Function | Description |
|----------|-------------|
| `gather(*coros)` | Run tasks in parallel, return list of results |
| `spawn(coro)` | Start task in background, return Task handle |
| `sleep(seconds)` | Pause execution |

## How It Works

1. **Import Hook** - Intercepts module loading
2. **AST Transformation** - Transforms async calls automatically
3. **ThreadPoolExecutor** - Powers real parallel execution

```
gather(task1, task2, task3)
         │       │       │
         ▼       ▼       ▼
    [Thread1][Thread2][Thread3]
         │       │       │
         └───────┴───────┘
                 │
         Collect Results
```

## Examples

See the `examples/` directory:
- `simple_async.py` - Basic async function
- `simple_async_http.py` - HTTP request with requests
- `simple_concurrent_requests.py` - Parallel HTTP requests
- `background_tasks.py` - spawn() for background work
- `web_scraping.py` - Parallel web scraping
- `multiple_api_calls.py` - Parallel API calls
- `parallel_file_processing.py` - File processing
- `mixing_sync_async.py` - Mix sync and async code

## Testing

Run all unit tests:

```bash
python -m unittest discover -s tests -v
```

Test files:
- `test_runtime.py` - Runtime, gather, spawn
- `test_transformer.py` - AST transformations
- `test_hook.py` - Import hooks

## Limitations

- Requires `import pyasync` at top of file
- Thread-based (good for I/O, not for thousands of connections)
- Only transforms user code, not third-party packages

## License

MIT
