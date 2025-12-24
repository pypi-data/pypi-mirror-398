"""
Pytest configuration for Tor Browser Selenium on macOS.

This module provides session-level fixtures for launching Tor
and managing test resources.
"""

import tempfile
from shutil import rmtree

import tbselenium_macos.common as cm
from tbselenium_macos.utils import is_busy
from tbselenium_macos.test.fixtures import launch_tbb_tor_with_stem_fixture
from tbselenium_macos.test import TBB_PATH

# Store test configuration
test_conf = {}


def launch_tor():
    """
    Launch Tor using Stem if not already running.

    Returns:
        tuple: (temp_data_dir, tor_process)
    """
    tor_process = None
    temp_data_dir = tempfile.mkdtemp()
    torrc = {
        'ControlPort': str(cm.STEM_CONTROL_PORT),
        'SOCKSPort': str(cm.STEM_SOCKS_PORT),
        'DataDirectory': temp_data_dir
    }

    if not is_busy(cm.STEM_SOCKS_PORT):
        try:
            tor_process = launch_tbb_tor_with_stem_fixture(
                tbb_path=TBB_PATH, torrc=torrc)
        except Exception as e:
            print(f"Could not launch Tor via Stem: {e}")
            print("Tests will use system Tor if available.")

    return (temp_data_dir, tor_process)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and before collection.

    On macOS, we don't need XVFB (no virtual display needed).
    We just launch Tor via Stem.
    """
    test_conf["temp_data_dir"], test_conf["tor_process"] = launch_tor()


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished.

    Cleanup Tor process and temporary directories.
    """
    tor_process = test_conf.get("tor_process")

    if tor_process:
        tor_process.kill()

    temp_data_dir = test_conf.get("temp_data_dir")
    if temp_data_dir:
        rmtree(temp_data_dir, ignore_errors=True)
