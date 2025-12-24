"""
Tests for browser-specific functionality on macOS.
"""

import os
import unittest

from tbselenium_macos.test import TBB_PATH
from tbselenium_macos.test.fixtures import TBDriverFixture
from tbselenium_macos import common as cm


class TorBrowserTest(unittest.TestCase):
    """Browser-specific tests."""

    def setUp(self):
        self.tb_driver = TBDriverFixture(TBB_PATH)

    def tearDown(self):
        self.tb_driver.quit()

    def test_should_use_correct_firefox_binary(self):
        """Test that the correct Firefox binary is used."""
        expected_binary = os.path.join(TBB_PATH, cm.DEFAULT_TBB_FX_BINARY_PATH)
        self.assertEqual(
            os.path.abspath(self.tb_driver.tbb_fx_binary_path),
            os.path.abspath(expected_binary))

    def test_should_have_correct_tbb_path(self):
        """Test that TBB path is set correctly."""
        self.assertEqual(
            os.path.abspath(self.tb_driver.tbb_path),
            os.path.abspath(TBB_PATH))

    def test_driver_is_running(self):
        """Test that driver is marked as running after init."""
        self.assertTrue(self.tb_driver.is_running)

    def test_driver_not_running_after_quit(self):
        """Test that driver is marked as not running after quit."""
        self.tb_driver.quit()
        self.assertFalse(self.tb_driver.is_running)

    def test_page_source_available(self):
        """Test that page source is available."""
        self.tb_driver.load_url_ensure(cm.ABOUT_TOR_URL)
        page_source = self.tb_driver.page_source
        self.assertIsNotNone(page_source)
        self.assertGreater(len(page_source), 0)

    def test_current_url_available(self):
        """Test that current URL is available."""
        self.tb_driver.load_url_ensure(cm.ABOUT_TOR_URL)
        current_url = self.tb_driver.current_url
        self.assertIsNotNone(current_url)


class TorBrowserMacOSPaths(unittest.TestCase):
    """Tests for macOS-specific paths."""

    def test_macos_fx_binary_path_format(self):
        """Test that macOS Firefox binary path has correct format."""
        expected_path = os.path.join('Contents', 'MacOS', 'firefox')
        self.assertEqual(cm.DEFAULT_TBB_FX_BINARY_PATH, expected_path)

    def test_macos_profile_path_format(self):
        """Test that macOS profile path has correct format."""
        expected = os.path.join(
            'Contents', 'Resources', 'TorBrowser', 'Data', 'Browser', 'profile.default')
        self.assertEqual(cm.DEFAULT_TBB_PROFILE_PATH, expected)

    def test_macos_tor_binary_path_format(self):
        """Test that macOS Tor binary path has correct format."""
        expected = os.path.join(
            'Contents', 'Resources', 'TorBrowser', 'Tor', 'tor')
        self.assertEqual(cm.DEFAULT_TOR_BINARY_PATH, expected)

    def test_paths_exist_in_tbb(self):
        """Test that expected paths exist in TBB."""
        fx_binary = os.path.join(TBB_PATH, cm.DEFAULT_TBB_FX_BINARY_PATH)
        profile = os.path.join(TBB_PATH, cm.DEFAULT_TBB_PROFILE_PATH)
        tor_binary = os.path.join(TBB_PATH, cm.DEFAULT_TOR_BINARY_PATH)

        self.assertTrue(os.path.isfile(fx_binary),
                        f"Firefox binary not found: {fx_binary}")
        self.assertTrue(os.path.isdir(profile),
                        f"Profile not found: {profile}")
        self.assertTrue(os.path.isfile(tor_binary),
                        f"Tor binary not found: {tor_binary}")


if __name__ == "__main__":
    unittest.main()
