#!/usr/bin/env python3
"""
Example: Visit onion services (hidden services).

This script demonstrates visiting .onion addresses
using Tor Browser on macOS.

Usage:
    python onion_service.py /Applications/Tor\ Browser.app

Requirements:
    - Tor Browser for macOS
    - geckodriver (brew install geckodriver)
    - Running Tor (brew services start tor)

Note:
    Onion services may take longer to load due to the
    multiple layers of encryption and routing.
"""

from argparse import ArgumentParser

from tbselenium_macos import TorBrowserDriver


def visit_onion(tbb_dir):
    """
    Visit an onion service.

    Args:
        tbb_dir: Path to Tor Browser.app
    """
    # Tor Project's official v3 onion address
    onion_url = "http://2gzyxa5ihm7nsggfxnu52rck2vv4rvmdlkiu3zzui5du4xyclen53wid.onion/"

    print("Starting Tor Browser...")
    print("Note: Onion services may take longer to load.")

    with TorBrowserDriver(tbb_dir) as driver:
        print(f"\nLoading onion service: {onion_url}")
        print("This may take 30-60 seconds...")

        try:
            # Set a longer timeout for onion services
            driver.set_page_load_timeout(120)
            driver.load_url(onion_url, wait_for_page_body=True)

            print(f"\nPage title: {driver.title}")
            print("Successfully connected to onion service!")

            # Take a screenshot
            screenshot_file = "onion_screenshot.png"
            driver.save_screenshot(screenshot_file)
            print(f"Screenshot saved: {screenshot_file}")

        except Exception as e:
            print(f"\nError loading onion service: {e}")
            print("\nTroubleshooting tips:")
            print("1. Make sure Tor is properly connected")
            print("2. The onion service might be temporarily unavailable")
            print("3. Try increasing the timeout")


def main():
    """Parse arguments and run the example."""
    desc = "Visit an onion service using Tor Browser"
    parser = ArgumentParser(description=desc)
    parser.add_argument(
        'tbb_path',
        nargs='?',
        default="/Applications/Tor Browser.app",
        help='Path to Tor Browser.app (default: /Applications/Tor Browser.app)'
    )
    args = parser.parse_args()
    visit_onion(args.tbb_path)


if __name__ == '__main__':
    main()
