"""Unit tests for pyasync.hook module."""

import unittest
import sys


class TestInstallHook(unittest.TestCase):
    """Tests for install_hook function."""
    
    def test_hook_installed(self):
        """Test that import hook is installed after importing pyasync."""
        from pyasync.hook import PyAsyncFinder
        
        # Check that a PyAsyncFinder is in sys.meta_path
        finders = [f for f in sys.meta_path if isinstance(f, PyAsyncFinder)]
        self.assertGreater(len(finders), 0)
    
    def test_install_hook_idempotent(self):
        """Test that calling install_hook multiple times doesn't add multiple hooks."""
        from pyasync.hook import install_hook, PyAsyncFinder
        
        initial_count = len([f for f in sys.meta_path if isinstance(f, PyAsyncFinder)])
        
        install_hook()
        install_hook()
        install_hook()
        
        final_count = len([f for f in sys.meta_path if isinstance(f, PyAsyncFinder)])
        self.assertEqual(initial_count, final_count)


class TestUninstallHook(unittest.TestCase):
    """Tests for uninstall_hook function."""
    
    def test_uninstall_removes_hook(self):
        """Test that uninstall_hook removes the finder."""
        from pyasync.hook import install_hook, uninstall_hook, PyAsyncFinder
        
        install_hook()
        self.assertGreater(len([f for f in sys.meta_path if isinstance(f, PyAsyncFinder)]), 0)
        
        uninstall_hook()
        self.assertEqual(len([f for f in sys.meta_path if isinstance(f, PyAsyncFinder)]), 0)
        
        # Reinstall for other tests
        install_hook()


class TestPyAsyncFinder(unittest.TestCase):
    """Tests for PyAsyncFinder class."""
    
    def test_skips_pyasync_itself(self):
        """Test that finder skips pyasync module."""
        from pyasync.hook import PyAsyncFinder
        
        finder = PyAsyncFinder(["/some/path"])
        result = finder.find_spec("pyasync", None)
        
        self.assertIsNone(result)
    
    def test_skips_pyasync_submodules(self):
        """Test that finder skips pyasync submodules."""
        from pyasync.hook import PyAsyncFinder
        
        finder = PyAsyncFinder(["/some/path"])
        
        self.assertIsNone(finder.find_spec("pyasync.runtime", None))
        self.assertIsNone(finder.find_spec("pyasync.transformer", None))
        self.assertIsNone(finder.find_spec("pyasync.hook", None))
    
    def test_skips_already_imported(self):
        """Test that finder skips already imported modules."""
        from pyasync.hook import PyAsyncFinder
        
        finder = PyAsyncFinder(["/some/path"])
        
        # 'os' is already imported
        result = finder.find_spec("os", None)
        self.assertIsNone(result)


class TestPyAsyncLoader(unittest.TestCase):
    """Tests for PyAsyncLoader class."""
    
    def test_loader_injects_runtime_functions(self):
        """Test that loader injects _pyasync_run and _pyasync_await."""
        from pyasync.hook import PyAsyncLoader
        import types
        
        # Create a mock module
        module = types.ModuleType("test_module")
        
        # Create a temp file with simple content
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x = 1\n")
            temp_path = f.name
        
        try:
            loader = PyAsyncLoader("test_module", temp_path)
            loader.exec_module(module)
            
            self.assertIn('_pyasync_run', module.__dict__)
            self.assertIn('_pyasync_await', module.__dict__)
            self.assertIn('__pyasync_transformed__', module.__dict__)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
