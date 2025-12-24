"""
Tests for security level setting on macOS.
"""

import unittest
import pytest

from tbselenium_macos.test import TBB_PATH
from tbselenium_macos.test.fixtures import TBDriverFixture
from tbselenium_macos.utils import (
    set_security_level,
    TB_SECURITY_LEVEL_STANDARD,
    TB_SECURITY_LEVEL_SAFER,
    TB_SECURITY_LEVEL_SAFEST,
    TB_SECURITY_LEVELS,
)


class SecurityLevelTest(unittest.TestCase):
    """Tests for security level settings."""

    def setUp(self):
        self.tb_driver = TBDriverFixture(TBB_PATH)

    def tearDown(self):
        self.tb_driver.quit()

    def test_security_levels_defined(self):
        """Test that all security levels are defined."""
        self.assertIn(TB_SECURITY_LEVEL_STANDARD, TB_SECURITY_LEVELS)
        self.assertIn(TB_SECURITY_LEVEL_SAFER, TB_SECURITY_LEVELS)
        self.assertIn(TB_SECURITY_LEVEL_SAFEST, TB_SECURITY_LEVELS)
        self.assertEqual(len(TB_SECURITY_LEVELS), 3)

    def test_invalid_security_level_raises_error(self):
        """Test that invalid security level raises ValueError."""
        with self.assertRaises(ValueError):
            set_security_level(self.tb_driver, "invalid_level")

    @pytest.mark.skipif(True, reason="Security level UI tests are fragile")
    def test_set_security_level_standard(self):
        """Test setting security level to standard."""
        set_security_level(self.tb_driver, TB_SECURITY_LEVEL_STANDARD)
        # Verification would require checking the actual preference

    @pytest.mark.skipif(True, reason="Security level UI tests are fragile")
    def test_set_security_level_safer(self):
        """Test setting security level to safer."""
        set_security_level(self.tb_driver, TB_SECURITY_LEVEL_SAFER)
        # Verification would require checking the actual preference

    @pytest.mark.skipif(True, reason="Security level UI tests are fragile")
    def test_set_security_level_safest(self):
        """Test setting security level to safest."""
        set_security_level(self.tb_driver, TB_SECURITY_LEVEL_SAFEST)
        # Verification would require checking the actual preference


if __name__ == "__main__":
    unittest.main()
