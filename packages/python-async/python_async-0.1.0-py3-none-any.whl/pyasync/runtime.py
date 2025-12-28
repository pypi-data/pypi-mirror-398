"""
PyAsync Runtime - Event loop, concurrency primitives, and thread-based execution.
"""

import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, Future
import heapq
from typing import Any, Coroutine, List, Optional
import threading


# Thread-local storage for event loops (one per thread)
_thread_local = threading.local()


def _get_event_loop() -> '_EventLoop':
    """Get or create an event loop for the current thread."""
    if not hasattr(_thread_local, 'loop'):
        _thread_local.loop = _EventLoop()
    return _thread_local.loop


class _EventLoop:
    """Minimal event loop for running coroutines."""
    
    def __init__(self):
        self._ready = deque()
        self._sleeping = []
    
    def run(self, coro: Coroutine) -> Any:
        """Run a coroutine to completion and return its result."""
        task = _Task(coro)
        self._ready.append(task)
        
        while not task.done:
            self._run_once()
        
        if task._exception:
            raise task._exception
        return task._result
    
    def _run_once(self):
        """Execute one iteration of the event loop."""
        # Wake up sleeping tasks
        now = time.monotonic()
        while self._sleeping and self._sleeping[0][0] <= now:
            _, task = heapq.heappop(self._sleeping)
            self._ready.append(task)
        
        # Run ready tasks
        if self._ready:
            task = self._ready.popleft()
            self._step_task(task)
        elif self._sleeping:
            # Nothing ready, wait for next sleeping task
            sleep_time = self._sleeping[0][0] - now
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _step_task(self, task: '_Task'):
        """Advance a task by one step."""
        try:
            result = task._coro.send(task._send_value)
            task._send_value = None
            
            # Handle yield values (sleep, etc.)
            if isinstance(result, tuple) and len(result) == 2:
                cmd, arg = result
                if cmd == 'sleep':
                    wake_time = time.monotonic() + arg
                    heapq.heappush(self._sleeping, (wake_time, task))
                    return
            
            # Task yielded but not done, reschedule
            self._ready.append(task)
            
        except StopIteration as e:
            task._result = e.value
            task._done = True
        except Exception as e:
            task._exception = e
            task._done = True


class _Task:
    """Wrapper for a coroutine being executed."""
    
    def __init__(self, coro: Coroutine):
        self._coro = coro
        self._result = None
        self._exception = None
        self._done = False
        self._send_value = None
    
    @property
    def done(self) -> bool:
        return self._done


class _Sleep:
    """Awaitable that pauses execution for a specified duration."""
    
    def __init__(self, seconds: float):
        self.seconds = seconds
    
    def __await__(self):
        yield ('sleep', self.seconds)


def sleep(seconds: float) -> _Sleep:
    """Pause execution for the specified number of seconds."""
    return _Sleep(seconds)


# Default thread pool for concurrent execution
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


def gather(*coros: Coroutine) -> List[Any]:
    """
    Run multiple coroutines concurrently using threads and return all results.
    
    Each coroutine runs in its own thread, providing true parallel execution
    for I/O-bound tasks.
    
    Example:
        results = gather(
            fetch("https://api1.com"),
            fetch("https://api2.com"),
            fetch("https://api3.com")
        )
        # All three requests run in parallel!
    """
    if not coros:
        return []
    
    executor = _get_executor()
    
    # Submit each coroutine to run in a separate thread
    futures = [executor.submit(_pyasync_run, coro) for coro in coros]
    
    # Collect results in order
    results = []
    exceptions = []
    
    for future in futures:
        try:
            results.append(future.result())
        except Exception as e:
            exceptions.append(e)
    
    # If any exceptions occurred, raise the first one
    if exceptions:
        raise exceptions[0]
    
    return results


class SpawnedTask:
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


def spawn(coro: Coroutine) -> SpawnedTask:
    """
    Start a coroutine running in the background.
    
    Returns a SpawnedTask that can be used to wait for the result.
    
    Example:
        task = spawn(slow_operation())
        # ... do other things ...
        result = task.result()  # Wait for completion
    """
    executor = _get_executor()
    future = executor.submit(_pyasync_run, coro)
    return SpawnedTask(future)


def _pyasync_run(coro: Coroutine) -> Any:
    """
    Execute a coroutine synchronously and return its result.
    
    This is the internal function that the AST transformer uses to wrap
    async function calls that appear in synchronous contexts.
    """
    if not hasattr(coro, 'send'):
        # Not a coroutine, return as-is
        return coro
    
    loop = _get_event_loop()
    return loop.run(coro)


class _SyncWrapper:
    """
    Wrapper that makes a synchronous value awaitable.
    
    This allows using `await` on non-coroutine values.
    """
    
    def __init__(self, value: Any):
        self._value = value
    
    def __await__(self):
        return self._value
        yield  # Makes this a generator (never reached)


def _pyasync_await(value: Any) -> Any:
    """
    Handle await on both sync and async values.
    
    If value is a coroutine/awaitable, return it as-is for await.
    If value is a regular sync value, wrap it to be awaitable.
    
    This allows code like:
        await requests.get(...)  # Works! (requests is sync)
        await async_func()       # Works! (async func)
    """
    # Check if it's already a coroutine or awaitable
    if hasattr(value, '__await__') or hasattr(value, 'send'):
        return value
    
    # Wrap sync value to make it awaitable
    return _SyncWrapper(value)
