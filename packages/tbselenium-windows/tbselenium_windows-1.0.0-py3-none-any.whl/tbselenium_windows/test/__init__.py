"""
Test package for Tor Browser Selenium on Windows.

Environment variable TBB_PATH must point to the Tor Browser directory.
Example: set TBB_PATH=C:\Users\User\Desktop\Tor Browser
"""

from os import environ
from os.path import abspath, isdir
from tbselenium_windows.exceptions import TBTestEnvVarError

# Environment variable that points to TBB directory
TBB_PATH = environ.get('TBB_PATH')

if TBB_PATH is None:
    raise TBTestEnvVarError(
        "Environment variable `TBB_PATH` can't be found. "
        "Please set it to your Tor Browser path, e.g.:\n"
        "set TBB_PATH=C:\\Users\\User\\Desktop\\Tor Browser"
    )

TBB_PATH = abspath(TBB_PATH)
if not isdir(TBB_PATH):
    raise TBTestEnvVarError(f"TBB_PATH is not a directory: {TBB_PATH}")
