"""
PyAsync - Execute async functions transparently without wrappers.

Usage:
    import pyasync  # This activates the import hook
    
    async def my_func():
        await pyasync.sleep(1)
        return "done"
    
    result = my_func()  # Works directly, no wrapper needed!
"""

import sys
import ast
import types
from pathlib import Path

from .hook import install_hook
from .runtime import sleep, gather, spawn, _pyasync_run, _pyasync_await
from .transformer import AsyncCallTransformer


def _transform_main_module():
    """
    Transform the __main__ module to wrap async calls.
    
    This is needed because import hooks don't apply to the main script.
    We re-execute the main module with transformed code.
    """
    import __main__
    
    # Check if already transformed
    if getattr(__main__, '__pyasync_transformed__', False):
        return
    
    # Get the source file of __main__
    main_file = getattr(__main__, '__file__', None)
    if not main_file:
        return
    
    main_path = Path(main_file)
    if not main_path.exists():
        return
    
    # Skip system modules (stdlib, site-packages, etc.)
    main_str = str(main_path.resolve())
    skip_prefixes = [
        sys.prefix,
        sys.base_prefix,
        str(Path(sys.executable).parent.parent),
    ]
    for prefix in skip_prefixes:
        if main_str.startswith(prefix):
            return
    
    # Read and transform the source
    source = main_path.read_text()
    
    # Parse and transform
    tree = ast.parse(source, str(main_path))
    transformer = AsyncCallTransformer()
    transformed = transformer.visit(tree)
    ast.fix_missing_locations(transformed)
    
    # Compile
    code = compile(transformed, str(main_path), 'exec')
    
    # Prepare new globals
    new_globals = {
        '__name__': '__main__',
        '__file__': str(main_path),
        '__pyasync_transformed__': True,
        '_pyasync_run': _pyasync_run,
        '_pyasync_await': _pyasync_await,
    }
    
    # Copy over any imports that were already done
    for name, value in __main__.__dict__.items():
        if name.startswith('__') and name.endswith('__'):
            continue
        if isinstance(value, types.ModuleType):
            new_globals[name] = value
    
    # Execute transformed code
    exec(code, new_globals)
    
    # Exit to prevent original code from continuing
    sys.exit(0)


# Install the import hook on import
install_hook()

# Transform the main module if this is imported from __main__
_transform_main_module()

__all__ = ['sleep', 'gather', '_pyasync_run', '_pyasync_await']
__version__ = '0.1.0'
