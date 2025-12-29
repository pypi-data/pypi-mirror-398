"""
Tests for utils.py module.

These tests verify utility functions work correctly.
"""

import os
import sys
import unittest
from os import environ

from tbselenium_windows.utils import (
    is_busy,
    prepend_to_env_var,
    is_windows,
    read_file,
    TB_SECURITY_LEVELS,
    TB_SECURITY_LEVEL_STANDARD,
    TB_SECURITY_LEVEL_SAFER,
    TB_SECURITY_LEVEL_SAFEST,
    find_tor_browser_dir,
    get_geckodriver_path,
)


class TestIsBusy(unittest.TestCase):
    """Tests for is_busy function."""

    def test_unused_port_not_busy(self):
        """Test that unused port returns False."""
        # Use a high port that's unlikely to be in use
        self.assertFalse(is_busy(59999))

    def test_returns_bool(self):
        """Test that is_busy returns a boolean."""
        result = is_busy(59999)
        self.assertIsInstance(result, bool)


class TestPrependToEnvVar(unittest.TestCase):
    """Tests for prepend_to_env_var function."""

    def setUp(self):
        """Save original environment."""
        self.test_var = "_TEST_PREPEND_VAR"
        self.original = environ.get(self.test_var)

    def tearDown(self):
        """Restore original environment."""
        if self.original is None:
            if self.test_var in environ:
                del environ[self.test_var]
        else:
            environ[self.test_var] = self.original

    def test_prepend_to_new_var(self):
        """Test prepending to a new environment variable."""
        if self.test_var in environ:
            del environ[self.test_var]

        prepend_to_env_var(self.test_var, "C:\\test\\path")
        self.assertEqual(environ[self.test_var], "C:\\test\\path")

    def test_prepend_to_existing_var(self):
        """Test prepending to an existing environment variable."""
        environ[self.test_var] = "C:\\existing\\path"

        prepend_to_env_var(self.test_var, "C:\\new\\path")
        expected = "C:\\new\\path" + os.pathsep + "C:\\existing\\path"
        self.assertEqual(environ[self.test_var], expected)

    def test_no_duplicate(self):
        """Test that prepending doesn't create duplicates."""
        # Use a path without the platform's path separator character
        test_path = "/existing/path"
        environ[self.test_var] = test_path

        prepend_to_env_var(self.test_var, test_path)
        self.assertEqual(environ[self.test_var], test_path)

    def test_multiple_prepends(self):
        """Test multiple prepends work correctly."""
        if self.test_var in environ:
            del environ[self.test_var]

        prepend_to_env_var(self.test_var, "C:\\path1")
        prepend_to_env_var(self.test_var, "C:\\path2")
        prepend_to_env_var(self.test_var, "C:\\path3")

        expected = os.pathsep.join(["C:\\path3", "C:\\path2", "C:\\path1"])
        self.assertEqual(environ[self.test_var], expected)


class TestIsWindows(unittest.TestCase):
    """Tests for is_windows function."""

    def test_returns_bool(self):
        """Test that is_windows returns a boolean."""
        result = is_windows()
        self.assertIsInstance(result, bool)

    def test_matches_platform(self):
        """Test that is_windows matches sys.platform."""
        self.assertEqual(is_windows(), sys.platform == 'win32')


class TestReadFile(unittest.TestCase):
    """Tests for read_file function."""

    def test_read_existing_file(self):
        """Test reading an existing file."""
        import tempfile

        content = "Hello, World!"
        with tempfile.NamedTemporaryFile(mode='w', delete=False,
                                         encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            result = read_file(temp_path)
            self.assertEqual(result, content)
        finally:
            os.unlink(temp_path)

    def test_read_file_not_found(self):
        """Test reading a non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            read_file("C:\\nonexistent\\file.txt")


class TestSecurityLevels(unittest.TestCase):
    """Tests for security level constants."""

    def test_security_levels_defined(self):
        """Test that security level constants are defined."""
        self.assertEqual(TB_SECURITY_LEVEL_STANDARD, 'standard')
        self.assertEqual(TB_SECURITY_LEVEL_SAFER, 'safer')
        self.assertEqual(TB_SECURITY_LEVEL_SAFEST, 'safest')

    def test_security_levels_list(self):
        """Test that security levels list contains all levels."""
        self.assertIn(TB_SECURITY_LEVEL_STANDARD, TB_SECURITY_LEVELS)
        self.assertIn(TB_SECURITY_LEVEL_SAFER, TB_SECURITY_LEVELS)
        self.assertIn(TB_SECURITY_LEVEL_SAFEST, TB_SECURITY_LEVELS)
        self.assertEqual(len(TB_SECURITY_LEVELS), 3)

    def test_security_levels_order(self):
        """Test that security levels are in correct order."""
        self.assertEqual(TB_SECURITY_LEVELS[0], TB_SECURITY_LEVEL_STANDARD)
        self.assertEqual(TB_SECURITY_LEVELS[1], TB_SECURITY_LEVEL_SAFER)
        self.assertEqual(TB_SECURITY_LEVELS[2], TB_SECURITY_LEVEL_SAFEST)


class TestFindTorBrowserDir(unittest.TestCase):
    """Tests for find_tor_browser_dir function."""

    def test_returns_none_or_string(self):
        """Test that function returns None or a string."""
        result = find_tor_browser_dir()
        self.assertTrue(result is None or isinstance(result, str))

    def test_returned_path_exists_if_not_none(self):
        """Test that returned path exists if not None."""
        result = find_tor_browser_dir()
        if result is not None:
            self.assertTrue(os.path.isdir(result))
            firefox_path = os.path.join(result, 'Browser', 'firefox.exe')
            self.assertTrue(os.path.isfile(firefox_path))


class TestGetGeckodriverPath(unittest.TestCase):
    """Tests for get_geckodriver_path function."""

    def test_returns_none_or_string(self):
        """Test that function returns None or a string."""
        result = get_geckodriver_path()
        self.assertTrue(result is None or isinstance(result, str))

    def test_returned_path_is_file_if_not_none(self):
        """Test that returned path is a file if not None."""
        result = get_geckodriver_path()
        if result is not None:
            self.assertTrue(os.path.isfile(result))


if __name__ == "__main__":
    unittest.main()
