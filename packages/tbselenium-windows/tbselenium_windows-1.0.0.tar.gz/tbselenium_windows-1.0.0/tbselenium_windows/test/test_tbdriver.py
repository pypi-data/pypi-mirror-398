"""
Tests for tbdriver.py module.

These tests verify the TorBrowserDriver class initialization and configuration
without requiring an actual Tor Browser installation.
"""

import unittest

from tbselenium_windows.tbdriver import (
    TorBrowserDriver,
    DEFAULT_BANNED_PORTS,
    GECKO_DRIVER_EXE_PATH,
)
from tbselenium_windows.exceptions import (
    TBDriverPathError,
)
from tbselenium_windows import common as cm


class TestTorBrowserDriverPathValidation(unittest.TestCase):
    """Test TorBrowserDriver path validation."""

    def test_no_path_raises_error(self):
        """Test that missing path raises TBDriverPathError."""
        with self.assertRaises(TBDriverPathError) as ctx:
            TorBrowserDriver()
        self.assertIn("Either TBB path", str(ctx.exception))

    def test_invalid_path_raises_error(self):
        """Test that invalid path raises TBDriverPathError."""
        with self.assertRaises(TBDriverPathError) as ctx:
            TorBrowserDriver("C:\\definitely\\nonexistent\\path")
        self.assertIn("not a directory", str(ctx.exception))

    def test_empty_path_raises_error(self):
        """Test that empty string path raises TBDriverPathError."""
        with self.assertRaises(TBDriverPathError) as ctx:
            TorBrowserDriver("")
        self.assertIn("Either TBB path", str(ctx.exception))


class TestTorBrowserDriverConfigConstants(unittest.TestCase):
    """Test TorBrowserDriver configuration constants."""

    def test_launch_new_tbb_tor_constant(self):
        """Test LAUNCH_NEW_TBB_TOR constant value."""
        self.assertEqual(cm.LAUNCH_NEW_TBB_TOR, 0)

    def test_use_running_tor_constant(self):
        """Test USE_RUNNING_TOR constant value."""
        self.assertEqual(cm.USE_RUNNING_TOR, 1)

    def test_use_stem_constant(self):
        """Test USE_STEM constant value."""
        self.assertEqual(cm.USE_STEM, 2)

    def test_valid_tor_cfg_values(self):
        """Test that valid tor_cfg values are USE_RUNNING_TOR and USE_STEM."""
        valid_configs = [cm.USE_RUNNING_TOR, cm.USE_STEM]
        self.assertEqual(len(valid_configs), 2)
        self.assertIn(1, valid_configs)
        self.assertIn(2, valid_configs)


class TestTorBrowserDriverPortConstants(unittest.TestCase):
    """Test TorBrowserDriver port-related constants."""

    def test_default_socks_port(self):
        """Test DEFAULT_SOCKS_PORT constant."""
        self.assertEqual(cm.DEFAULT_SOCKS_PORT, 9050)

    def test_default_control_port(self):
        """Test DEFAULT_CONTROL_PORT constant."""
        self.assertEqual(cm.DEFAULT_CONTROL_PORT, 9051)

    def test_stem_socks_port(self):
        """Test STEM_SOCKS_PORT constant."""
        self.assertEqual(cm.STEM_SOCKS_PORT, 9250)

    def test_stem_control_port(self):
        """Test STEM_CONTROL_PORT constant."""
        self.assertEqual(cm.STEM_CONTROL_PORT, 9251)

    def test_tbb_socks_port(self):
        """Test TBB_SOCKS_PORT constant."""
        self.assertEqual(cm.TBB_SOCKS_PORT, 9150)

    def test_tbb_control_port(self):
        """Test TBB_CONTROL_PORT constant."""
        self.assertEqual(cm.TBB_CONTROL_PORT, 9151)


