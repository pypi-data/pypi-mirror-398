#!/usr/bin/env python3
"""
Example: Take screenshots with Tor Browser.

This script demonstrates taking screenshots of websites
using Tor Browser on macOS.

Usage:
    python screenshot.py /Applications/Tor\ Browser.app

Requirements:
    - Tor Browser for macOS
    - geckodriver (brew install geckodriver)
    - Running Tor (brew services start tor)
"""

from argparse import ArgumentParser
from datetime import datetime

from tbselenium_macos import TorBrowserDriver


def take_screenshots(tbb_dir, urls=None):
    """
    Take screenshots of multiple URLs.

    Args:
        tbb_dir: Path to Tor Browser.app
        urls: List of URLs to screenshot (default: some examples)
    """
    if urls is None:
        urls = [
            "https://check.torproject.org",
            "https://www.torproject.org",
            "about:tor",
        ]

    print(f"Starting Tor Browser...")

    with TorBrowserDriver(tbb_dir) as driver:
        for i, url in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}] Loading {url}...")

            try:
                driver.load_url(url, wait_for_page_body=True)
                print(f"  Title: {driver.title}")

                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_url = url.replace("://", "_").replace("/", "_")[:50]
                filename = f"screenshot_{i+1}_{safe_url}_{timestamp}.png"

                # Take screenshot
                driver.save_screenshot(filename)
                print(f"  Screenshot saved: {filename}")

            except Exception as e:
                print(f"  Error: {e}")

    print("\nDone!")


def main():
    """Parse arguments and run the example."""
    desc = "Take screenshots of websites using Tor Browser"
    parser = ArgumentParser(description=desc)
    parser.add_argument(
        'tbb_path',
        nargs='?',
        default="/Applications/Tor Browser.app",
        help='Path to Tor Browser.app (default: /Applications/Tor Browser.app)'
    )
    parser.add_argument(
        '--url',
        '-u',
        action='append',
        dest='urls',
        help='URL to screenshot (can be specified multiple times)'
    )
    args = parser.parse_args()
    take_screenshots(args.tbb_path, args.urls)


if __name__ == '__main__':
    main()
