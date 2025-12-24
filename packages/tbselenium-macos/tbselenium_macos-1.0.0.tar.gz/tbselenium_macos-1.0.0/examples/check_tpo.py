#!/usr/bin/env python3
"""
Example: Check Tor Project connection status.

This script visits check.torproject.org to verify Tor connectivity
and displays the connection status in multiple languages.

Usage:
    python check_tpo.py /Applications/Tor\ Browser.app

Requirements:
    - Tor Browser for macOS
    - geckodriver (brew install geckodriver)
    - Running Tor (brew services start tor)
"""

from argparse import ArgumentParser
from time import sleep

from tbselenium_macos import TorBrowserDriver
from selenium.webdriver.support.ui import Select


def visit(tbb_dir):
    """
    Visit check.torproject.org and display connection status in multiple languages.

    Args:
        tbb_dir: Path to Tor Browser.app
    """
    url = "https://check.torproject.org"

    with TorBrowserDriver(tbb_dir) as driver:
        driver.load_url(url)

        # Iterate over a bunch of locales from the drop-down menu
        for lang_code in ["en_US", "fr", "zh_CN", "th", "tr"]:
            select = Select(driver.find_element_by_id("cl"))
            select.select_by_value(lang_code)
            sleep(1)

            print(f"\n======== Locale: {lang_code} ========")
            print(driver.find_element_by("h1.on").text)  # status text
            print(driver.find_element_by(".content > p").text)  # IP address


def main():
    """Parse arguments and run the example."""
    desc = "Visit check.torproject.org website and verify Tor connectivity"
    parser = ArgumentParser(description=desc)
    parser.add_argument(
        'tbb_path',
        nargs='?',
        default="/Applications/Tor Browser.app",
        help='Path to Tor Browser.app (default: /Applications/Tor Browser.app)'
    )
    args = parser.parse_args()
    visit(args.tbb_path)


if __name__ == '__main__':
    main()
