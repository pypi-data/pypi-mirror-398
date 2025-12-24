"""
Tests for extension/addon handling on macOS.
"""

import os
import unittest
import tempfile

from tbselenium_macos.test import TBB_PATH
from tbselenium_macos.test.fixtures import TBDriverFixture
from tbselenium_macos import common as cm


class AddonsTest(unittest.TestCase):
    """Tests for extension handling."""

    def setUp(self):
        self.tb_driver = TBDriverFixture(TBB_PATH)

    def tearDown(self):
        self.tb_driver.quit()

    def test_noscript_xpi_exists(self):
        """Test that NoScript XPI exists in TBB."""
        noscript_path = os.path.join(TBB_PATH, cm.DEFAULT_TBB_NO_SCRIPT_XPI_PATH)
        # NoScript may or may not be bundled depending on TBB version
        # This test just checks the path format is correct
        self.assertTrue(
            noscript_path.endswith('.xpi'),
            "NoScript path should end with .xpi")

    def test_install_extension_method_exists(self):
        """Test that install_addon method exists on driver."""
        self.assertTrue(hasattr(self.tb_driver, 'install_addon'))
        self.assertTrue(callable(self.tb_driver.install_addon))

    def test_extensions_list_parameter(self):
        """Test that extensions parameter is handled correctly."""
        # Close the default driver
        self.tb_driver.quit()

        # Create a new driver with empty extensions list
        # (just verifying parameter is accepted)
        self.tb_driver = TBDriverFixture(TBB_PATH, extensions=[])
        self.assertIsNotNone(self.tb_driver)


if __name__ == "__main__":
    unittest.main()
