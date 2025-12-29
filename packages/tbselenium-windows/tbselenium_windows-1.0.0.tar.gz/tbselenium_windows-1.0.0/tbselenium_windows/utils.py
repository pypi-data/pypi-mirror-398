"""
Utility functions for Tor Browser Selenium on Windows.

This module provides Windows-specific utilities including:
- Environment variable management using Windows conventions
- Tor process launching with Stem
- Browser preference management
- Security level controls
"""

import os
import sys
import tempfile
import json
from os import environ
from os.path import dirname, isfile, join
from time import sleep

import tbselenium_windows.common as cm
from tbselenium_windows.exceptions import StemLaunchError

from selenium.webdriver.common.utils import is_connectable
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import JavascriptException, NoSuchElementException


# Optional imports - only needed for some features
try:
    from stem.process import launch_tor_with_config
    HAS_STEM = True
except ImportError:
    HAS_STEM = False


# Security slider settings (same as Tor Browser on other platforms)
TB_SECURITY_LEVEL_STANDARD = 'standard'
TB_SECURITY_LEVEL_SAFER = 'safer'
TB_SECURITY_LEVEL_SAFEST = 'safest'

TB_SECURITY_LEVELS = [
    TB_SECURITY_LEVEL_STANDARD,
    TB_SECURITY_LEVEL_SAFER,
    TB_SECURITY_LEVEL_SAFEST
]


def is_windows():
    """Check if the current platform is Windows."""
    return sys.platform == 'win32'


def is_busy(port_no):
    """
    Return True if the given port is already in use.

    Args:
        port_no: The port number to check

    Returns:
        bool: True if port is in use, False otherwise
    """
    return is_connectable(port_no)


def prepend_to_env_var(env_var, new_value):
    """
    Add the given value to the beginning of the environment variable.

    Uses os.pathsep for platform-independent path separator.
    On Windows, this is ';' (semicolon).

    Args:
        env_var: Name of the environment variable
        new_value: Value to prepend
    """
    path_sep = os.pathsep  # ';' on Windows, ':' on Unix

    if environ.get(env_var, None):
        existing_paths = environ[env_var].split(path_sep)
        if new_value not in existing_paths:
            environ[env_var] = f"{new_value}{path_sep}{environ[env_var]}"
    else:
        environ[env_var] = new_value


def read_file(file_path, mode='r'):
    """
    Read and return file content.

    Args:
        file_path: Path to the file
        mode: File open mode (default: 'r')

    Returns:
        str: File contents
    """
    with open(file_path, mode, encoding='utf-8') as f:
        content = f.read()
    return content


def launch_tbb_tor_with_stem(tbb_path=None, torrc=None, tor_binary=None):
    """
    Launch the Tor binary using Stem library.

    This function launches Tor from either:
    1. The Tor binary bundled in Tor Browser
    2. A custom Tor binary path

    When tbb_path is provided, GeoIP file paths are automatically configured
    in the torrc if they exist and aren't already set. This is necessary when
    using a custom DataDirectory, as Tor needs explicit paths to the GeoIP files.

    Args:
        tbb_path: Path to Tor Browser directory
        torrc: Custom Tor configuration dictionary
        tor_binary: Direct path to Tor binary (optional)

    Returns:
        stem.process.Process: The Tor process launched by Stem

    Raises:
        StemLaunchError: If Tor cannot be launched
    """
    if not HAS_STEM:
        raise StemLaunchError("Stem library is not installed. "
                              "Install with: pip install stem")

    if not (tor_binary or tbb_path):
        raise StemLaunchError("Either pass tbb_path or tor_binary")

    if not tor_binary and tbb_path:
        tor_binary = join(tbb_path, cm.DEFAULT_TOR_BINARY_PATH)

    if not isfile(tor_binary):
        raise StemLaunchError(f"Invalid Tor binary: {tor_binary}")

    # On Windows, add the Tor directory to PATH for DLL loading
    # Windows uses PATH for DLL resolution unlike Unix's LD_LIBRARY_PATH
    prepend_to_env_var("PATH", dirname(tor_binary))

    if torrc is None:
        torrc = {
            'ControlPort': str(cm.STEM_CONTROL_PORT),
            'SOCKSPort': str(cm.STEM_SOCKS_PORT),
            'DataDirectory': tempfile.mkdtemp()
        }

    # Add GeoIP paths if tbb_path is provided and files exist
    if tbb_path:
        geoip_path = join(tbb_path, cm.DEFAULT_GEOIP_PATH)
        geoip6_path = join(tbb_path, cm.DEFAULT_GEOIP6_PATH)

        if 'GeoIPFile' not in torrc and isfile(geoip_path):
            torrc['GeoIPFile'] = geoip_path
        if 'GeoIPv6File' not in torrc and isfile(geoip6_path):
            torrc['GeoIPv6File'] = geoip6_path

    return launch_tor_with_config(config=torrc, tor_cmd=tor_binary)


def set_tbb_pref(driver, name, value):
    """
    Set a Tor Browser preference using JavaScript in chrome context.

    Args:
        driver: TorBrowserDriver instance
        name: Preference name
        value: Preference value (bool, str, or int)
    """
    try:
        script = 'Services.prefs.'
        if isinstance(value, bool):
            script += 'setBoolPref'
        elif isinstance(value, str):
            script += 'setStringPref'
        else:
            script += 'setIntPref'
        script += f'({json.dumps(name)}, {json.dumps(value)});'

        with driver.context(driver.CONTEXT_CHROME):
            driver.execute_script(script)
    except Exception:
        raise
    finally:
        driver.set_context(driver.CONTEXT_CONTENT)


