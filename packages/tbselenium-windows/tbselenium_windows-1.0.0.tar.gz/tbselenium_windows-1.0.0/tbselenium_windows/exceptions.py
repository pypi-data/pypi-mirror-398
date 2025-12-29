"""
Custom exceptions for Tor Browser Selenium on Windows.
"""


class TBDriverPathError(Exception):
    """Raised when there is an issue with Tor Browser paths."""
    pass


class TBTestEnvVarError(Exception):
    """Raised when required test environment variables are missing."""
    pass


class TBDriverPortError(Exception):
    """Raised when there is an issue with port configuration."""
    pass


class TBDriverConfigError(Exception):
    """Raised when there is an invalid configuration."""
    pass


class TimeExceededError(Exception):
    """Raised when an operation times out."""
    pass


class TorBrowserDriverInitError(Exception):
    """Raised when the TorBrowserDriver fails to initialize."""
    pass


class StemLaunchError(Exception):
    """Raised when Tor fails to launch via Stem."""
    pass


class PlatformNotSupportedError(Exception):
    """Raised when the platform is not Windows."""
    pass
