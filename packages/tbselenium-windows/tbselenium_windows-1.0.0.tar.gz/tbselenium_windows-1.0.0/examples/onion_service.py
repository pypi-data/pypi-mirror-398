#!/usr/bin/env python3
"""
Example: Visit a .onion service through Tor.

This example demonstrates visiting an onion (hidden) service.

Usage:
    python onion_service.py "C:\\Path\\To\\Tor Browser"

Requirements:
    - Tor Browser for Windows
    - geckodriver
    - Running Tor

Note: Onion services may take longer to load than clearnet sites.
"""

from argparse import ArgumentParser

from tbselenium_windows import TorBrowserDriver


# DuckDuckGo's onion service
DUCKDUCKGO_ONION = "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion"


def visit_onion(tbb_dir, onion_url=DUCKDUCKGO_ONION):
    """
    Visit an onion service.

    Args:
        tbb_dir: Path to Tor Browser directory
        onion_url: The .onion URL to visit
    """
    print(f"Loading onion service: {onion_url}")
    print("Note: Onion services may take longer to load...")

    with TorBrowserDriver(tbb_dir) as driver:
        try:
            driver.load_url(onion_url, wait_for_page_body=True)
            print(f"\nPage title: {driver.title}")
            print(f"Current URL: {driver.current_url}")
            print("\nOnion service loaded successfully!")
        except Exception as e:
            print(f"\nError loading onion service: {e}")
            print("This may be due to network issues or the service being offline.")


def main():
    """Parse arguments and run the example."""
    desc = "Visit a .onion service through Tor"
    parser = ArgumentParser(description=desc)
    parser.add_argument(
        'tbb_path',
        nargs='?',
        default=None,
        help='Path to Tor Browser directory'
    )
    parser.add_argument(
        '-u', '--url',
        default=DUCKDUCKGO_ONION,
        help=f'Onion URL to visit (default: DuckDuckGo)'
    )
    args = parser.parse_args()

    if args.tbb_path is None:
        from tbselenium_windows.utils import find_tor_browser_dir
        args.tbb_path = find_tor_browser_dir()
        if args.tbb_path is None:
            print("Error: Could not find Tor Browser.")
            print("Please provide the path as an argument.")
            return

    visit_onion(args.tbb_path, args.url)


if __name__ == '__main__':
    main()