class TestDefaultBannedPorts(unittest.TestCase):
    """Test default banned ports constant."""

    def test_default_banned_ports_format(self):
        """Test DEFAULT_BANNED_PORTS has correct format."""
        self.assertIsInstance(DEFAULT_BANNED_PORTS, str)
        ports = DEFAULT_BANNED_PORTS.split(',')
        self.assertEqual(len(ports), 4)
        for port in ports:
            self.assertTrue(port.strip().isdigit())

    def test_default_banned_ports_contains_standard_ports(self):
        """Test DEFAULT_BANNED_PORTS contains standard Tor ports."""
        self.assertIn("9050", DEFAULT_BANNED_PORTS)
        self.assertIn("9051", DEFAULT_BANNED_PORTS)
        self.assertIn("9150", DEFAULT_BANNED_PORTS)
        self.assertIn("9151", DEFAULT_BANNED_PORTS)


class TestGeckodriverPath(unittest.TestCase):
    """Test geckodriver path detection."""

    def test_geckodriver_path_is_none_or_string(self):
        """Test GECKO_DRIVER_EXE_PATH is None or valid string."""
        self.assertTrue(
            GECKO_DRIVER_EXE_PATH is None or
            isinstance(GECKO_DRIVER_EXE_PATH, str)
        )


class TestTorBrowserDriverClass(unittest.TestCase):
    """Test TorBrowserDriver class structure."""

    def test_class_has_expected_methods(self):
        """Test that class has all expected methods."""
        expected_methods = [
            'load_url',
            'find_element_by',
            'quit',
            'install_extensions',
            'init_ports',
            'init_prefs',
            'setup_tbb_paths',
            'export_env_vars',
            'add_ports_to_fx_banned_ports',
            'set_tb_prefs_for_using_system_tor',
            'clean_up_profile_dirs',
        ]

        for method_name in expected_methods:
            self.assertTrue(
                hasattr(TorBrowserDriver, method_name),
                f"TorBrowserDriver should have method {method_name}"
            )

    def test_class_has_context_manager_methods(self):
        """Test that class supports context manager protocol."""
        self.assertTrue(hasattr(TorBrowserDriver, '__enter__'))
        self.assertTrue(hasattr(TorBrowserDriver, '__exit__'))

    def test_class_has_is_connection_error_page_property(self):
        """Test that class has is_connection_error_page property."""
        self.assertTrue(
            hasattr(TorBrowserDriver, 'is_connection_error_page')
        )


class TestTorBrowserDriverDefaults(unittest.TestCase):
    """Test TorBrowserDriver default values."""

    def test_default_parameter_values(self):
        """Test that __init__ has correct default parameters."""
        import inspect
        sig = inspect.signature(TorBrowserDriver.__init__)

        # Check default values for key parameters
        params = sig.parameters

        self.assertEqual(params['tbb_path'].default, "")
        self.assertEqual(params['tor_cfg'].default, cm.USE_RUNNING_TOR)
        self.assertEqual(params['tbb_fx_binary_path'].default, "")
        self.assertEqual(params['tbb_profile_path'].default, "")
        self.assertEqual(params['tbb_logfile_path'].default, "")
        self.assertEqual(params['tor_data_dir'].default, "")
        self.assertEqual(params['default_bridge_type'].default, "")
        self.assertEqual(params['headless'].default, False)
        self.assertEqual(params['use_custom_profile'].default, False)
        self.assertEqual(params['geckodriver_port'].default, 0)
        self.assertEqual(params['marionette_port'].default, 0)

    def test_default_none_for_mutable_args(self):
        """Test that mutable defaults are None (not empty collections)."""
        import inspect
        sig = inspect.signature(TorBrowserDriver.__init__)
        params = sig.parameters

        self.assertIsNone(params['pref_dict'].default)
        self.assertIsNone(params['extensions'].default)
        self.assertIsNone(params['socks_port'].default)
        self.assertIsNone(params['control_port'].default)
        self.assertIsNone(params['options'].default)


if __name__ == "__main__":
    unittest.main()
