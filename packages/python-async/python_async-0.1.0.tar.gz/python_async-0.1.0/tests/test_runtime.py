"""Unit tests for pyasync.runtime module."""

import unittest
import time
import threading


class TestPyAsyncRun(unittest.TestCase):
    """Tests for _pyasync_run function."""
    
    def test_simple_coroutine(self):
        """Test execution of a simple coroutine."""
        from pyasync.runtime import _pyasync_run
        
        async def simple():
            return 42
        
        result = _pyasync_run(simple())
        self.assertEqual(result, 42)
    
    def test_nested_await(self):
        """Test nested await calls."""
        from pyasync.runtime import _pyasync_run
        
        async def inner():
            return "inner"
        
        async def outer():
            result = await inner()
            return f"outer-{result}"
        
        result = _pyasync_run(outer())
        self.assertEqual(result, "outer-inner")
    
    def test_exception_propagation(self):
        """Test that exceptions are properly propagated."""
        from pyasync.runtime import _pyasync_run
        
        async def raises():
            raise ValueError("test error")
        
        with self.assertRaises(ValueError) as ctx:
            _pyasync_run(raises())
        
        self.assertEqual(str(ctx.exception), "test error")
    
    def test_return_complex_types(self):
        """Test returning complex data structures."""
        from pyasync.runtime import _pyasync_run
        
        async def returns_complex():
            return {"key": "value", "list": [1, 2, 3], "nested": {"a": 1}}
        
        result = _pyasync_run(returns_complex())
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["list"], [1, 2, 3])
        self.assertEqual(result["nested"]["a"], 1)
    
    def test_with_non_coroutine(self):
        """Test that _pyasync_run returns non-coroutines as-is."""
        from pyasync.runtime import _pyasync_run
        
        result = _pyasync_run(42)
        self.assertEqual(result, 42)
        
        result = _pyasync_run("string")
        self.assertEqual(result, "string")


class TestPyAsyncAwait(unittest.TestCase):
    """Tests for _pyasync_await function."""
    
    def test_with_sync_value(self):
        """Test _pyasync_await with synchronous values."""
        from pyasync.runtime import _pyasync_await, _pyasync_run
        
        async def use_await():
            result = await _pyasync_await(42)
            return result
        
        result = _pyasync_run(use_await())
        self.assertEqual(result, 42)
    
    def test_with_coroutine(self):
        """Test _pyasync_await passes through coroutines."""
        from pyasync.runtime import _pyasync_await, _pyasync_run
        
        async def inner():
            return "from_coroutine"
        
        async def outer():
            coro = inner()
            wrapped = _pyasync_await(coro)
            return await wrapped
        
        result = _pyasync_run(outer())
        self.assertEqual(result, "from_coroutine")


class TestSleep(unittest.TestCase):
    """Tests for sleep function."""
    
    def test_sleep_pauses_execution(self):
        """Test that sleep actually pauses execution."""
        from pyasync.runtime import _pyasync_run, sleep
        
        async def with_sleep():
            start = time.monotonic()
            await sleep(0.1)
            elapsed = time.monotonic() - start
            return elapsed >= 0.1
        
        result = _pyasync_run(with_sleep())
        self.assertTrue(result)


class TestGather(unittest.TestCase):
    """Tests for gather function."""
    
    def test_empty(self):
        """Test gather with no arguments."""
        from pyasync.runtime import gather
        
        results = gather()
        self.assertEqual(results, [])
    
    def test_single(self):
        """Test gather with a single coroutine."""
        from pyasync.runtime import gather
        
        async def task():
            return "single"
        
        results = gather(task())
        self.assertEqual(results, ["single"])
    
    def test_multiple(self):
        """Test gather with multiple coroutines."""
        from pyasync.runtime import gather
        
        async def task(n):
            return n * 2
        
        results = gather(task(1), task(2), task(3))
        self.assertEqual(results, [2, 4, 6])
    
    def test_parallel_execution(self):
        """Test that gather runs tasks in parallel."""
        from pyasync.runtime import gather, sleep
        
        async def slow_task(n):
            await sleep(0.2)
            return n
        
        start = time.monotonic()
        results = gather(slow_task(1), slow_task(2), slow_task(3))
        elapsed = time.monotonic() - start
        
        self.assertEqual(results, [1, 2, 3])
        self.assertLess(elapsed, 0.5)  # Should be ~0.2s, not ~0.6s
    
    def test_preserves_order(self):
        """Test that gather preserves result order."""
        from pyasync.runtime import gather, sleep
        
        async def task(n, delay):
            await sleep(delay)
            return n
        
        results = gather(
            task(1, 0.2),
            task(2, 0.15),
            task(3, 0.1)
        )
        
        self.assertEqual(results, [1, 2, 3])


class TestSpawn(unittest.TestCase):
    """Tests for spawn function."""
    
    def test_basic(self):
        """Test basic spawn functionality."""
        from pyasync.runtime import spawn, sleep
        
        async def task():
            await sleep(0.1)
            return "done"
        
        spawned = spawn(task())
        self.assertFalse(spawned.done)
        
        result = spawned.result()
        self.assertEqual(result, "done")
        self.assertTrue(spawned.done)
    
    def test_runs_in_background(self):
        """Test that spawn runs task in background."""
        from pyasync.runtime import spawn, sleep
        
        results = []
        
        async def background_task():
            await sleep(0.1)
            results.append("background")
            return "done"
        
        spawned = spawn(background_task())
        results.append("main_before")
        
        spawned.result()
        results.append("main_after")
        
        self.assertEqual(results, ["main_before", "background", "main_after"])
    
    def test_exception_propagation(self):
        """Test that spawn propagates exceptions."""
        from pyasync.runtime import spawn
        
        async def failing_task():
            raise RuntimeError("task failed")
        
        spawned = spawn(failing_task())
        
        with self.assertRaises(RuntimeError) as ctx:
            spawned.result()
        
        self.assertEqual(str(ctx.exception), "task failed")


class TestEventLoop(unittest.TestCase):
    """Tests for EventLoop internals."""
    
    def test_thread_local_loops(self):
        """Test that each thread gets its own event loop."""
        from pyasync.runtime import _get_event_loop
        
        main_loop = _get_event_loop()
        thread_loops = []
        
        def get_loop_in_thread():
            loop = _get_event_loop()
            thread_loops.append(loop)
        
        threads = [threading.Thread(target=get_loop_in_thread) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        all_loops = [main_loop] + thread_loops
        self.assertEqual(len(all_loops), len(set(id(l) for l in all_loops)))


if __name__ == '__main__':
    unittest.main()
