"""
Tor Browser Driver for Windows.

This module provides the TorBrowserDriver class, which extends Selenium's
Firefox WebDriver to automate Tor Browser on Windows.

Key differences from the Linux/macOS versions:
1. Uses Windows directory structure with .exe extensions
2. Uses PATH for DLL loading instead of LD_LIBRARY_PATH
3. No FONTCONFIG environment variables needed
4. Uses os.pathsep (;) for path separation

Example usage:
    from tbselenium_windows.tbdriver import TorBrowserDriver

    # Using Tor Browser directory path
    with TorBrowserDriver("C:\\Users\\User\\Desktop\\Tor Browser") as driver:
        driver.load_url("https://check.torproject.org")
        print(driver.title)
"""

import shutil
import sys
import os
from os import environ, chdir
from os.path import isdir, isfile, join, abspath, dirname
from time import sleep
from http.client import CannotSendRequest

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxDriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException

import tbselenium_windows.common as cm
from tbselenium_windows.utils import prepend_to_env_var, is_busy, get_geckodriver_path
from tbselenium_windows.exceptions import (
    TBDriverConfigError, TBDriverPortError, TBDriverPathError)


# Default banned ports in Tor Browser
DEFAULT_BANNED_PORTS = "9050,9051,9150,9151"

# Find geckodriver in PATH
GECKO_DRIVER_EXE_PATH = get_geckodriver_path() or shutil.which("geckodriver")


