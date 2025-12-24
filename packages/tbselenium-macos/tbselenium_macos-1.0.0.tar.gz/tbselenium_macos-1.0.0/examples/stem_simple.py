#!/usr/bin/env python3
"""
Example: Using Stem to launch Tor from the browser bundle.

This script demonstrates launching Tor using the Stem library,
which allows you to use the Tor binary bundled with Tor Browser
instead of requiring a separate system Tor installation.

Usage:
    python stem_simple.py /Applications/Tor\ Browser.app

Requirements:
    - Tor Browser for macOS
    - geckodriver (brew install geckodriver)
    - stem library (pip install stem)
"""

from argparse import ArgumentParser

from tbselenium_macos import (
    TorBrowserDriver,
    launch_tbb_tor_with_stem,
    USE_STEM,
)


def visit_with_stem(tbb_dir):
    """
    Visit a website using Tor launched via Stem.

    Args:
        tbb_dir: Path to Tor Browser.app
    """
    url = "https://check.torproject.org"

    print("Launching Tor using Stem...")

    # Launch Tor from the browser bundle
    tor_process = launch_tbb_tor_with_stem(tbb_path=tbb_dir)

    print("Tor is running, starting browser...")

    try:
        with TorBrowserDriver(tbb_dir, tor_cfg=USE_STEM) as driver:
            print(f"Loading {url}...")
            driver.load_url(url, wait_for_page_body=True)

            print(f"Page title: {driver.title}")

            # Get the status
            try:
                status = driver.find_element_by("h1.on")
                print(f"Status: {status.text}")

                # Get IP address
                ip_element = driver.find_element_by(".content > p")
                print(f"IP info: {ip_element.text}")
            except Exception as e:
                print(f"Could not find element: {e}")
    finally:
        # Clean up Tor process
        print("Stopping Tor process...")
        tor_process.kill()
        print("Done!")


def main():
    """Parse arguments and run the example."""
    desc = "Use Stem to launch Tor from the browser bundle"
    parser = ArgumentParser(description=desc)
    parser.add_argument(
        'tbb_path',
        nargs='?',
        default="/Applications/Tor Browser.app",
        help='Path to Tor Browser.app (default: /Applications/Tor Browser.app)'
    )
    args = parser.parse_args()
    visit_with_stem(args.tbb_path)


if __name__ == '__main__':
    main()
