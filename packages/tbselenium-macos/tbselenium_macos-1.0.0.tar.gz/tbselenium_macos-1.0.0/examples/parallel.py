#!/usr/bin/env python3
"""
Example: Run multiple Tor Browser instances in parallel.

This script demonstrates running multiple Tor Browser instances
concurrently, each on a different geckodriver port.

Usage:
    python parallel.py /Applications/Tor\ Browser.app

Requirements:
    - Tor Browser for macOS
    - geckodriver (brew install geckodriver)
    - Running Tor (brew services start tor)

Note:
    Running multiple browser instances requires significant
    system resources. Each instance needs its own geckodriver port.
"""

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from selenium.webdriver.common.utils import free_port

from tbselenium_macos import TorBrowserDriver


# Lock for thread-safe printing
print_lock = Lock()


def safe_print(*args, **kwargs):
    """Thread-safe print function."""
    with print_lock:
        print(*args, **kwargs)


def visit_url(tbb_dir, url, instance_id):
    """
    Visit a URL in a Tor Browser instance.

    Args:
        tbb_dir: Path to Tor Browser.app
        url: URL to visit
        instance_id: Identifier for this instance

    Returns:
        dict: Result containing instance_id, url, title, and success status
    """
    # Get a free port for geckodriver
    geckodriver_port = free_port()

    safe_print(f"[Instance {instance_id}] Starting on port {geckodriver_port}...")

    try:
        with TorBrowserDriver(
            tbb_dir,
            geckodriver_port=geckodriver_port
        ) as driver:
            safe_print(f"[Instance {instance_id}] Loading {url}...")
            driver.load_url(url, wait_for_page_body=True)

            title = driver.title
            safe_print(f"[Instance {instance_id}] Title: {title}")

            return {
                "instance_id": instance_id,
                "url": url,
                "title": title,
                "success": True,
            }

    except Exception as e:
        safe_print(f"[Instance {instance_id}] Error: {e}")
        return {
            "instance_id": instance_id,
            "url": url,
            "error": str(e),
            "success": False,
        }


def run_parallel(tbb_dir, urls=None, max_workers=3):
    """
    Visit multiple URLs in parallel browser instances.

    Args:
        tbb_dir: Path to Tor Browser.app
        urls: List of URLs to visit
        max_workers: Maximum number of parallel browser instances
    """
    if urls is None:
        urls = [
            "https://check.torproject.org",
            "https://www.torproject.org",
            "https://www.eff.org",
        ]

    print(f"Starting {len(urls)} parallel browser instances...")
    print(f"Max workers: {max_workers}\n")

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(visit_url, tbb_dir, url, i + 1): url
            for i, url in enumerate(urls)
        }

        # Collect results as they complete
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    success_count = sum(1 for r in results if r["success"])
    print(f"\nSuccessful: {success_count}/{len(results)}")

    for result in sorted(results, key=lambda x: x["instance_id"]):
        status = "SUCCESS" if result["success"] else "FAILED"
        print(f"\n[Instance {result['instance_id']}] {status}")
        print(f"  URL: {result['url']}")
        if result["success"]:
            print(f"  Title: {result['title']}")
        else:
            print(f"  Error: {result.get('error', 'Unknown')}")


def main():
    """Parse arguments and run the example."""
    desc = "Run multiple Tor Browser instances in parallel"
    parser = ArgumentParser(description=desc)
    parser.add_argument(
        'tbb_path',
        nargs='?',
        default="/Applications/Tor Browser.app",
        help='Path to Tor Browser.app (default: /Applications/Tor Browser.app)'
    )
    parser.add_argument(
        '--workers',
        '-w',
        type=int,
        default=3,
        help='Maximum number of parallel browser instances (default: 3)'
    )
    parser.add_argument(
        '--url',
        '-u',
        action='append',
        dest='urls',
        help='URL to visit (can be specified multiple times)'
    )
    args = parser.parse_args()
    run_parallel(args.tbb_path, args.urls, args.workers)


if __name__ == '__main__':
    main()