class TorBrowserDriver(FirefoxDriver):
    """
    Extend Firefox WebDriver to automate Tor Browser on Windows.

    This class handles the Windows-specific directory structure and
    provides a Selenium interface for controlling Tor Browser.

    Args:
        tbb_path: Path to Tor Browser directory (e.g., "C:\\Tor Browser")
        tor_cfg: Tor configuration mode (USE_RUNNING_TOR or USE_STEM)
        tbb_fx_binary_path: Direct path to firefox.exe (optional)
        tbb_profile_path: Path to browser profile (optional)
        tbb_logfile_path: Path for browser logs (optional)
        tor_data_dir: Custom Tor data directory (optional)
        executable_path: Path to geckodriver.exe
        pref_dict: Dictionary of custom Firefox preferences
        socks_port: SOCKS proxy port (default: 9050)
        control_port: Tor control port (default: 9051)
        extensions: List of extension .xpi files to install
        default_bridge_type: Tor bridge type to use
        headless: Run browser in headless mode
        options: Custom Firefox Options object
        use_custom_profile: Whether to use a persistent profile. When True,
            Firefox writes directly to the profile directory. Ensure the
            directory is writable.
        geckodriver_port: Port for geckodriver (0 = random)
        marionette_port: Port for Marionette (0 = don't set, only used with use_custom_profile)
    """

    def __init__(self,
                 tbb_path="",
                 tor_cfg=cm.USE_RUNNING_TOR,
                 tbb_fx_binary_path="",
                 tbb_profile_path="",
                 tbb_logfile_path="",
                 tor_data_dir="",
                 executable_path=GECKO_DRIVER_EXE_PATH,
                 pref_dict=None,
                 socks_port=None,
                 control_port=None,
                 extensions=None,
                 default_bridge_type="",
                 headless=False,
                 options=None,
                 use_custom_profile=False,
                 geckodriver_port=0,
                 marionette_port=0):
        """Initialize the TorBrowserDriver."""

        # Handle mutable default arguments
        if pref_dict is None:
            pref_dict = {}
        if extensions is None:
            extensions = []

        # use_custom_profile: whether to launch from and *write to* the given profile
        # False: copy the profile to a tempdir; remove the temp folder on quit
        # True: use the given profile without copying. This can be used to keep
        # a stateful profile across different launches of the Tor Browser.
        # Uses Firefox's `-profile` command line parameter under the hood

        self.use_custom_profile = use_custom_profile
        self.tor_cfg = tor_cfg

        # Setup paths for Windows directory structure
        self.setup_tbb_paths(tbb_path, tbb_fx_binary_path,
                             tbb_profile_path, tor_data_dir)

        self.options = Options() if options is None else options
        install_noscript = False

        USE_DEPRECATED_PROFILE_METHOD = True
        if self.use_custom_profile:
            # Launch from and write to this custom profile
            self.options.add_argument("-profile")
            self.options.add_argument(self.tbb_profile_path)
        elif USE_DEPRECATED_PROFILE_METHOD:
            # Launch from this custom profile (stateless mode)
            self.options.profile = self.tbb_profile_path
        else:
            # Launch with no profile at all.
            # NoScript does not come installed on browsers launched by this
            # method, so we install it ourselves
            install_noscript = True

        self.init_ports(tor_cfg, socks_port, control_port)
        self.init_prefs(pref_dict, default_bridge_type)
        self.export_env_vars()

        if use_custom_profile:
            service_args = []
            if marionette_port > 0:
                service_args = ["--marionette-port", str(marionette_port)]
            tbb_service = Service(
                executable_path=executable_path,
                log_output=tbb_logfile_path,
                service_args=service_args,
                port=geckodriver_port
            )
        else:
            tbb_service = Service(
                executable_path=executable_path,
                log_output=tbb_logfile_path,
                port=geckodriver_port
            )

        # Set the Firefox binary path
        self.options.binary = self.tbb_fx_binary_path

        # Add headless mode if requested
        if headless:
            self.options.add_argument('-headless')

        # Initialize the Firefox driver
        super(TorBrowserDriver, self).__init__(
            service=tbb_service,
            options=self.options,
        )

        self.is_running = True
        self.install_extensions(extensions, install_noscript)
        self.temp_profile_dir = self.capabilities.get("moz:profile")
        sleep(1)

    def install_extensions(self, extensions, install_noscript):
        """
        Install the given extensions to the profile we are launching.

        Args:
            extensions: List of .xpi file paths
            install_noscript: Whether to install NoScript from TBB
        """
        if install_noscript:
            no_script_xpi = join(
                self.tbb_path, cm.DEFAULT_TBB_NO_SCRIPT_XPI_PATH)
            if isfile(no_script_xpi):
                extensions.append(no_script_xpi)

        for extension in extensions:
            if isfile(extension):
                self.install_addon(extension)

    def init_ports(self, tor_cfg, socks_port, control_port):
        """
        Check SOCKS port and Tor config inputs.

        Args:
            tor_cfg: Tor configuration mode
            socks_port: SOCKS proxy port
            control_port: Tor control port

        Raises:
            TBDriverConfigError: If configuration is invalid
            TBDriverPortError: If SOCKS port is not listening
        """
        if tor_cfg == cm.LAUNCH_NEW_TBB_TOR:
            raise TBDriverConfigError(
                "`LAUNCH_NEW_TBB_TOR` config is not supported anymore. "
                "Use USE_RUNNING_TOR or USE_STEM")

        if tor_cfg not in [cm.USE_RUNNING_TOR, cm.USE_STEM]:
            raise TBDriverConfigError(f"Unrecognized tor_cfg: {tor_cfg}")

        if socks_port is None:
            if tor_cfg == cm.USE_RUNNING_TOR:
                socks_port = cm.DEFAULT_SOCKS_PORT  # 9050
            else:
                socks_port = cm.STEM_SOCKS_PORT

        if control_port is None:
            if tor_cfg == cm.USE_RUNNING_TOR:
                control_port = cm.DEFAULT_CONTROL_PORT
            else:
                control_port = cm.STEM_CONTROL_PORT

        if not is_busy(socks_port):
            raise TBDriverPortError(
                f"SOCKS port {socks_port} is not listening. "
                "Make sure Tor is running. On Windows, you can:\n"
                "1. Start Tor Browser and use port 9150\n"
                "2. Install Tor via Chocolatey: choco install tor\n"
                "3. Use Stem to launch Tor from the bundle")

        self.socks_port = socks_port
        self.control_port = control_port

    def setup_tbb_paths(self, tbb_path, tbb_fx_binary_path, tbb_profile_path,
                        tor_data_dir):
        """
        Update instance variables based on the passed paths.

        TorBrowserDriver can be initialized by passing either:
        1) path to TBB directory (tbb_path)
        2) path to TBB directory and profile (tbb_path, tbb_profile_path)
        3) path to TBB's Firefox binary and profile (tbb_fx_binary_path, tbb_profile_path)

        Args:
            tbb_path: Path to Tor Browser directory
            tbb_fx_binary_path: Path to firefox.exe
            tbb_profile_path: Path to profile directory
            tor_data_dir: Path to Tor data directory

        Raises:
            TBDriverPathError: If paths are invalid
        """
        if not (tbb_path or (tbb_fx_binary_path and tbb_profile_path)):
            raise TBDriverPathError(
                "Either TBB path or Firefox profile and binary path "
                f"should be provided: {tbb_path}")

        if tbb_path:
            if not isdir(tbb_path):
                raise TBDriverPathError(
                    f"TBB path is not a directory: {tbb_path}")

            # Windows: Firefox binary is in Browser/firefox.exe
            tbb_fx_binary_path = join(tbb_path, cm.DEFAULT_TBB_FX_BINARY_PATH)
        else:
            # If binary is provided directly, derive tbb_path from it
            # Binary is at: Tor Browser/Browser/firefox.exe
            # So tbb_path is: Tor Browser/
            tbb_path = dirname(dirname(tbb_fx_binary_path))

        if not tbb_profile_path:
            # Fall back to the default profile path in TBB
            tbb_profile_path = join(tbb_path, cm.DEFAULT_TBB_PROFILE_PATH)

        if not isfile(tbb_fx_binary_path):
            raise TBDriverPathError(
                f"Invalid Firefox binary: {tbb_fx_binary_path}")

        if not isdir(tbb_profile_path):
            raise TBDriverPathError(
                f"Invalid Firefox profile dir: {tbb_profile_path}")

        self.tbb_path = abspath(tbb_path)
        self.tbb_profile_path = abspath(tbb_profile_path)
        self.tbb_fx_binary_path = abspath(tbb_fx_binary_path)
        self.tbb_browser_dir = abspath(join(tbb_path, cm.DEFAULT_TBB_BROWSER_DIR))

        if tor_data_dir:
            self.tor_data_dir = tor_data_dir
        else:
            # Fall back to default tor data dir in TBB
            self.tor_data_dir = join(tbb_path, cm.DEFAULT_TOR_DATA_PATH)

        # Change to the browser directory for finding bundled resources
        chdir(self.tbb_browser_dir)

    def load_url(self, url, wait_on_page=0, wait_for_page_body=False):
        """
        Load a URL and wait before returning.

        If you query/manipulate DOM or execute a script immediately
        after the page load, you may get the following error:
            "WebDriverException: Message: waiting for doc.body failed"

        To prevent this, set wait_for_page_body to True, and driver
        will wait for the page body to become available before it returns.

        Args:
            url: URL to load
            wait_on_page: Seconds to wait after page load
            wait_for_page_body: Wait for page body element
        """
        self.get(url)
        if wait_for_page_body:
            # If the page can't be loaded this will raise a TimeoutException
            self.find_element_by("body", find_by=By.TAG_NAME)
        sleep(wait_on_page)

    def find_element_by(self, selector, timeout=30, find_by=By.CSS_SELECTOR):
        """
        Wait until the element matching the selector appears or timeout.

        Args:
            selector: CSS selector or other selector string
            timeout: Maximum wait time in seconds
            find_by: Selector type (default: By.CSS_SELECTOR)

        Returns:
            WebElement: The found element
        """
        return WebDriverWait(self, timeout).until(
            EC.presence_of_element_located((find_by, selector)))

    def add_ports_to_fx_banned_ports(self, socks_port, control_port):
        """
        Add custom ports to Firefox's banned ports list.

        By default, ports 9050, 9051, 9150, 9151 are banned in TB.
        If we use a Tor process running on custom ports, we add SOCKS
        and control ports to the following prefs:
            network.security.ports.banned
            extensions.torbutton.banned_ports

        Args:
            socks_port: SOCKS proxy port
            control_port: Tor control port
        """
        if socks_port in cm.KNOWN_SOCKS_PORTS:
            return

        tb_prefs = self.options.preferences
        set_pref = self.options.set_preference

        for port_ban_pref in cm.PORT_BAN_PREFS:
            banned_ports = tb_prefs.get(port_ban_pref, DEFAULT_BANNED_PORTS)
            set_pref(port_ban_pref, f"{banned_ports},{socks_port},{control_port}")

    def set_tb_prefs_for_using_system_tor(self, control_port):
        """
        Set the preferences suggested by start-tor-browser script
        to run TB with system-installed Tor.

        We set these prefs for running with Tor started with Stem as well.

        Args:
            control_port: Tor control port
        """
        set_pref = self.options.set_preference

        # Prevent Tor Browser from running its own Tor process
        set_pref('extensions.torlauncher.start_tor', False)

        # Torbutton settings
        set_pref('extensions.torbutton.block_disk', False)
        set_pref('extensions.torbutton.custom.socks_host', '127.0.0.1')
        set_pref('extensions.torbutton.custom.socks_port', self.socks_port)
        set_pref('extensions.torbutton.inserted_button', True)
        set_pref('extensions.torbutton.launch_warning', False)
        set_pref('privacy.spoof_english', 2)
        set_pref('extensions.torbutton.loglevel', 2)
        set_pref('extensions.torbutton.logmethod', 0)
        set_pref('extensions.torbutton.settings_method', 'custom')
        set_pref('extensions.torbutton.use_privoxy', False)

        # Torlauncher settings
        set_pref('extensions.torlauncher.control_port', control_port)
        set_pref('extensions.torlauncher.loglevel', 2)
        set_pref('extensions.torlauncher.logmethod', 0)
        set_pref('extensions.torlauncher.prompt_at_startup', False)

        # Disable XPI signature checking (for custom extensions)
        set_pref('xpinstall.signatures.required', False)
        set_pref('xpinstall.whitelist.required', False)

    def init_prefs(self, pref_dict, default_bridge_type):
        """
        Initialize Firefox preferences for Tor Browser.

        Args:
            pref_dict: Dictionary of custom preferences
            default_bridge_type: Tor bridge type to use
        """
        self.add_ports_to_fx_banned_ports(self.socks_port, self.control_port)
        set_pref = self.options.set_preference

        # Startup preferences
        set_pref('browser.startup.page', "0")
        set_pref('torbrowser.settings.quickstart.enabled', True)
        set_pref('browser.startup.homepage', 'about:newtab')
        set_pref('extensions.torlauncher.prompt_at_startup', 0)

        # WebDriver load strategy
        set_pref('webdriver.load.strategy', 'normal')

        # Disable auto-update
        set_pref('app.update.enabled', False)
        set_pref('extensions.torbutton.versioncheck_enabled', False)

        # Bridge configuration
        if default_bridge_type:
            set_pref('extensions.torlauncher.default_bridge_type',
                     default_bridge_type)

        # Suppress language prompts
        set_pref('extensions.torbutton.prompted_language', True)
        set_pref('intl.language_notification.shown', True)

        # Configure Firefox to use Tor SOCKS proxy
        set_pref('network.proxy.socks_port', self.socks_port)
        set_pref('extensions.torbutton.socks_port', self.socks_port)
        set_pref('extensions.torlauncher.control_port', self.control_port)

        # Set up for system Tor
        self.set_tb_prefs_for_using_system_tor(self.control_port)

        # Apply custom preferences (these override above preferences)
        for pref_name, pref_val in pref_dict.items():
            set_pref(pref_name, pref_val)

    def export_env_vars(self):
        """
        Setup environment variables for Tor Browser on Windows.

        On Windows:
        - Uses PATH for DLL loading (no LD_LIBRARY_PATH)
        - Sets HOME to the browser directory
        - Adds browser and Tor directories to PATH
        """
        tor_binary_dir = join(self.tbb_path, cm.DEFAULT_TOR_BINARY_DIR)

        # On Windows, add the Tor directory to PATH for DLL loading
        # Windows uses PATH for DLL resolution
        prepend_to_env_var("PATH", tor_binary_dir)
        prepend_to_env_var("PATH", self.tbb_browser_dir)

        # Set HOME to browser directory (some Firefox internals may use this)
        environ["HOME"] = self.tbb_browser_dir

    @property
    def is_connection_error_page(self):
        """
        Check if we get a connection error page.

        Returns:
            bool: True if on a connection error page
        """
        return "ENTITY connectionFailure.title" in self.page_source

    def clean_up_profile_dirs(self):
        """
        Remove temporary profile directories.

        Only called when WebDriver.quit() is interrupted.
        """
        if self.use_custom_profile:
            # Don't remove the profile if we are writing into it (stateful mode)
            return

        if self.temp_profile_dir and isdir(self.temp_profile_dir):
            shutil.rmtree(self.temp_profile_dir)

    def quit(self):
        """
        Quit the driver. Clean up if the parent's quit fails.
        """
        self.is_running = False
        try:
            super(TorBrowserDriver, self).quit()
        except (CannotSendRequest, AttributeError, WebDriverException):
            try:
                # Clean up if webdriver.quit() throws
                if hasattr(self, "service"):
                    self.service.stop()
                if hasattr(self, "options") and hasattr(self.options, "profile"):
                    self.clean_up_profile_dirs()
            except Exception as e:
                print(f"[tbselenium_windows] Exception while quitting: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.quit()
