"""Unit tests for pyasync.transformer module."""

import unittest
import ast


class TestAsyncCallTransformer(unittest.TestCase):
    """Tests for AsyncCallTransformer class."""
    
    def test_detects_async_functions(self):
        """Test that transformer correctly identifies async functions."""
        from pyasync.transformer import AsyncCallTransformer
        
        source = """
async def foo():
    return 1

async def bar():
    return 2

def sync_func():
    return 3
"""
        tree = ast.parse(source)
        transformer = AsyncCallTransformer()
        transformer.visit(tree)
        
        self.assertIn('foo', transformer._async_functions)
        self.assertIn('bar', transformer._async_functions)
        self.assertNotIn('sync_func', transformer._async_functions)
    
    def test_transforms_async_calls_outside_async(self):
        """Test that async calls outside async context are transformed."""
        from pyasync.transformer import transform_source
        
        source = """
async def my_async():
    return 42

result = my_async()
"""
        transformed = transform_source(source)
        code = ast.unparse(transformed)
        
        self.assertIn('_pyasync_run', code)
    
    def test_preserves_calls_in_async_context(self):
        """Test that async calls inside async functions are not transformed."""
        from pyasync.transformer import transform_source
        
        source = """
async def inner():
    return 42

async def outer():
    return await inner()
"""
        transformed = transform_source(source)
        code = ast.unparse(transformed)
        
        # Inner call should NOT be wrapped with _pyasync_run
        lines = code.split('\n')
        outer_body = [l for l in lines if 'inner()' in l and 'async def' not in l]
        
        for line in outer_body:
            if '_pyasync_run' in line:
                self.fail("Async call inside async function should not be wrapped")
    
    def test_transforms_await_expressions(self):
        """Test that await expressions are transformed."""
        from pyasync.transformer import transform_source
        
        source = """
async def my_func():
    result = await some_call()
    return result
"""
        transformed = transform_source(source)
        code = ast.unparse(transformed)
        
        self.assertIn('_pyasync_await', code)
    
    def test_preserves_gather_args(self):
        """Test that args to gather are not auto-executed."""
        from pyasync.transformer import transform_source
        
        source = """
async def task():
    return 1

results = gather(task(), task())
"""
        transformed = transform_source(source)
        code = ast.unparse(transformed)
        
        gather_line = [l for l in code.split('\n') if 'gather(' in l][0]
        self.assertNotIn('_pyasync_run(task())', gather_line)
    
    def test_preserves_spawn_args(self):
        """Test that args to spawn are not auto-executed."""
        from pyasync.transformer import transform_source
        
        source = """
async def task():
    return 1

spawned = spawn(task())
"""
        transformed = transform_source(source)
        code = ast.unparse(transformed)
        
        spawn_line = [l for l in code.split('\n') if 'spawn(' in l][0]
        self.assertNotIn('_pyasync_run(task())', spawn_line)
    
    def test_preserves_pyasync_gather_args(self):
        """Test that pyasync.gather args are preserved."""
        from pyasync.transformer import transform_source
        
        source = """
async def task():
    return 1

results = pyasync.gather(task(), task())
"""
        transformed = transform_source(source)
        code = ast.unparse(transformed)
        
        gather_line = [l for l in code.split('\n') if 'gather(' in l][0]
        self.assertNotIn('_pyasync_run(task())', gather_line)


class TestTransformSource(unittest.TestCase):
    """Tests for transform_source function."""
    
    def test_returns_ast_module(self):
        """Test that transform_source returns an AST Module."""
        from pyasync.transformer import transform_source
        
        source = "x = 1"
        result = transform_source(source)
        
        self.assertIsInstance(result, ast.Module)
    
    def test_handles_empty_source(self):
        """Test handling of empty source."""
        from pyasync.transformer import transform_source
        
        result = transform_source("")
        self.assertIsInstance(result, ast.Module)
    
    def test_preserves_non_async_code(self):
        """Test that non-async code is preserved."""
        from pyasync.transformer import transform_source
        
        source = """
def regular_func():
    return 42

x = regular_func()
y = x + 1
"""
        transformed = transform_source(source)
        code = ast.unparse(transformed)
        
        self.assertIn('regular_func()', code)
        self.assertIn('y = x + 1', code)


if __name__ == '__main__':
    unittest.main()
