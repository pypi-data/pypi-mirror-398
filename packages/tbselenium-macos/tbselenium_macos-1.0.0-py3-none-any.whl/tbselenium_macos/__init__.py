"""
Tor Browser Selenium for macOS.

This package provides Selenium WebDriver automation for Tor Browser on macOS.
It handles the macOS-specific .app bundle structure and provides a clean
interface for controlling Tor Browser.

Basic Usage:
    from tbselenium_macos import TorBrowserDriver

    with TorBrowserDriver("/Applications/Tor Browser.app") as driver:
        driver.load_url("https://check.torproject.org")
        print(driver.title)

Requirements:
    - Tor Browser for macOS
    - Selenium 4+
    - geckodriver (install with: brew install geckodriver)
    - Running Tor (install with: brew install tor && brew services start tor)
      OR use Stem to launch Tor from the bundle
"""

__version__ = "1.0.0"
__author__ = "tbselenium-macos contributors"

from tbselenium_macos.tbdriver import TorBrowserDriver
from tbselenium_macos.common import (
    USE_RUNNING_TOR,
    USE_STEM,
    DEFAULT_SOCKS_PORT,
    DEFAULT_CONTROL_PORT,
    STEM_SOCKS_PORT,
    STEM_CONTROL_PORT,
)
from tbselenium_macos.utils import (
    launch_tbb_tor_with_stem,
    set_security_level,
    disable_js,
    enable_js,
    TB_SECURITY_LEVEL_STANDARD,
    TB_SECURITY_LEVEL_SAFER,
    TB_SECURITY_LEVEL_SAFEST,
)
from tbselenium_macos.exceptions import (
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
