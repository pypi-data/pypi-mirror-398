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


if __name__ == '__main__':
    unittest.main()
