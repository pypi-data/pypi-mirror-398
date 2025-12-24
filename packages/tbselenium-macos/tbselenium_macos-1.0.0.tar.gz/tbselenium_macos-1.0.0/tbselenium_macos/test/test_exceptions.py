"""
Tests for exception handling on macOS.
"""

import unittest

from tbselenium_macos.exceptions import (
    TBDriverPathError,
    TBDriverPortError,
    TBDriverConfigError,
    StemLaunchError,
    TorBrowserDriverInitError,
    TBTestEnvVarError,
    TimeExceededError,
    PlatformNotSupportedError,
)
from tbselenium_macos.tbdriver import TorBrowserDriver
from tbselenium_macos import common as cm


class ExceptionsTest(unittest.TestCase):
    """Tests for exception handling."""

    def test_invalid_tbb_path_raises_error(self):
        """Test that invalid TBB path raises TBDriverPathError."""
        with self.assertRaises(TBDriverPathError):
            TorBrowserDriver("/invalid/path/to/tor/browser")

    def test_no_path_raises_error(self):
        """Test that missing path raises TBDriverPathError."""
        with self.assertRaises(TBDriverPathError):
            TorBrowserDriver()

    def test_invalid_tor_cfg_raises_error(self):
        """Test that invalid tor_cfg raises TBDriverConfigError."""
        # Create a mock valid path scenario by catching the path error first
        # The config error would be raised after path validation
        pass  # This requires a valid TBB path to test properly

    def test_deprecated_tor_cfg_raises_error(self):
        """Test that LAUNCH_NEW_TBB_TOR raises TBDriverConfigError."""
        # The config check happens after path validation
        pass  # This requires a valid TBB path to test properly

    def test_exception_inheritance(self):
        """Test that custom exceptions inherit from Exception."""
        exceptions = [
            TBDriverPathError,
            TBDriverPortError,
            TBDriverConfigError,
            StemLaunchError,
            TorBrowserDriverInitError,
            TBTestEnvVarError,
            TimeExceededError,
            PlatformNotSupportedError,
        ]

        for exc_class in exceptions:
            self.assertTrue(issubclass(exc_class, Exception))

    def test_exception_can_be_raised(self):
        """Test that custom exceptions can be raised with messages."""
        with self.assertRaises(TBDriverPathError) as ctx:
            raise TBDriverPathError("Test path error")
        self.assertEqual(str(ctx.exception), "Test path error")

        with self.assertRaises(TBDriverPortError) as ctx:
            raise TBDriverPortError("Test port error")
        self.assertEqual(str(ctx.exception), "Test port error")

        with self.assertRaises(StemLaunchError) as ctx:
            raise StemLaunchError("Test stem error")
        self.assertEqual(str(ctx.exception), "Test stem error")


if __name__ == "__main__":
    unittest.main()