def set_security_level(driver, level):
    """
    Set the Tor Browser security level (Standard, Safer, Safest).

    Args:
        driver: TorBrowserDriver instance
        level: One of TB_SECURITY_LEVEL_STANDARD, TB_SECURITY_LEVEL_SAFER,
               or TB_SECURITY_LEVEL_SAFEST

    Raises:
        ValueError: If level is not a valid security level
    """
    if level not in TB_SECURITY_LEVELS:
        raise ValueError(f"Invalid Tor Browser security setting: {level}")
    open_security_level_panel(driver)
    click_to_set_security_level(driver, level)


def js_click_by_id(driver, element_id):
    """
    Execute a script to find and click an element with the given ID.

    Args:
        driver: WebDriver instance
        element_id: ID of the element to click
    """
    driver.execute_script(
        f'document.getElementById("{element_id}").click();')


def open_security_level_panel(driver):
    """
    Click on the Shield (security settings) and "Change" buttons to
    open the security level settings on the about:preferences#privacy page.

    Based on:
    https://gitlab.torproject.org/tpo/applications/tor-browser-bundle-testsuite/-/blob/main/marionette/tor_browser_tests/test_security_level_ui.py
    """
    # Switch to chrome context since buttons we need to click are
    # part of the browser UI, not the content page.
    with driver.context('chrome'):
        # Emulate a click on the Shield button next to the address bar.
        # Use execute_script() because driver.find_element
        # and similar methods don't seem to match these elements
        # in chrome context.
        js_click_by_id(driver, 'security-level-button')

        # Emulate a click on the Change (security settings) button
        try:
            # For 12.5a7 and later
            js_click_by_id(driver, 'securityLevel-settings')
        except JavascriptException:
            # For 12.5a6 and earlier
            js_click_by_id(driver, 'securityLevel-advancedSecuritySettings')


def click_to_set_security_level(driver, level):
    """
    Click the radio button to set the desired security level.

    Args:
        driver: TorBrowserDriver instance
        level: Security level to set
    """
    assert level in TB_SECURITY_LEVELS

    with driver.context('content'):
        # Make sure the security level panel is highlighted/scrolled to
        spotlight = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "spotlight"))
        )
        assert spotlight.get_attribute("data-subcategory") == "securitylevel"

        # Click on the radio button for the desired security level
        try:
            # 12.5a7 and later
            level_idx = TB_SECURITY_LEVELS.index(level) + 1
            # CSS selector for the radio button
            driver.find_element(
                By.CSS_SELECTOR,
                f'vbox.securityLevel-radio-option:nth-child({level_idx}) >'
                ' radio:nth-child(1)').click()
        except NoSuchElementException:
            # Older versions
            driver.find_element(
                By.CSS_SELECTOR, f'#securityLevel-vbox-{level} radio').click()


def disable_js(driver):
    """
    Disable JavaScript in the browser.

    Args:
        driver: TorBrowserDriver instance
    """
    set_tbb_pref(driver, "javascript.enabled", False)
    sleep(1)  # Wait for the pref to update


def enable_js(driver):
    """
    Enable JavaScript in the browser.

    Args:
        driver: TorBrowserDriver instance
    """
    set_tbb_pref(driver, "javascript.enabled", True)
    sleep(1)  # Wait for the pref to update


def get_js_status_text(driver):
    """
    Return the text of the JS status element.

    Args:
        driver: WebDriver instance

    Returns:
        str: Inner text of the element with ID 'js'
    """
    return driver.find_element(By.ID, 'js').get_attribute("innerText")


def find_tor_browser_dir():
    """
    Attempt to find Tor Browser in common locations on Windows.

    Returns:
        str or None: Path to Tor Browser directory if found, None otherwise
    """
    # Common installation paths on Windows
    common_paths = [
        os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop', 'Tor Browser'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads', 'Tor Browser'),
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Tor Browser'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Tor Browser'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Tor Browser'),
        "C:\\Tor Browser",
        "D:\\Tor Browser",
    ]

    for path in common_paths:
        if path and os.path.isdir(path):
            # Verify it's actually a Tor Browser directory
            firefox_exe = os.path.join(path, 'Browser', 'firefox.exe')
            if os.path.isfile(firefox_exe):
                return path

    return None


def get_geckodriver_path():
    """
    Find the geckodriver executable on Windows.

    Checks:
    1. System PATH
    2. Common locations

    Returns:
        str or None: Path to geckodriver if found
    """
    import shutil

    # Check system PATH
    geckodriver = shutil.which("geckodriver")
    if geckodriver:
        return geckodriver

    # Also try with .exe extension explicitly
    geckodriver = shutil.which("geckodriver.exe")
    if geckodriver:
        return geckodriver

    # Check common locations on Windows
    common_paths = [
        os.path.join(os.environ.get('USERPROFILE', ''), 'geckodriver.exe'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads', 'geckodriver.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'geckodriver.exe'),
        "C:\\geckodriver.exe",
        "C:\\WebDriver\\geckodriver.exe",
    ]

    for path in common_paths:
        if path and os.path.isfile(path):
            return path

    return None
