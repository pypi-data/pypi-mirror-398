"""
Test fixtures for Tor Browser Selenium on Windows.

Provides TBDriverFixture class with retry logic and helper functions
for robust testing.
"""

import os
import tempfile
from socket import error as socket_error
from http.client import CannotSendRequest

from selenium.common.exceptions import TimeoutException, WebDriverException

import tbselenium_windows.common as cm
from tbselenium_windows.tbdriver import TorBrowserDriver
from tbselenium_windows.exceptions import StemLaunchError, TorBrowserDriverInitError
from tbselenium_windows.utils import launch_tbb_tor_with_stem, is_busy, read_file


# Maximum number of retry attempts for flaky operations
MAX_FIXTURE_TRIES = 3

# Force TB logs during tests for debugging
FORCE_TB_LOGS_DURING_TESTS = True

# Error message patterns
ERR_MSG_NETERROR_NETTIMEOUT = "Reached error page: about:neterror?e=netTimeout"


class TBDriverFixture(TorBrowserDriver):
    """
    Extend TorBrowserDriver with fixtures for tests.

    This class adds:
    - Automatic retry logic for flaky initializations
    - Automatic Tor configuration detection
    - Debug logging to temporary files
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the test fixture with retry logic.

        Args:
            *args: Positional arguments for TorBrowserDriver
            **kwargs: Keyword arguments for TorBrowserDriver
        """
        self.change_default_tor_cfg(kwargs)
        last_err = None
        log_file = kwargs.get("tbb_logfile_path")

        for tries in range(MAX_FIXTURE_TRIES):
            try:
                return super(TBDriverFixture, self).__init__(*args, **kwargs)
            except (TimeoutException, WebDriverException, socket_error) as err:
                last_err = err
                print(f"\nERROR: TBDriver init error. Attempt {tries + 1}: {err}")

                if FORCE_TB_LOGS_DURING_TESTS and log_file:
                    try:
                        logs = read_file(log_file)
                        if logs:
                            print(f"TB logs:\n{logs}\n(End of TB logs)")
                    except Exception:
                        pass

                # Clean up failed initialization
                try:
                    super(TBDriverFixture, self).quit()
                except Exception:
                    pass
                continue

        # Raise if we didn't return yet
        if last_err:
            raise TorBrowserDriverInitError(
                f"Cannot initialize after {MAX_FIXTURE_TRIES} attempts: {last_err}")

    def __del__(self):
        """Clean up temporary log file if created."""
        if (FORCE_TB_LOGS_DURING_TESTS and
                hasattr(self, "log_file") and
                os.path.isfile(self.log_file)):
            try:
                os.remove(self.log_file)
            except Exception:
                pass

    def change_default_tor_cfg(self, kwargs):
        """
        Use the Tor process that we started at the beginning of tests.

        This makes tests faster and more robust against network issues
        since otherwise we'd have to launch a new Tor process for each test.

        If FORCE_TB_LOGS_DURING_TESTS is True, adds a log file arg to make
        it easier to debug failures.

        Args:
            kwargs: Keyword arguments dict to modify
        """
        # Use Stem Tor if it's running and no explicit config provided
        if kwargs.get("tor_cfg") is None and is_busy(cm.STEM_SOCKS_PORT):
            kwargs["tor_cfg"] = cm.USE_STEM
            kwargs["socks_port"] = cm.STEM_SOCKS_PORT
            kwargs["control_port"] = cm.STEM_CONTROL_PORT

        # Add log file for debugging if not provided
        if FORCE_TB_LOGS_DURING_TESTS and kwargs.get("tbb_logfile_path") is None:
            _, self.log_file = tempfile.mkstemp()
            kwargs["tbb_logfile_path"] = self.log_file

    def load_url_ensure(self, *args, **kwargs):
        """
        Make sure the requested URL is loaded. Retry if necessary.

        Args:
            *args: Positional arguments for load_url
            **kwargs: Keyword arguments for load_url

        Raises:
            WebDriverException: If page cannot be loaded after retries
        """
        last_err = None

        for tries in range(MAX_FIXTURE_TRIES):
            try:
                self.load_url(*args, **kwargs)
                if (self.current_url != "about:newtab" and
                        not self.is_connection_error_page):
                    return
            except (TimeoutException, CannotSendRequest) as err:
                last_err = err
                print(f"\nload_url timed out. Attempt {tries + 1}: {err}")
                continue
            except WebDriverException as wd_err:
                if ERR_MSG_NETERROR_NETTIMEOUT in str(wd_err):
                    last_err = wd_err
                    print(f"\nload_url timed out (WebDriverException). "
                          f"Attempt {tries + 1}: {wd_err}")
                    continue
                raise wd_err

        # Raise if we didn't return yet
        if last_err:
            raise WebDriverException(f"Can't load the page: {last_err}")


def launch_tbb_tor_with_stem_fixture(*args, **kwargs):
    """
    Launch Tor using Stem with retry logic.

    Args:
        *args: Positional arguments for launch_tbb_tor_with_stem
        **kwargs: Keyword arguments for launch_tbb_tor_with_stem

    Returns:
        stem.process.Process: The Tor process

    Raises:
        StemLaunchError: If Tor cannot be started after retries
    """
    last_err = None

    for tries in range(MAX_FIXTURE_TRIES):
        try:
            return launch_tbb_tor_with_stem(*args, **kwargs)
        except OSError as err:
            last_err = err
            print(f"\nlaunch_tor try {tries + 1}: {err}")

            if "timeout without success" in str(err):
                continue
            else:
                # Don't retry if this is not a timeout
                raise

    # Raise if we didn't return yet
    if last_err:
        raise StemLaunchError(f"Cannot start Tor: {last_err}")
