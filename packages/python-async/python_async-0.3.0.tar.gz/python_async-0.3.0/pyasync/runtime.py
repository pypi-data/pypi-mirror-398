"""
PyAsync - Thread and Process-based parallelism for Python.

Simple, explicit API for running tasks in parallel using threads and processes.
Threads for I/O-bound tasks, processes for CPU-bound tasks.
"""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from typing import Callable, Any, List, Optional, Iterator
import threading
import multiprocessing
import os


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


# =============================================================================
# CPU-BOUND TASK HANDLING (ProcessPoolExecutor)
# =============================================================================

# Global process pool
_cpu_executor: Optional[ProcessPoolExecutor] = None
_cpu_executor_lock = threading.Lock()


def _get_cpu_executor(max_workers: Optional[int] = None) -> ProcessPoolExecutor:
    """Get or create the global process pool executor."""
    global _cpu_executor
    if _cpu_executor is None:
        with _cpu_executor_lock:
            if _cpu_executor is None:
                workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
                _cpu_executor = ProcessPoolExecutor(max_workers=workers)
    return _cpu_executor


class CpuTask:
    """
    A CPU-bound task running in a separate process.
    
    Provides fine-grained control over task execution including
    status monitoring, timeouts, and cancellation.
    
    Example:
        task = cpu_background(partial(heavy_compute, 1000000))
        
        while not task.done:
            print("Still computing...")
            time.sleep(0.5)
        
        try:
            result = task.result(timeout=10.0)
        except TimeoutError:
            task.cancel()
    """
    
    def __init__(self, future: Future):
        self._future = future
    
    @property
    def done(self) -> bool:
        """Check if the task has completed (successfully or with error)."""
        return self._future.done()
    
    @property
    def running(self) -> bool:
        """Check if the task is currently running."""
        return self._future.running()
    
    @property
    def cancelled(self) -> bool:
        """Check if the task was cancelled."""
        return self._future.cancelled()
    
    def result(self, timeout: Optional[float] = None) -> Any:
        """
        Wait for and return the task result.
        
        Args:
            timeout: Maximum seconds to wait. None means wait forever.
        
        Returns:
            The result of the callable.
        
        Raises:
            TimeoutError: If timeout expires before task completes.
            Exception: Any exception raised by the callable.
        """
        return self._future.result(timeout=timeout)
    
    def exception(self, timeout: Optional[float] = None) -> Optional[Exception]:
        """
        Return the exception raised by the task, if any.
        
        Args:
            timeout: Maximum seconds to wait. None means wait forever.
        
        Returns:
            The exception, or None if task completed successfully.
        
        Raises:
            TimeoutError: If timeout expires before task completes.
        """
        return self._future.exception(timeout=timeout)
    
    def cancel(self) -> bool:
        """
        Attempt to cancel the task.
        
        Returns True if the task was successfully cancelled.
        Returns False if the task has already started or completed.
        
        Note: Once a task is running in a process, it cannot be cancelled
        through this method. Use CpuExecutor for more control.
        """
        return self._future.cancel()
    
    def add_done_callback(self, fn: Callable[['CpuTask'], None]) -> None:
        """
        Add a callback to be called when the task completes.
        
        Args:
            fn: Callback function that receives this CpuTask.
        """
        self._future.add_done_callback(lambda f: fn(self))


