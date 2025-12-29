#!/usr/bin/env python3
"""
Example: Use Tor Browser in headless mode.

This example demonstrates running Tor Browser without a visible window,
which is useful for automated testing and scripts.

Usage:
    python headless.py "C:\\Path\\To\\Tor Browser"

Requirements:
    - Tor Browser for Windows
    - geckodriver
    - Running Tor
"""

from argparse import ArgumentParser

from tbselenium_windows import TorBrowserDriver


def run_headless(tbb_dir):
    """
    Run Tor Browser in headless mode and visit a page.

    Args:
        tbb_dir: Path to Tor Browser directory
    """
    url = "https://check.torproject.org"

    print("Starting Tor Browser in headless mode...")

    with TorBrowserDriver(tbb_dir, headless=True) as driver:
        print(f"Loading {url}...")
        driver.load_url(url, wait_for_page_body=True)

        print(f"\nPage title: {driver.title}")
        print(f"Current URL: {driver.current_url}")

        # Get the connection status
        try:
            status = driver.find_element_by("h1.on").text
            print(f"Connection status: {status}")
        except Exception:
            print("Could not determine connection status")

        print("\nHeadless mode test complete!")


def main():
    """Parse arguments and run the example."""
    desc = "Run Tor Browser in headless mode"
    parser = ArgumentParser(description=desc)
    parser.add_argument(
        'tbb_path',
        nargs='?',
        default=None,
        help='Path to Tor Browser directory'
    )
    args = parser.parse_args()

    if args.tbb_path is None:
        from tbselenium_windows.utils import find_tor_browser_dir
        args.tbb_path = find_tor_browser_dir()
        if args.tbb_path is None:
            print("Error: Could not find Tor Browser.")
            print("Please provide the path as an argument.")
            return

    run_headless(args.tbb_path)


if __name__ == '__main__':
    main()
