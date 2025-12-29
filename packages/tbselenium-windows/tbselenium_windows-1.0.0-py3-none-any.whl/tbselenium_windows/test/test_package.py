"""
Tests for package structure and imports.

These tests verify the package is correctly structured and all exports work.
"""

import unittest


class TestPackageImports(unittest.TestCase):
    """Test that package imports work correctly."""

    def test_import_package(self):
        """Test that main package can be imported."""
        import tbselenium_windows
        self.assertIsNotNone(tbselenium_windows)

    def test_import_tbdriver(self):
        """Test that TorBrowserDriver can be imported."""
        from tbselenium_windows import TorBrowserDriver
        self.assertIsNotNone(TorBrowserDriver)

    def test_import_tor_cfg_constants(self):
        """Test that Tor configuration constants can be imported."""
        from tbselenium_windows import USE_RUNNING_TOR, USE_STEM
        self.assertEqual(USE_RUNNING_TOR, 1)
        self.assertEqual(USE_STEM, 2)

    def test_import_port_constants(self):
        """Test that port constants can be imported."""
        from tbselenium_windows import (
            DEFAULT_SOCKS_PORT,
            DEFAULT_CONTROL_PORT,
            STEM_SOCKS_PORT,
            STEM_CONTROL_PORT,
        )
        self.assertEqual(DEFAULT_SOCKS_PORT, 9050)
        self.assertEqual(DEFAULT_CONTROL_PORT, 9051)
        self.assertEqual(STEM_SOCKS_PORT, 9250)
        self.assertEqual(STEM_CONTROL_PORT, 9251)

    def test_import_utility_functions(self):
        """Test that utility functions can be imported."""
        from tbselenium_windows import (
            launch_tbb_tor_with_stem,
            set_security_level,
            disable_js,
            enable_js,
        )
        self.assertIsNotNone(launch_tbb_tor_with_stem)
        self.assertIsNotNone(set_security_level)
        self.assertIsNotNone(disable_js)
        self.assertIsNotNone(enable_js)

    def test_import_security_levels(self):
        """Test that security level constants can be imported."""
        from tbselenium_windows import (
            TB_SECURITY_LEVEL_STANDARD,
            TB_SECURITY_LEVEL_SAFER,
            TB_SECURITY_LEVEL_SAFEST,
        )
        self.assertEqual(TB_SECURITY_LEVEL_STANDARD, 'standard')
        self.assertEqual(TB_SECURITY_LEVEL_SAFER, 'safer')
        self.assertEqual(TB_SECURITY_LEVEL_SAFEST, 'safest')

    def test_import_exceptions(self):
        """Test that exception classes can be imported."""
        from tbselenium_windows import (
            TBDriverPathError,
            TBDriverPortError,
            TBDriverConfigError,
            StemLaunchError,
            TorBrowserDriverInitError,
        )

        # All should be exception classes
        self.assertTrue(issubclass(TBDriverPathError, Exception))
        self.assertTrue(issubclass(TBDriverPortError, Exception))
        self.assertTrue(issubclass(TBDriverConfigError, Exception))
        self.assertTrue(issubclass(StemLaunchError, Exception))
        self.assertTrue(issubclass(TorBrowserDriverInitError, Exception))


class TestPackageVersion(unittest.TestCase):
    """Test package version information."""

    def test_version_defined(self):
        """Test that __version__ is defined."""
        import tbselenium_windows
        self.assertTrue(hasattr(tbselenium_windows, '__version__'))
        self.assertIsInstance(tbselenium_windows.__version__, str)

    def test_version_format(self):
        """Test that version follows semantic versioning format."""
        import tbselenium_windows
        version = tbselenium_windows.__version__

        # Should have at least major.minor.patch
        parts = version.split('.')
        self.assertGreaterEqual(len(parts), 3)

        # First three parts should be numeric
        for part in parts[:3]:
            # Handle pre-release suffixes like "1.0.0a1"
            numeric_part = ''.join(c for c in part if c.isdigit())
            self.assertTrue(numeric_part.isdigit())


class TestPackageAll(unittest.TestCase):
    """Test __all__ exports."""

    def test_all_defined(self):
        """Test that __all__ is defined."""
        import tbselenium_windows
        self.assertTrue(hasattr(tbselenium_windows, '__all__'))
        self.assertIsInstance(tbselenium_windows.__all__, list)

    def test_all_exports_are_importable(self):
        """Test that all items in __all__ can be imported."""
        import tbselenium_windows

        for name in tbselenium_windows.__all__:
            self.assertTrue(
                hasattr(tbselenium_windows, name),
                f"{name} in __all__ but not importable"
            )

    def test_all_contains_main_exports(self):
        """Test that __all__ contains main exports."""
        import tbselenium_windows

        expected_exports = [
            'TorBrowserDriver',
            'USE_RUNNING_TOR',
            'USE_STEM',
            'DEFAULT_SOCKS_PORT',
            'DEFAULT_CONTROL_PORT',
            'launch_tbb_tor_with_stem',
        ]

        for export in expected_exports:
            self.assertIn(export, tbselenium_windows.__all__)


class TestSubmoduleImports(unittest.TestCase):
    """Test that submodules can be imported directly."""

    def test_import_common(self):
        """Test that common module can be imported."""
        from tbselenium_windows import common
        self.assertIsNotNone(common)

    def test_import_exceptions_module(self):
        """Test that exceptions module can be imported."""
        from tbselenium_windows import exceptions
        self.assertIsNotNone(exceptions)

    def test_import_utils(self):
        """Test that utils module can be imported."""
        from tbselenium_windows import utils
        self.assertIsNotNone(utils)

    def test_import_tbdriver_module(self):
        """Test that tbdriver module can be imported."""
        from tbselenium_windows import tbdriver
        self.assertIsNotNone(tbdriver)


class TestNoCircularImports(unittest.TestCase):
    """Test that there are no circular import issues."""

    def test_import_order_1(self):
        """Test importing in one order works."""
        from tbselenium_windows import common
        from tbselenium_windows import exceptions
        from tbselenium_windows import utils
        from tbselenium_windows import tbdriver
        self.assertIsNotNone(tbdriver)

    def test_import_order_2(self):
        """Test importing in reverse order works."""
        from tbselenium_windows import tbdriver
        from tbselenium_windows import utils
        from tbselenium_windows import exceptions
        from tbselenium_windows import common
        self.assertIsNotNone(common)

    def test_import_main_first(self):
        """Test importing main package first works."""
        import tbselenium_windows
        from tbselenium_windows import common
        from tbselenium_windows import TorBrowserDriver
        self.assertIsNotNone(TorBrowserDriver)


if __name__ == "__main__":
    unittest.main()
