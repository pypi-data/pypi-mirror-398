"""Unit tests for pyasync.runtime module (v2)."""

import unittest
import time
import threading


class TestParallel(unittest.TestCase):
    """Tests for parallel() function."""
    
    def test_empty(self):
        """Test parallel with no arguments."""
        from pyasync import parallel
        
        results = parallel()
        self.assertEqual(results, [])
    
    def test_single(self):
        """Test parallel with single callable."""
        from pyasync import parallel
        
        results = parallel(lambda: 42)
        self.assertEqual(results, [42])
    
    def test_multiple(self):
        """Test parallel with multiple callables."""
        from pyasync import parallel
        
        results = parallel(
            lambda: 1,
            lambda: 2,
            lambda: 3
        )
        self.assertEqual(results, [1, 2, 3])
    
    def test_parallel_execution(self):
        """Test that parallel runs callables concurrently."""
        from pyasync import parallel
        
        def slow_task(n):
            time.sleep(0.2)
            return n
        
        start = time.monotonic()
        results = parallel(
            lambda: slow_task(1),
            lambda: slow_task(2),
            lambda: slow_task(3)
        )
        elapsed = time.monotonic() - start
        
        self.assertEqual(results, [1, 2, 3])
        self.assertLess(elapsed, 0.5)  # Should be ~0.2s, not ~0.6s
    
    def test_preserves_order(self):
        """Test that parallel preserves result order."""
        from pyasync import parallel
        
        def task(n, delay):
            time.sleep(delay)
            return n
        
        results = parallel(
            lambda: task(1, 0.2),
            lambda: task(2, 0.1),
            lambda: task(3, 0.05)
        )
        
        self.assertEqual(results, [1, 2, 3])
    
    def test_exception_propagation(self):
        """Test that exceptions are propagated."""
        from pyasync import parallel
        
        def failing():
            raise ValueError("test error")
        
        with self.assertRaises(ValueError):
            parallel(lambda: 1, failing)


class TestBackground(unittest.TestCase):
    """Tests for background() function."""
    
    def test_basic(self):
        """Test basic background functionality."""
        from pyasync import background
        
        task = background(lambda: 42)
        result = task.result()
        
        self.assertEqual(result, 42)
        self.assertTrue(task.done)
    
    def test_runs_in_background(self):
        """Test that background runs task concurrently."""
        from pyasync import background
        
        results = []
        
        def bg_task():
            time.sleep(0.1)
            results.append("background")
            return "done"
        
        task = background(bg_task)
        results.append("main_before")
        
        task.result()
        results.append("main_after")
        
        self.assertEqual(results, ["main_before", "background", "main_after"])
    
    def test_exception_propagation(self):
        """Test that exceptions are propagated."""
        from pyasync import background
        
        def failing():
            raise RuntimeError("task failed")
        
        task = background(failing)
        
        with self.assertRaises(RuntimeError):
            task.result()


class TestRun(unittest.TestCase):
    """Tests for run() function."""
    
    def test_basic(self):
        """Test basic run functionality."""
        from pyasync import run
        
        result = run(lambda: 42)
        self.assertEqual(result, 42)
    
    def test_with_complex_return(self):
        """Test run with complex return value."""
        from pyasync import run
        
        result = run(lambda: {"key": "value", "list": [1, 2, 3]})
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["list"], [1, 2, 3])


# =============================================================================
# CPU-BOUND TASK TESTS
# =============================================================================

# Helper functions for CPU tests (must be module-level for pickling)
def _cpu_compute(n):
    """CPU-intensive computation for testing."""
    return sum(i * i for i in range(n))


def _cpu_slow_task(delay, result):
    """Slow task that returns after delay."""
    import time
    time.sleep(delay)
    return result


def _cpu_failing_task():
    """Task that raises an exception."""
    raise ValueError("CPU task failed")


def _cpu_return_dict(n):
    """Return a dict with computed values."""
    return {"sum": sum(range(n)), "count": n}


class TestCpuParallel(unittest.TestCase):
    """Tests for cpu_parallel() function."""
    
    def test_empty(self):
        """Test cpu_parallel with no arguments."""
        from pyasync import cpu_parallel
        
        results = cpu_parallel()
        self.assertEqual(results, [])
    
    def test_single(self):
        """Test cpu_parallel with single callable."""
        from pyasync import cpu_parallel
        from functools import partial
        
        results = cpu_parallel(partial(_cpu_compute, 1000))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], sum(i * i for i in range(1000)))
    
    def test_multiple(self):
        """Test cpu_parallel with multiple callables."""
        from pyasync import cpu_parallel
        from functools import partial
        
        results = cpu_parallel(
            partial(_cpu_compute, 100),
            partial(_cpu_compute, 200),
            partial(_cpu_compute, 300)
        )
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], sum(i * i for i in range(100)))
        self.assertEqual(results[1], sum(i * i for i in range(200)))
        self.assertEqual(results[2], sum(i * i for i in range(300)))
    
    def test_preserves_order(self):
        """Test that cpu_parallel preserves result order."""
        from pyasync import cpu_parallel
        from functools import partial
        
        results = cpu_parallel(
            partial(_cpu_slow_task, 0.2, 1),
            partial(_cpu_slow_task, 0.1, 2),
            partial(_cpu_slow_task, 0.05, 3)
        )
        
        self.assertEqual(results, [1, 2, 3])
    
    def test_exception_propagation(self):
        """Test that exceptions are propagated."""
        from pyasync import cpu_parallel
        from functools import partial
        
        with self.assertRaises(ValueError):
            cpu_parallel(partial(_cpu_compute, 100), _cpu_failing_task)
    
    def test_timeout(self):
        """Test cpu_parallel with timeout."""
        from pyasync import cpu_parallel
        from functools import partial
        
        with self.assertRaises(TimeoutError):
            cpu_parallel(
                partial(_cpu_slow_task, 5.0, "slow"),
                timeout=0.1
            )
    
    def test_max_workers(self):
        """Test cpu_parallel with custom max_workers."""
        from pyasync import cpu_parallel
        from functools import partial
        
        results = cpu_parallel(
            partial(_cpu_compute, 100),
            partial(_cpu_compute, 200),
            max_workers=1
        )
        
        self.assertEqual(len(results), 2)


