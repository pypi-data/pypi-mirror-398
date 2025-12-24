"""
Test package for Tor Browser Selenium on macOS.

Environment variable TBB_PATH must point to the Tor Browser.app directory.
Example: export TBB_PATH="/Applications/Tor Browser.app"
"""

from os import environ
from os.path import abspath, isdir
from tbselenium_macos.exceptions import TBTestEnvVarError

# Environment variable that points to TBB directory
TBB_PATH = environ.get('TBB_PATH')

if TBB_PATH is None:
    raise TBTestEnvVarError(
        "Environment variable `TBB_PATH` can't be found. "
        "Please set it to your Tor Browser.app path, e.g.:\n"
        "export TBB_PATH=\"/Applications/Tor Browser.app\""
    )

TBB_PATH = abspath(TBB_PATH)
if not isdir(TBB_PATH):
    raise TBTestEnvVarError(f"TBB_PATH is not a directory: {TBB_PATH}")
