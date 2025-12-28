"""
PyAsync - Thread and Process-based parallelism for Python.

Simple, explicit API for running tasks in parallel using threads and processes.
No magic just straightforward parallel execution.

Usage:
    import pyasync
    
    # Run I/O-bound tasks in parallel (threads)
    results = pyasync.parallel(
        lambda: requests.get("url1"),
        lambda: requests.get("url2")
    )
    
    # Run CPU-bound tasks in parallel (processes)
    from functools import partial
    results = pyasync.cpu_parallel(
        partial(heavy_compute, 1000000),
        partial(heavy_compute, 2000000)
    )
    
    # Background tasks with fine-grained control
    task = pyasync.cpu_background(partial(slow_compute, n))
    result = task.result(timeout=30.0)
"""

from .runtime import (
    # Thread-based (I/O-bound)
    parallel,
    background,
    run,
    Task,
    # Process-based (CPU-bound)
    cpu_parallel,
    cpu_background,
    cpu_run,
    CpuTask,
    CpuExecutor,
)

__all__ = [
    # Thread-based (I/O-bound)
    'parallel',
    'background', 
    'run',
    'Task',
    # Process-based (CPU-bound)
    'cpu_parallel',
    'cpu_background',
    'cpu_run',
    'CpuTask',
    'CpuExecutor',
]
__version__ = '0.3.0'

