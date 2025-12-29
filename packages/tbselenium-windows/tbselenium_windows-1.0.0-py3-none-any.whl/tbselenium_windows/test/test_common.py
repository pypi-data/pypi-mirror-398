"""
Tests for common.py module.

These tests verify the constants and path helpers in the common module.
"""

import sys
import unittest

from tbselenium_windows import common as cm


class TestConstants(unittest.TestCase):
    """Test that all expected constants are defined."""

    def test_platform_constant(self):
        """Test IS_WINDOWS constant matches platform."""
        self.assertEqual(cm.IS_WINDOWS, sys.platform == 'win32')

    def test_tbb_paths_are_strings(self):
        """Test that all TBB path constants are strings."""
        path_constants = [
            cm.DEFAULT_TBB_BROWSER_DIR,
            cm.DEFAULT_TBB_TORBROWSER_DIR,
            cm.DEFAULT_TBB_FX_BINARY_PATH,
            cm.DEFAULT_TOR_BINARY_DIR,
            cm.DEFAULT_TOR_BINARY_PATH,
            cm.DEFAULT_TBB_DATA_DIR,
            cm.DEFAULT_TBB_PROFILE_PATH,
            cm.DEFAULT_TOR_DATA_PATH,
        ]

        for path in path_constants:
            self.assertIsInstance(path, str)

    def test_windows_binary_paths_have_exe_extension(self):
        """Test that Windows binary paths use .exe extension."""
        self.assertTrue(cm.DEFAULT_TBB_FX_BINARY_PATH.endswith('.exe'))
        self.assertTrue(cm.DEFAULT_TOR_BINARY_PATH.endswith('.exe'))

    def test_port_constants(self):
        """Test that port constants are integers in valid range."""
        ports = [
            cm.DEFAULT_SOCKS_PORT,
            cm.DEFAULT_CONTROL_PORT,
            cm.TBB_SOCKS_PORT,
            cm.TBB_CONTROL_PORT,
            cm.STEM_SOCKS_PORT,
            cm.STEM_CONTROL_PORT,
        ]

        for port in ports:
            self.assertIsInstance(port, int)
            self.assertGreater(port, 0)
            self.assertLess(port, 65536)

    def test_port_values(self):
        """Test that port constants have expected values."""
        self.assertEqual(cm.DEFAULT_SOCKS_PORT, 9050)
        self.assertEqual(cm.DEFAULT_CONTROL_PORT, 9051)
        self.assertEqual(cm.TBB_SOCKS_PORT, 9150)
        self.assertEqual(cm.TBB_CONTROL_PORT, 9151)
        self.assertEqual(cm.STEM_SOCKS_PORT, 9250)
        self.assertEqual(cm.STEM_CONTROL_PORT, 9251)

    def test_tor_cfg_constants(self):
        """Test Tor configuration mode constants."""
        self.assertEqual(cm.LAUNCH_NEW_TBB_TOR, 0)
        self.assertEqual(cm.USE_RUNNING_TOR, 1)
        self.assertEqual(cm.USE_STEM, 2)

    def test_known_socks_ports(self):
        """Test KNOWN_SOCKS_PORTS list."""
        self.assertIsInstance(cm.KNOWN_SOCKS_PORTS, list)
        self.assertIn(cm.DEFAULT_SOCKS_PORT, cm.KNOWN_SOCKS_PORTS)
        self.assertIn(cm.TBB_SOCKS_PORT, cm.KNOWN_SOCKS_PORTS)

    def test_port_ban_prefs(self):
        """Test PORT_BAN_PREFS list."""
        self.assertIsInstance(cm.PORT_BAN_PREFS, list)
        self.assertGreater(len(cm.PORT_BAN_PREFS), 0)

    def test_test_urls(self):
        """Test that test URLs are valid."""
        self.assertTrue(cm.CHECK_TPO_URL.startswith('http'))
        self.assertEqual(cm.TEST_URL, cm.CHECK_TPO_URL)
        self.assertEqual(cm.ABOUT_TOR_URL, 'about:tor')


class TestGetTbbPathsForDir(unittest.TestCase):
    """Test the get_tbb_paths_for_dir helper function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        result = cm.get_tbb_paths_for_dir("C:\\Tor Browser")
        self.assertIsInstance(result, dict)

    def test_contains_expected_keys(self):
        """Test that returned dict contains all expected keys."""
        result = cm.get_tbb_paths_for_dir("C:\\Tor Browser")
        expected_keys = ['fx_binary', 'profile', 'tor_binary', 'tor_data',
                         'browser_dir', 'tor_binary_dir']

        for key in expected_keys:
            self.assertIn(key, result)

    def test_paths_are_strings(self):
        """Test that all returned paths are strings."""
        result = cm.get_tbb_paths_for_dir("C:\\Tor Browser")

        for key, value in result.items():
            self.assertIsInstance(value, str)

    def test_paths_contain_tbb_dir(self):
        """Test that returned paths start with the TBB directory."""
        tbb_dir = "C:\\Tor Browser"
        result = cm.get_tbb_paths_for_dir(tbb_dir)

        for key, value in result.items():
            self.assertTrue(
                value.startswith(tbb_dir),
                f"Path {key}={value} should start with {tbb_dir}"
            )

    def test_binary_paths_have_exe(self):
        """Test that binary paths have .exe extension."""
        result = cm.get_tbb_paths_for_dir("C:\\Tor Browser")

        self.assertTrue(result['fx_binary'].endswith('.exe'))
        self.assertTrue(result['tor_binary'].endswith('.exe'))


class TestDirectoryStructure(unittest.TestCase):
    """Test that expected directory structure constants are correct."""

    def test_profile_path_structure(self):
        """Test profile path has correct structure."""
        # Profile should be under TorBrowser/Data/Browser/profile.default
        self.assertIn('TorBrowser', cm.DEFAULT_TBB_PROFILE_PATH)
        self.assertIn('Data', cm.DEFAULT_TBB_PROFILE_PATH)
        self.assertIn('Browser', cm.DEFAULT_TBB_PROFILE_PATH)
        self.assertIn('profile.default', cm.DEFAULT_TBB_PROFILE_PATH)

    def test_tor_binary_structure(self):
        """Test Tor binary path has correct structure."""
        # Tor binary should be under TorBrowser/Tor/tor.exe
        self.assertIn('TorBrowser', cm.DEFAULT_TOR_BINARY_PATH)
        self.assertIn('Tor', cm.DEFAULT_TOR_BINARY_PATH)
        self.assertIn('tor.exe', cm.DEFAULT_TOR_BINARY_PATH)

    def test_firefox_binary_structure(self):
        """Test Firefox binary path has correct structure."""
        # Firefox binary should be under Browser/firefox.exe
        self.assertIn('Browser', cm.DEFAULT_TBB_FX_BINARY_PATH)
        self.assertIn('firefox.exe', cm.DEFAULT_TBB_FX_BINARY_PATH)


if __name__ == "__main__":
    unittest.main()
