"""
PyAsync Import Hook - Intercepts module imports and transforms async code.
"""

import sys
import importlib.abc
import importlib.machinery
import importlib.util
from pathlib import Path
from typing import Optional, Sequence

from .transformer import transform_source


_installed = False
_pyasync_marker = '__pyasync_transformed__'


class PyAsyncLoader(importlib.abc.SourceLoader):
    """Custom loader that transforms async code before execution."""
    
    def __init__(self, fullname: str, path: str):
        self.fullname = fullname
        self.path = path
    
    def get_filename(self, fullname: str) -> str:
        return self.path
    
    def get_data(self, path: str) -> bytes:
        with open(path, 'rb') as f:
            return f.read()
    
    def exec_module(self, module):
        """Execute module with transformed source code."""
        source = self.get_data(self.path).decode('utf-8')
        
        # Transform the AST
        transformed_ast = transform_source(source, self.path)
        
        # Compile the transformed AST
        code = compile(transformed_ast, self.path, 'exec')
        
        # Inject pyasync runtime functions into the module namespace
        from .runtime import _pyasync_run, _pyasync_await
        module.__dict__['_pyasync_run'] = _pyasync_run
        module.__dict__['_pyasync_await'] = _pyasync_await
        module.__dict__[_pyasync_marker] = True
        
        # Execute the transformed code
        exec(code, module.__dict__)


class PyAsyncFinder(importlib.abc.MetaPathFinder):
    """
    Custom finder that identifies modules to transform.
    
    Only transforms modules that are in the same directory as pyasync
    or in subdirectories (user code, not standard library).
    """
    
    def __init__(self, base_paths: Optional[Sequence[str]] = None):
        self.base_paths = base_paths or []
    
    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]],
        target=None
    ) -> Optional[importlib.machinery.ModuleSpec]:
        """Find and return a module spec if we should transform this module."""
        
        # Don't transform pyasync itself
        if fullname.startswith('pyasync'):
            return None
        
        # Don't transform already-imported modules
        if fullname in sys.modules:
            return None
        
        # Try to find the module source
        search_paths = path or sys.path
        
        for search_path in search_paths:
            if not search_path:
                continue
                
            # Check if it's in our base paths (user code)
            should_transform = False
            for base_path in self.base_paths:
                if search_path.startswith(base_path):
                    should_transform = True
                    break
            
            if not should_transform:
                # Also transform if it's in the current working directory
                try:
                    cwd = str(Path.cwd())
                    if search_path.startswith(cwd):
                        should_transform = True
                except:
                    pass
            
            if not should_transform:
                continue
            
            # Look for the module file
            module_path = Path(search_path)
            
            # Try as a package
            package_init = module_path / fullname.replace('.', '/') / '__init__.py'
            if package_init.exists():
                return importlib.machinery.ModuleSpec(
                    fullname,
                    PyAsyncLoader(fullname, str(package_init)),
                    origin=str(package_init),
                    is_package=True
                )
            
            # Try as a module
            module_file = module_path / (fullname.replace('.', '/') + '.py')
            if module_file.exists():
                return importlib.machinery.ModuleSpec(
                    fullname,
                    PyAsyncLoader(fullname, str(module_file)),
                    origin=str(module_file)
                )
            
            # Try simple filename
            simple_file = module_path / (fullname + '.py')
            if simple_file.exists():
                return importlib.machinery.ModuleSpec(
                    fullname,
                    PyAsyncLoader(fullname, str(simple_file)),
                    origin=str(simple_file)
                )
        
        return None


def install_hook():
    """Install the PyAsync import hook."""
    global _installed
    
    if _installed:
        return
    
    # Get the current working directory as base path
    try:
        base_paths = [str(Path.cwd())]
    except:
        base_paths = []
    
    finder = PyAsyncFinder(base_paths)
    sys.meta_path.insert(0, finder)
    _installed = True


def uninstall_hook():
    """Remove the PyAsync import hook."""
    global _installed
    
    sys.meta_path = [
        f for f in sys.meta_path 
        if not isinstance(f, PyAsyncFinder)
    ]
    _installed = False
