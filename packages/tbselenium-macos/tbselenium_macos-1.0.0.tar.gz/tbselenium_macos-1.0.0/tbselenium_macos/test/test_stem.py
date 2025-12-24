"""
Tests for Stem integration on macOS.
"""

import unittest
import pytest
import tempfile

from selenium.webdriver.common.utils import free_port

from tbselenium_macos.test.fixtures import TBDriverFixture, launch_tbb_tor_with_stem_fixture
from tbselenium_macos import common as cm
from tbselenium_macos.test import TBB_PATH

# Try to import Stem
try:
    from stem.control import Controller
    HAS_STEM = True
except ImportError:
    HAS_STEM = False


@pytest.mark.skipif(not HAS_STEM, reason="Stem library not installed")
class TBStemTest(unittest.TestCase):
    """Tests for Stem integration."""

    @classmethod
    def setUpClass(cls):
        """Set up Tor process and controller for all tests."""
        super(TBStemTest, cls).setUpClass()

        cls.control_port = free_port()
        cls.socks_port = free_port()
        temp_data_dir = tempfile.mkdtemp()

        torrc = {
            'ControlPort': str(cls.control_port),
            'SOCKSPort': str(cls.socks_port),
            'DataDirectory': temp_data_dir
        }

        cls.tor_process = launch_tbb_tor_with_stem_fixture(
            tbb_path=TBB_PATH, torrc=torrc)

        cls.controller = Controller.from_port(port=cls.control_port)
        cls.controller.authenticate()

        cls.driver = TBDriverFixture(
            TBB_PATH,
            tor_cfg=cm.USE_STEM,
            socks_port=cls.socks_port,
            control_port=cls.control_port)

    @classmethod
    def tearDownClass(cls):
        """Clean up Tor process and driver."""
        cls.driver.quit()
        cls.controller.close()
        if cls.tor_process:
            cls.tor_process.kill()

    def test_should_add_custom_ports_to_fx_banned_ports(self):
        """Test that custom ports are added to banned ports list."""
        for pref in cm.PORT_BAN_PREFS:
            banned_ports = self.driver.options.preferences[pref]
            self.assertIn(str(self.socks_port), banned_ports)
            self.assertIn(str(self.control_port), banned_ports)

    def test_running_with_stem(self):
        """Test that browser works with Stem-launched Tor."""
        driver = self.driver
        driver.load_url_ensure(cm.CHECK_TPO_URL)
        driver.find_element_by("h1.on")

        # Verify we have circuits
        ccts = self.controller.get_circuits()
        self.assertGreater(len(ccts), 0)


if __name__ == "__main__":
    unittest.main()