class TestCpuBackground(unittest.TestCase):
    """Tests for cpu_background() function."""
    
    def test_basic(self):
        """Test basic cpu_background functionality."""
        from pyasync import cpu_background
        from functools import partial
        
        task = cpu_background(partial(_cpu_compute, 1000))
        result = task.result()
        
        self.assertEqual(result, sum(i * i for i in range(1000)))
        self.assertTrue(task.done)
    
    def test_returns_cpu_task(self):
        """Test that cpu_background returns CpuTask."""
        from pyasync import cpu_background, CpuTask
        from functools import partial
        
        task = cpu_background(partial(_cpu_compute, 100))
        self.assertIsInstance(task, CpuTask)
        task.result()  # Wait for completion
    
    def test_exception_propagation(self):
        """Test that exceptions are propagated."""
        from pyasync import cpu_background
        
        task = cpu_background(_cpu_failing_task)
        
        with self.assertRaises(ValueError):
            task.result()
    
    def test_timeout(self):
        """Test cpu_background with result timeout."""
        from pyasync import cpu_background
        from functools import partial
        
        task = cpu_background(partial(_cpu_slow_task, 5.0, "slow"))
        
        with self.assertRaises(TimeoutError):
            task.result(timeout=0.1)


class TestCpuRun(unittest.TestCase):
    """Tests for cpu_run() function."""
    
    def test_basic(self):
        """Test basic cpu_run functionality."""
        from pyasync import cpu_run
        from functools import partial
        
        result = cpu_run(partial(_cpu_compute, 1000))
        self.assertEqual(result, sum(i * i for i in range(1000)))
    
    def test_with_complex_return(self):
        """Test cpu_run with complex return value."""
        from pyasync import cpu_run
        from functools import partial
        
        result = cpu_run(partial(_cpu_return_dict, 100))
        self.assertEqual(result["sum"], sum(range(100)))
        self.assertEqual(result["count"], 100)
    
    def test_timeout(self):
        """Test cpu_run with timeout."""
        from pyasync import cpu_run
        from functools import partial
        
        with self.assertRaises(TimeoutError):
            cpu_run(partial(_cpu_slow_task, 5.0, "slow"), timeout=0.1)


class TestCpuTask(unittest.TestCase):
    """Tests for CpuTask class."""
    
    def test_done_property(self):
        """Test done property."""
        from pyasync import cpu_background
        from functools import partial
        
        task = cpu_background(partial(_cpu_compute, 100))
        task.result()  # Wait for completion
        
        self.assertTrue(task.done)
    
    def test_cancelled_property(self):
        """Test cancelled property."""
        from pyasync import cpu_background
        from functools import partial
        
        task = cpu_background(partial(_cpu_compute, 100))
        task.result()
        
        self.assertFalse(task.cancelled)
    
    def test_exception_method(self):
        """Test exception method."""
        from pyasync import cpu_background
        
        task = cpu_background(_cpu_failing_task)
        
        # Wait for completion
        try:
            task.result()
        except ValueError:
            pass
        
        exception = task.exception()
        self.assertIsInstance(exception, ValueError)


class TestCpuExecutor(unittest.TestCase):
    """Tests for CpuExecutor context manager."""
    
    def test_basic_usage(self):
        """Test basic CpuExecutor usage."""
        from pyasync import CpuExecutor
        
        with CpuExecutor(max_workers=2) as executor:
            task1 = executor.submit(_cpu_compute, 100)
            task2 = executor.submit(_cpu_compute, 200)
            
            self.assertEqual(task1.result(), sum(i * i for i in range(100)))
            self.assertEqual(task2.result(), sum(i * i for i in range(200)))
    
    def test_tasks_property(self):
        """Test tasks property returns all submitted tasks."""
        from pyasync import CpuExecutor
        
        with CpuExecutor(max_workers=2) as executor:
            executor.submit(_cpu_compute, 100)
            executor.submit(_cpu_compute, 200)
            
            self.assertEqual(len(executor.tasks), 2)
    
    def test_wait_all(self):
        """Test wait_all method."""
        from pyasync import CpuExecutor
        
        with CpuExecutor(max_workers=2) as executor:
            executor.submit(_cpu_compute, 100)
            executor.submit(_cpu_compute, 200)
            
            results = executor.wait_all()
            
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0], sum(i * i for i in range(100)))
            self.assertEqual(results[1], sum(i * i for i in range(200)))
    
    def test_map(self):
        """Test map method."""
        from pyasync import CpuExecutor
        
        with CpuExecutor(max_workers=2) as executor:
            results = list(executor.map(_cpu_compute, [100, 200, 300]))
            
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0], sum(i * i for i in range(100)))
    
    def test_not_entered_error(self):
        """Test error when not using context manager."""
        from pyasync import CpuExecutor
        
        executor = CpuExecutor()
        
        with self.assertRaises(RuntimeError):
            executor.submit(_cpu_compute, 100)


if __name__ == '__main__':
    unittest.main()
