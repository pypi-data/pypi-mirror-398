"""
Tests for disabling browser features on macOS.
"""

import unittest
import pytest

from tbselenium_macos.test import TBB_PATH
from tbselenium_macos.test.fixtures import TBDriverFixture
from tbselenium_macos.utils import disable_js, enable_js, get_js_status_text
from tbselenium_macos import common as cm


class DisableFeaturesTest(unittest.TestCase):
    """Tests for feature disabling."""

    def setUp(self):
        self.tb_driver = TBDriverFixture(TBB_PATH)

    def tearDown(self):
        self.tb_driver.quit()

    def test_disable_js_function_exists(self):
        """Test that disable_js function exists."""
        self.assertTrue(callable(disable_js))

    def test_enable_js_function_exists(self):
        """Test that enable_js function exists."""
        self.assertTrue(callable(enable_js))

    @pytest.mark.skipif(True, reason="JS tests require specific test page")
    def test_disable_and_enable_js(self):
        """Test disabling and enabling JavaScript."""
        # Load JS test page
        self.tb_driver.load_url_ensure(cm.LOCAL_JS_TEST_URL)

        # Initially JS should work
        initial_status = get_js_status_text(self.tb_driver)
        self.assertIn("enabled", initial_status.lower())

        # Disable JS
        disable_js(self.tb_driver)
        self.tb_driver.refresh()

        # Check JS is disabled
        disabled_status = get_js_status_text(self.tb_driver)
        self.assertIn("disabled", disabled_status.lower())

        # Re-enable JS
        enable_js(self.tb_driver)
        self.tb_driver.refresh()

        # Check JS is enabled again
        enabled_status = get_js_status_text(self.tb_driver)
        self.assertIn("enabled", enabled_status.lower())


class DisableImagesTest(unittest.TestCase):
    """Tests for image loading control."""

    def test_disable_images_via_pref(self):
        """Test disabling images via preference."""
        pref_dict = {"permissions.default.image": 2}
        driver = TBDriverFixture(TBB_PATH, pref_dict=pref_dict)

        try:
            # Verify the preference was set
            prefs = driver.options.preferences
            self.assertEqual(prefs.get("permissions.default.image"), 2)
        finally:
            driver.quit()


if __name__ == "__main__":
    unittest.main()
