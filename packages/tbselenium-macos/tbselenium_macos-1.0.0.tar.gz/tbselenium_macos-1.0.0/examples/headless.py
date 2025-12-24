#!/usr/bin/env python3
"""
Example: Headless Tor Browser on macOS.

This script demonstrates running Tor Browser in headless mode,
which is useful for automation and CI/CD pipelines.

Usage:
    python headless.py /Applications/Tor\ Browser.app

Requirements:
    - Tor Browser for macOS
    - geckodriver (brew install geckodriver)
    - Running Tor (brew services start tor)

Note:
    WebGL might not work correctly in headless mode due to
    Firefox limitations.
"""

from argparse import ArgumentParser

from tbselenium_macos import TorBrowserDriver


def visit_headless(tbb_dir):
    """
    Visit a website in headless mode and take a screenshot.

    Args:
        tbb_dir: Path to Tor Browser.app
    """
    url = "https://check.torproject.org"
    screenshot_path = "tor_check_screenshot.png"

    print(f"Starting Tor Browser in headless mode...")

    with TorBrowserDriver(tbb_dir, headless=True) as driver:
        print(f"Loading {url}...")
        driver.load_url(url, wait_for_page_body=True)

        print(f"Page title: {driver.title}")

        # Take a screenshot
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")

        # Get the status
        try:
            status = driver.find_element_by("h1.on")
            print(f"Status: {status.text}")
        except Exception as e:
            print(f"Could not find status element: {e}")


def main():
    """Parse arguments and run the example."""
    desc = "Run Tor Browser in headless mode and take a screenshot"
    parser = ArgumentParser(description=desc)
    parser.add_argument(
        'tbb_path',
        nargs='?',
        default="/Applications/Tor Browser.app",
        help='Path to Tor Browser.app (default: /Applications/Tor Browser.app)'
    )
    args = parser.parse_args()
    visit_headless(args.tbb_path)


if __name__ == '__main__':
    main()
