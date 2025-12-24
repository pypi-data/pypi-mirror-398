"""
Tests for utility functions on macOS.
"""

import os
import unittest
from os import environ

from tbselenium_macos.utils import (
    is_busy,
    prepend_to_env_var,
    is_macos,
    find_tor_browser_app,
    get_geckodriver_path,
)


class UtilsTest(unittest.TestCase):
    """Tests for utility functions."""

    def test_is_busy_on_unused_port(self):
        """Test is_busy returns False for unused port."""
        # Use a high port that's unlikely to be in use
        self.assertFalse(is_busy(59999))

    def test_prepend_to_env_var_new(self):
        """Test prepending to a new environment variable."""
        test_var = "_TEST_PREPEND_VAR_NEW"
        if test_var in environ:
            del environ[test_var]

        prepend_to_env_var(test_var, "/test/path")
        self.assertEqual(environ[test_var], "/test/path")

        # Cleanup
        del environ[test_var]

    def test_prepend_to_env_var_existing(self):
        """Test prepending to an existing environment variable."""
        test_var = "_TEST_PREPEND_VAR_EXISTING"
        environ[test_var] = "/existing/path"

        prepend_to_env_var(test_var, "/new/path")
        self.assertEqual(environ[test_var], "/new/path:/existing/path")

        # Cleanup
        del environ[test_var]

    def test_prepend_to_env_var_no_duplicate(self):
        """Test that prepending doesn't create duplicates."""
        test_var = "_TEST_PREPEND_VAR_DUP"
        environ[test_var] = "/existing/path"

        prepend_to_env_var(test_var, "/existing/path")
        self.assertEqual(environ[test_var], "/existing/path")

        # Cleanup
        del environ[test_var]

    def test_is_macos(self):
        """Test platform detection."""
        import sys
        result = is_macos()
        self.assertEqual(result, sys.platform == 'darwin')

    def test_find_tor_browser_app(self):
        """Test Tor Browser app detection."""
        # This will return None if TBB is not in a standard location
        # or the actual path if found
        result = find_tor_browser_app()
        if result is not None:
            self.assertTrue(os.path.isdir(result))
            self.assertTrue(result.endswith('.app'))

    def test_get_geckodriver_path(self):
        """Test geckodriver path detection."""
        result = get_geckodriver_path()
        if result is not None:
            self.assertTrue(os.path.isfile(result))


if __name__ == "__main__":
    unittest.main()
