"""
PyAsync - Thread-based parallelism for Python.

Simple, explicit API for running tasks in parallel using threads.
No magic, no hijacking - just straightforward parallel execution.

Usage:
    import pyasync
    
    # Run in parallel
    results = pyasync.parallel(
        lambda: requests.get("url1"),
        lambda: requests.get("url2")
    )
    
    # Background task
    task = pyasync.background(lambda: slow_op())
    result = task.result()
"""

from .runtime import parallel, background, run, Task

__all__ = ['parallel', 'background', 'run', 'Task']
__version__ = '0.2.0'
