"""
Common constants and paths for Tor Browser Selenium on Windows.

Windows Tor Browser directory structure (after extraction):
    Tor Browser/
    ├── Browser/
    │   ├── firefox.exe           (Firefox binary)
    │   ├── TorBrowser/
    │   │   ├── Tor/
    │   │   │   ├── tor.exe       (Tor binary)
    │   │   │   └── *.dll         (Tor libraries)
    │   │   └── Data/
    │   │       ├── Browser/
    │   │       │   └── profile.default/  (Default profile)
    │   │       └── Tor/          (Tor data directory)
    │   └── fonts/                (Bundled fonts)
    └── Start Tor Browser.lnk    (Shortcut)

Note: The structure is similar to Linux, but uses .exe extensions
and Windows path conventions.
"""

from os.path import join, dirname, abspath
from os import environ
import sys

# Platform check
IS_WINDOWS = sys.platform == 'win32'

# Windows Tor Browser directory structure paths (relative to TBB directory)
# The TBB directory is typically: C:\Users\<user>\Desktop\Tor Browser\
# or extracted to any location

# Browser directory containing Firefox and TorBrowser subdirectory
DEFAULT_TBB_BROWSER_DIR = 'Browser'

# TorBrowser directory inside Browser
DEFAULT_TBB_TORBROWSER_DIR = join('Browser', 'TorBrowser')

# Firefox binary path (with .exe extension on Windows)
DEFAULT_TBB_FX_BINARY_PATH = join('Browser', 'firefox.exe')

# Tor binary directory and path
DEFAULT_TOR_BINARY_DIR = join(DEFAULT_TBB_TORBROWSER_DIR, 'Tor')
DEFAULT_TOR_BINARY_PATH = join(DEFAULT_TOR_BINARY_DIR, 'tor.exe')

# Data directories
DEFAULT_TBB_DATA_DIR = join(DEFAULT_TBB_TORBROWSER_DIR, 'Data')
DEFAULT_TBB_PROFILE_PATH = join(DEFAULT_TBB_DATA_DIR, 'Browser', 'profile.default')
DEFAULT_TOR_DATA_PATH = join(DEFAULT_TBB_DATA_DIR, 'Tor')

# GeoIP file paths (needed when using a custom DataDirectory)
DEFAULT_GEOIP_PATH = join(DEFAULT_TOR_DATA_PATH, 'geoip')
DEFAULT_GEOIP6_PATH = join(DEFAULT_TOR_DATA_PATH, 'geoip6')

# Changelog path
TB_CHANGE_LOG_PATH = join(DEFAULT_TBB_TORBROWSER_DIR, 'Docs', 'ChangeLog.txt')

# NoScript XPI path in the default profile
DEFAULT_TBB_NO_SCRIPT_XPI_PATH = join(
    DEFAULT_TBB_PROFILE_PATH, 'extensions',
    '{73a6fe31-595d-460b-a920-fcc0f8843232}.xpi')

# Bundled fonts directory (Windows has fonts in Browser/fonts)
DEFAULT_BUNDLED_FONTS_PATH = join('Browser', 'fonts')

# SYSTEM TOR PORTS
# Note: On Windows, Tor can be installed via Chocolatey or run standalone
DEFAULT_SOCKS_PORT = 9050
DEFAULT_CONTROL_PORT = 9051

# TBB TOR PORTS (when using Tor Browser's bundled Tor)
TBB_SOCKS_PORT = 9150
TBB_CONTROL_PORT = 9151

# STEM PORTS (when launching Tor via Stem library)
# Pick 9250, 9251 to avoid conflict with system and TBB Tor
STEM_SOCKS_PORT = 9250
STEM_CONTROL_PORT = 9251

# Known SOCKS ports that Tor Browser expects
KNOWN_SOCKS_PORTS = [DEFAULT_SOCKS_PORT, TBB_SOCKS_PORT]

# Preferences for banning ports in Tor Browser
PORT_BAN_PREFS = [
    "extensions.torbutton.banned_ports",
    "network.security.ports.banned"
]

# Test constants
CHECK_TPO_URL = "http://check.torproject.org"
CHECK_TPO_HOST = "check.torproject.org"
TEST_URL = CHECK_TPO_URL
ABOUT_TOR_URL = "about:tor"

# Which tor process/binary to use
LAUNCH_NEW_TBB_TOR = 0  # Not supported (would launch tor in TBB as new process)
USE_RUNNING_TOR = 1     # Use system tor or tor started with stem
USE_STEM = 2            # Use tor started with Stem library

# CI/CD detection
TRAVIS = "CI" in environ and "TRAVIS" in environ
GITHUB_ACTIONS = "GITHUB_ACTIONS" in environ
APPVEYOR = "APPVEYOR" in environ

# Package directory
TB_SELENIUM_DIR = dirname(abspath(__file__))
TEST_DATA_DIR = join(TB_SELENIUM_DIR, "test", "test_data")
LOCAL_JS_TEST_URL = 'file:///' + join(TEST_DATA_DIR, "js_test.html").replace('\\', '/')
LOCAL_IMG_TEST_URL = 'file:///' + join(TEST_DATA_DIR, "img_test.html").replace('\\', '/')


def get_tbb_paths_for_dir(tbb_dir):
    """
    Get all relevant paths for a Tor Browser installation directory.

    Args:
        tbb_dir: Path to the Tor Browser directory

    Returns:
        dict with keys: fx_binary, profile, tor_binary, tor_data, browser_dir
    """
    return {
        'fx_binary': join(tbb_dir, DEFAULT_TBB_FX_BINARY_PATH),
        'profile': join(tbb_dir, DEFAULT_TBB_PROFILE_PATH),
        'tor_binary': join(tbb_dir, DEFAULT_TOR_BINARY_PATH),
        'tor_data': join(tbb_dir, DEFAULT_TOR_DATA_PATH),
        'browser_dir': join(tbb_dir, DEFAULT_TBB_BROWSER_DIR),
        'tor_binary_dir': join(tbb_dir, DEFAULT_TOR_BINARY_DIR),
    }
