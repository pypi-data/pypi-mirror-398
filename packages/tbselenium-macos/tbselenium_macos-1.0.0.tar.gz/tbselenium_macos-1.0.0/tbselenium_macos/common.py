"""
Common constants and paths for Tor Browser Selenium on macOS.

macOS Tor Browser uses an .app bundle structure:
    Tor Browser.app/
    ├── Contents/
    │   ├── MacOS/
    │   │   └── firefox       (Firefox binary)
    │   ├── Resources/
    │   │   ├── TorBrowser/
    │   │   │   ├── Tor/
    │   │   │   │   └── tor   (Tor binary)
    │   │   │   └── Data/
    │   │   │       ├── Browser/
    │   │   │       │   └── profile.default/  (Default profile)
    │   │   │       └── Tor/  (Tor data directory)
    │   │   └── browser/      (Browser resources)
    │   └── Info.plist
"""

from os.path import join, dirname, abspath
from os import environ
import sys

# Ensure we're running on macOS for production use
IS_MACOS = sys.platform == 'darwin'

# macOS .app bundle structure paths (relative to .app directory)
# The .app is typically at: /Applications/Tor Browser.app/
# or extracted to: ~/Downloads/Tor Browser.app/

# Default paths relative to the .app bundle Contents directory
DEFAULT_TBB_CONTENTS_DIR = 'Contents'
DEFAULT_TBB_MACOS_DIR = join(DEFAULT_TBB_CONTENTS_DIR, 'MacOS')
DEFAULT_TBB_RESOURCES_DIR = join(DEFAULT_TBB_CONTENTS_DIR, 'Resources')

# Firefox binary is in Contents/MacOS/firefox
DEFAULT_TBB_FX_BINARY_PATH = join(DEFAULT_TBB_MACOS_DIR, 'firefox')

# TorBrowser directory inside Resources
DEFAULT_TBB_TORBROWSER_DIR = join(DEFAULT_TBB_RESOURCES_DIR, 'TorBrowser')

# Tor binary directory and path
DEFAULT_TOR_BINARY_DIR = join(DEFAULT_TBB_TORBROWSER_DIR, 'Tor')
DEFAULT_TOR_BINARY_PATH = join(DEFAULT_TOR_BINARY_DIR, 'tor')

# Data directories
DEFAULT_TBB_DATA_DIR = join(DEFAULT_TBB_TORBROWSER_DIR, 'Data')
DEFAULT_TBB_PROFILE_PATH = join(DEFAULT_TBB_DATA_DIR, 'Browser', 'profile.default')
DEFAULT_TOR_DATA_PATH = join(DEFAULT_TBB_DATA_DIR, 'Tor')

# GeoIP file paths (needed when using a custom DataDirectory)
DEFAULT_GEOIP_PATH = join(DEFAULT_TOR_DATA_PATH, 'geoip')
DEFAULT_GEOIP6_PATH = join(DEFAULT_TOR_DATA_PATH, 'geoip6')

# Browser directory (equivalent to Linux's "Browser" dir)
# On macOS, this is Contents/MacOS for binary or Contents/Resources for resources
DEFAULT_TBB_BROWSER_DIR = DEFAULT_TBB_MACOS_DIR

# Changelog path (if exists)
TB_CHANGE_LOG_PATH = join(DEFAULT_TBB_TORBROWSER_DIR, 'Docs', 'ChangeLog.txt')

# NoScript XPI path in the default profile
DEFAULT_TBB_NO_SCRIPT_XPI_PATH = join(
    DEFAULT_TBB_PROFILE_PATH, 'extensions',
    '{73a6fe31-595d-460b-a920-fcc0f8843232}.xpi')

# SYSTEM TOR PORTS (from Homebrew: brew install tor)
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

# Package directory
TB_SELENIUM_DIR = dirname(abspath(__file__))
TEST_DATA_DIR = join(TB_SELENIUM_DIR, "test", "test_data")
LOCAL_JS_TEST_URL = 'file://' + join(TEST_DATA_DIR, "js_test.html")
LOCAL_IMG_TEST_URL = 'file://' + join(TEST_DATA_DIR, "img_test.html")


def get_tbb_paths_for_app(app_path):
    """
    Get all relevant paths for a Tor Browser .app bundle.

    Args:
        app_path: Path to the Tor Browser.app directory

    Returns:
        dict with keys: fx_binary, profile, tor_binary, tor_data, browser_dir
    """
    return {
        'fx_binary': join(app_path, DEFAULT_TBB_FX_BINARY_PATH),
        'profile': join(app_path, DEFAULT_TBB_PROFILE_PATH),
        'tor_binary': join(app_path, DEFAULT_TOR_BINARY_PATH),
        'tor_data': join(app_path, DEFAULT_TOR_DATA_PATH),
        'browser_dir': join(app_path, DEFAULT_TBB_BROWSER_DIR),
        'resources_dir': join(app_path, DEFAULT_TBB_RESOURCES_DIR),
        'tor_binary_dir': join(app_path, DEFAULT_TOR_BINARY_DIR),
    }