class CpuExecutor:
    """
    Context manager for CPU-bound task execution with full control.
    
    Use this when you need fine-grained control over the process pool,
    including custom worker count, initializers, and shutdown behavior.
    
    Example:
        with CpuExecutor(max_workers=4, timeout=30.0) as executor:
            task1 = executor.submit(heavy_compute, 1000000)
            task2 = executor.submit(heavy_compute, 2000000)
            
            print(task1.result())
            print(task2.result())
    """
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        timeout: Optional[float] = None,
        initializer: Optional[Callable[[], None]] = None,
        initargs: tuple = ()
    ):
        """
        Initialize the CPU executor.
        
        Args:
            max_workers: Maximum number of processes. Defaults to CPU count.
            timeout: Default timeout for all tasks (can be overridden per-task).
            initializer: Function called at the start of each worker process.
            initargs: Arguments to pass to the initializer.
        """
        self._max_workers = max_workers or (os.cpu_count() or 1)
        self._default_timeout = timeout
        self._initializer = initializer
        self._initargs = initargs
        self._executor: Optional[ProcessPoolExecutor] = None
        self._tasks: List[CpuTask] = []
    
    def __enter__(self) -> 'CpuExecutor':
        self._executor = ProcessPoolExecutor(
            max_workers=self._max_workers,
            initializer=self._initializer,
            initargs=self._initargs
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._executor:
            # Cancel pending tasks on exception
            cancel_futures = exc_type is not None
            self._executor.shutdown(wait=True, cancel_futures=cancel_futures)
            self._executor = None
        return False
    
    def submit(self, fn: Callable, *args, **kwargs) -> CpuTask:
        """
        Submit a callable to be executed in a separate process.
        
        Args:
            fn: Function to execute (must be picklable).
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
        
        Returns:
            CpuTask for monitoring and result retrieval.
        """
        if self._executor is None:
            raise RuntimeError("CpuExecutor not entered. Use 'with' statement.")
        
        future = self._executor.submit(fn, *args, **kwargs)
        task = CpuTask(future)
        self._tasks.append(task)
        return task
    
    def map(
        self,
        fn: Callable,
        *iterables,
        timeout: Optional[float] = None,
        chunksize: int = 1
    ) -> Iterator[Any]:
        """
        Map a function over iterables in parallel processes.
        
        Args:
            fn: Function to apply to each element.
            *iterables: Iterables of arguments.
            timeout: Maximum seconds for entire operation.
            chunksize: Number of items per process batch.
        
        Returns:
            Iterator of results in order.
        
        Raises:
            TimeoutError: If timeout expires.
        """
        if self._executor is None:
            raise RuntimeError("CpuExecutor not entered. Use 'with' statement.")
        
        effective_timeout = timeout or self._default_timeout
        return self._executor.map(fn, *iterables, timeout=effective_timeout, chunksize=chunksize)
    
    @property
    def tasks(self) -> List[CpuTask]:
        """Return list of all submitted tasks."""
        return self._tasks.copy()
    
    def wait_all(self, timeout: Optional[float] = None) -> List[Any]:
        """
        Wait for all submitted tasks and return their results.
        
        Args:
            timeout: Maximum seconds to wait for all tasks.
        
        Returns:
            List of results in submission order.
        
        Raises:
            TimeoutError: If timeout expires.
        """
        effective_timeout = timeout or self._default_timeout
        return [task.result(timeout=effective_timeout) for task in self._tasks]


def cpu_parallel(
    *callables: Callable[[], Any],
    timeout: Optional[float] = None,
    max_workers: Optional[int] = None
) -> List[Any]:
    """
    Run multiple callables in parallel processes.
    
    Each callable runs in its own process, providing true parallelism
    for CPU-bound tasks (bypasses the GIL).
    
    Note: Callables must be picklable. Use functools.partial for 
    functions with arguments instead of lambdas.
    
    Example:
        from functools import partial
        
        def compute(n):
            return sum(i * i for i in range(n))
        
        results = cpu_parallel(
            partial(compute, 1000000),
            partial(compute, 2000000),
            partial(compute, 3000000),
            timeout=10.0
        )
    
    Args:
        *callables: Functions to run in parallel (no arguments).
        timeout: Maximum seconds to wait. None means wait forever.
        max_workers: Maximum processes to use. Defaults to CPU count.
    
    Returns:
        List of results in order.
    
    Raises:
        TimeoutError: If timeout expires before all tasks complete.
    """
    if not callables:
        return []
    
    workers = max_workers or min(len(callables), os.cpu_count() or 1)
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fn) for fn in callables]
        
        results = []
        exceptions = []
        
        for future in futures:
            try:
                results.append(future.result(timeout=timeout))
            except Exception as e:
                exceptions.append(e)
        
        if exceptions:
            raise exceptions[0]
        
        return results


def cpu_background(fn: Callable[[], Any]) -> CpuTask:
    """
    Start a callable running in a background process.
    
    Returns a CpuTask with fine-grained control for monitoring,
    timeouts, and cancellation.
    
    Note: The callable must be picklable. Use functools.partial
    for functions with arguments instead of lambdas.
    
    Example:
        from functools import partial
        
        def heavy_compute(n):
            return sum(i * i for i in range(n))
        
        task = cpu_background(partial(heavy_compute, 100000000))
        
        # Check status
        print(f"Running: {task.running}")
        
        # Wait with timeout
        try:
            result = task.result(timeout=30.0)
        except TimeoutError:
            print("Task took too long!")
    
    Args:
        fn: Function to run in background process (no arguments).
    
    Returns:
        CpuTask object for monitoring and control.
    """
    executor = _get_cpu_executor()
    future = executor.submit(fn)
    return CpuTask(future)


def cpu_run(fn: Callable[[], Any], timeout: Optional[float] = None) -> Any:
    """
    Run a callable in a separate process and wait for result.
    
    Useful for running a single CPU-intensive operation with
    true parallelism (bypasses the GIL).
    
    Note: The callable must be picklable. Use functools.partial
    for functions with arguments instead of lambdas.
    
    Example:
        from functools import partial
        
        def compute(n):
            return sum(i * i for i in range(n))
        
        # With timeout
        try:
            result = cpu_run(partial(compute, 100000000), timeout=10.0)
        except TimeoutError:
            print("Computation took too long!")
    
    Args:
        fn: Function to run (no arguments).
        timeout: Maximum seconds to wait. None means wait forever.
    
    Returns:
        Result of the callable.
    
    Raises:
        TimeoutError: If timeout expires before completion.
    """
    executor = _get_cpu_executor()
    return executor.submit(fn).result(timeout=timeout)

