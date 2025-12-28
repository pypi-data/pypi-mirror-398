"""
PyAsync - Thread-based parallelism for Python.

Simple, explicit API for running tasks in parallel using threads.
"""

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, List, Optional
import threading


# Global thread pool
_executor: Optional[ThreadPoolExecutor] = None
_executor_lock = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    """Get or create the global thread pool executor."""
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = ThreadPoolExecutor(max_workers=32)
    return _executor


def parallel(*callables: Callable[[], Any]) -> List[Any]:
    """
    Run multiple callables in parallel threads.
    
    Each callable runs in its own thread. Results are returned
    in the same order as the input callables.
    
    Example:
        results = parallel(
            lambda: requests.get("https://api1.com"),
            lambda: requests.get("https://api2.com"),
            lambda: requests.get("https://api3.com")
        )
        # All 3 requests run in parallel!
    
    Args:
        *callables: Functions to run in parallel (no arguments)
    
    Returns:
        List of results in order
    """
    if not callables:
        return []
    
    executor = _get_executor()
    futures = [executor.submit(fn) for fn in callables]
    
    results = []
    exceptions = []
    
    for future in futures:
        try:
            results.append(future.result())
        except Exception as e:
            exceptions.append(e)
    
    if exceptions:
        raise exceptions[0]
    
    return results


class Task:
    """
    A task running in the background.
    
    Use .result() to wait for and get the result.
    Use .done to check if the task has completed.
    """
    
    def __init__(self, future: Future):
        self._future = future
    
    @property
    def done(self) -> bool:
        """Check if the task has completed."""
        return self._future.done()
    
    def result(self, timeout: Optional[float] = None) -> Any:
        """Wait for and return the task result."""
        return self._future.result(timeout=timeout)
    
    def cancel(self) -> bool:
        """Attempt to cancel the task."""
        return self._future.cancel()


def background(fn: Callable[[], Any]) -> Task:
    """
    Start a callable running in the background.
    
    Returns a Task that can be used to wait for the result.
    
    Example:
        task = background(lambda: slow_operation())
        print("Doing other work...")
        result = task.result()  # Wait for completion
    
    Args:
        fn: Function to run in background (no arguments)
    
    Returns:
        Task object
    """
    executor = _get_executor()
    future = executor.submit(fn)
    return Task(future)


def run(fn: Callable[[], Any]) -> Any:
    """
    Run a callable in the thread pool and wait for result.
    
    Useful for running a single blocking operation without
    blocking the main thread in certain contexts.
    
    Example:
        result = run(lambda: requests.get("https://api.com"))
    
    Args:
        fn: Function to run (no arguments)
    
    Returns:
        Result of the callable
    """
    executor = _get_executor()
    return executor.submit(fn).result()
