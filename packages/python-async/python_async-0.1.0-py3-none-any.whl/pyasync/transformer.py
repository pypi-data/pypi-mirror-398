"""
PyAsync AST Transformer - Transforms async calls to run synchronously.
"""

import ast
from typing import Set


# Functions that should receive raw coroutines (not auto-executed)
COROUTINE_CONSUMERS = {'spawn', 'gather'}


class AsyncCallTransformer(ast.NodeTransformer):
    """
    Transforms calls to async functions into wrapped synchronous calls.
    Also transforms await expressions to handle both sync and async values.
    
    Transformations:
        1. result = my_async_func()  ->  result = _pyasync_run(my_async_func())
        2. await expr  ->  _pyasync_await(expr)  (inside async functions)
    
    Exceptions:
        - Async calls inside spawn() or gather() are NOT transformed
          (they need the raw coroutine for parallel execution)
    """
    
    def __init__(self):
        super().__init__()
        self._async_functions: Set[str] = set()
        self._in_async_context = False
        self._in_coroutine_consumer = False  # Inside spawn/gather args
    
    def visit_Module(self, node: ast.Module) -> ast.Module:
        """First pass: collect all async function names."""
        for item in ast.walk(node):
            if isinstance(item, ast.AsyncFunctionDef):
                self._async_functions.add(item.name)
        
        # Second pass: transform the tree
        self.generic_visit(node)
        return node
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Mark that we're inside an async context while visiting."""
        old_context = self._in_async_context
        self._in_async_context = True
        self.generic_visit(node)
        self._in_async_context = old_context
        return node
    
    def visit_Await(self, node: ast.Await) -> ast.AST:
        """
        Transform await expressions to handle both sync and async values.
        
        await expr  ->  await _pyasync_await(expr)
        
        This allows using await on sync functions without errors.
        """
        # First transform any nested nodes
        self.generic_visit(node)
        
        # Wrap the await value with _pyasync_await
        return ast.Await(
            value=ast.Call(
                func=ast.Name(id='_pyasync_await', ctx=ast.Load()),
                args=[node.value],
                keywords=[]
            )
        )
    
    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Transform async function calls outside of async context."""
        
        # Check if this is a call to spawn/gather (coroutine consumers)
        func_name = self._get_full_func_name(node)
        is_coroutine_consumer = func_name in COROUTINE_CONSUMERS or \
                                func_name.endswith('.spawn') or \
                                func_name.endswith('.gather')
        
        if is_coroutine_consumer:
            # Don't transform the arguments of spawn/gather
            # They need the raw coroutines for parallel execution
            old_in_consumer = self._in_coroutine_consumer
            self._in_coroutine_consumer = True
            
            # Transform the args manually
            new_args = []
            for arg in node.args:
                new_args.append(self.visit(arg))
            
            new_keywords = []
            for kw in node.keywords:
                new_keywords.append(ast.keyword(arg=kw.arg, value=self.visit(kw.value)))
            
            self._in_coroutine_consumer = old_in_consumer
            
            # Return the call with transformed args (but args not wrapped with _pyasync_run)
            return ast.Call(
                func=node.func,
                args=new_args,
                keywords=new_keywords
            )
        
        # Standard transformation
        self.generic_visit(node)
        
        # Don't transform if we're inside an async function
        if self._in_async_context:
            return node
        
        # Don't transform if we're inside spawn/gather args
        if self._in_coroutine_consumer:
            return node
        
        # Check if this is a call to a known async function
        simple_name = self._get_func_name(node)
        if simple_name and simple_name in self._async_functions:
            # Wrap with _pyasync_run()
            return ast.Call(
                func=ast.Name(id='_pyasync_run', ctx=ast.Load()),
                args=[node],
                keywords=[]
            )
        
        return node
    
    def _get_func_name(self, node: ast.Call) -> str | None:
        """Extract the simple function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None
    
    def _get_full_func_name(self, node: ast.Call) -> str:
        """Extract the full function name (including module) from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return ''


def transform_source(source: str, filename: str = '<unknown>') -> ast.Module:
    """
    Parse and transform Python source code.
    
    Returns a transformed AST with async calls wrapped for synchronous execution.
    """
    tree = ast.parse(source, filename=filename)
    transformer = AsyncCallTransformer()
    transformed = transformer.visit(tree)
    ast.fix_missing_locations(transformed)
    return transformed
