"""
Tor Browser Selenium for Windows.

This package provides Selenium WebDriver automation for Tor Browser on Windows.
It handles the Windows-specific directory structure and provides a clean
interface for controlling Tor Browser.

Basic Usage:
    from tbselenium_windows import TorBrowserDriver

    with TorBrowserDriver("C:\\Path\\To\\Tor Browser") as driver:
        driver.load_url("https://check.torproject.org")
        print(driver.title)

Requirements:
    - Tor Browser for Windows
    - Selenium 4+
    - geckodriver (download from https://github.com/mozilla/geckodriver/releases)
    - Running Tor (either system Tor or use Stem to launch from bundle)
"""

__version__ = "1.0.0"
__author__ = "tbselenium-windows contributors"

from tbselenium_windows.tbdriver import TorBrowserDriver
from tbselenium_windows.common import (
    USE_RUNNING_TOR,
    USE_STEM,
    DEFAULT_SOCKS_PORT,
    DEFAULT_CONTROL_PORT,
    STEM_SOCKS_PORT,
    STEM_CONTROL_PORT,
)
from tbselenium_windows.utils import (
    launch_tbb_tor_with_stem,
    set_security_level,
    disable_js,
    enable_js,
    TB_SECURITY_LEVEL_STANDARD,
    TB_SECURITY_LEVEL_SAFER,
    TB_SECURITY_LEVEL_SAFEST,
)
from tbselenium_windows.exceptions import (
    TBDriverPathError,
    TBDriverPortError,
    TBDriverConfigError,
    StemLaunchError,
    TorBrowserDriverInitError,
)

__all__ = [
    # Main driver
    'TorBrowserDriver',

    # Tor configuration modes
    'USE_RUNNING_TOR',
    'USE_STEM',

    # Default ports
    'DEFAULT_SOCKS_PORT',
    'DEFAULT_CONTROL_PORT',
    'STEM_SOCKS_PORT',
    'STEM_CONTROL_PORT',

    # Utility functions
    'launch_tbb_tor_with_stem',
    'set_security_level',
    'disable_js',
    'enable_js',

    # Security levels
    'TB_SECURITY_LEVEL_STANDARD',
    'TB_SECURITY_LEVEL_SAFER',
    'TB_SECURITY_LEVEL_SAFEST',

    # Exceptions
    'TBDriverPathError',
    'TBDriverPortError',
    'TBDriverConfigError',
    'StemLaunchError',
    'TorBrowserDriverInitError',
]
