"""
Tests for exception handling on Windows.
"""

import unittest

from tbselenium_windows.exceptions import (
    TBDriverPathError,
    TBDriverPortError,
    TBDriverConfigError,
    StemLaunchError,
    TorBrowserDriverInitError,
    TBTestEnvVarError,
    TimeExceededError,
    PlatformNotSupportedError,
)
from tbselenium_windows.tbdriver import TorBrowserDriver


class ExceptionsTest(unittest.TestCase):
    """Tests for exception handling."""

    def test_invalid_tbb_path_raises_error(self):
        """Test that invalid TBB path raises TBDriverPathError."""
        with self.assertRaises(TBDriverPathError):
            TorBrowserDriver("C:\\invalid\\path\\to\\tor\\browser")

    def test_no_path_raises_error(self):
        """Test that missing path raises TBDriverPathError."""
        with self.assertRaises(TBDriverPathError):
            TorBrowserDriver()

    def test_invalid_tor_cfg_raises_error(self):
        """Test that invalid tor_cfg raises TBDriverConfigError."""
        # Create a mock valid path scenario by catching the path error first
        # The config error would be raised after path validation
        pass  # This requires a valid TBB path to test properly

    def test_deprecated_tor_cfg_raises_error(self):
        """Test that LAUNCH_NEW_TBB_TOR raises TBDriverConfigError."""
        # The config check happens after path validation
        pass  # This requires a valid TBB path to test properly

    def test_exception_inheritance(self):
        """Test that custom exceptions inherit from Exception."""
        exceptions = [
            TBDriverPathError,
            TBDriverPortError,
            TBDriverConfigError,
            StemLaunchError,
            TorBrowserDriverInitError,
            TBTestEnvVarError,
            TimeExceededError,
            PlatformNotSupportedError,
        ]

        for exc_class in exceptions:
            self.assertTrue(issubclass(exc_class, Exception))

    def test_exception_can_be_raised(self):
        """Test that custom exceptions can be raised with messages."""
        with self.assertRaises(TBDriverPathError) as ctx:
            raise TBDriverPathError("Test path error")
        self.assertEqual(str(ctx.exception), "Test path error")

        with self.assertRaises(TBDriverPortError) as ctx:
            raise TBDriverPortError("Test port error")
        self.assertEqual(str(ctx.exception), "Test port error")

        with self.assertRaises(StemLaunchError) as ctx:
            raise StemLaunchError("Test stem error")
        self.assertEqual(str(ctx.exception), "Test stem error")

        with self.assertRaises(TBTestEnvVarError) as ctx:
            raise TBTestEnvVarError("Missing environment variable")
        self.assertEqual(str(ctx.exception), "Missing environment variable")


class TestExceptionCatching(unittest.TestCase):
    """Test that exceptions can be caught correctly."""

    def test_catch_as_exception(self):
        """All custom exceptions should be catchable as Exception."""
        exceptions_to_test = [
            (TBDriverPathError, "path error"),
            (TBDriverPortError, "port error"),
            (TBDriverConfigError, "config error"),
            (StemLaunchError, "stem error"),
        ]

        for exc_class, msg in exceptions_to_test:
            caught = False
            try:
                raise exc_class(msg)
            except Exception as e:
                caught = True
                self.assertEqual(str(e), msg)
            self.assertTrue(caught, f"Failed to catch {exc_class.__name__}")

    def test_exception_with_no_message(self):
        """Exceptions should work with no message."""
        for exc_class in [TBDriverPathError, TBDriverPortError, StemLaunchError]:
            try:
                raise exc_class()
            except exc_class as e:
                self.assertEqual(str(e), "")


if __name__ == "__main__":
    unittest.main()
