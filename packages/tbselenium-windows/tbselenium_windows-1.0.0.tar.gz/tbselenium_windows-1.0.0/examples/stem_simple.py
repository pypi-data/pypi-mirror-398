#!/usr/bin/env python3
"""
Example: Use Stem to launch Tor from the bundle.

This example demonstrates launching Tor from Tor Browser's bundle
using the Stem library, which allows running without system Tor.

Usage:
    python stem_simple.py "C:\\Path\\To\\Tor Browser"

Requirements:
    - Tor Browser for Windows
    - geckodriver
    - stem library (pip install stem)
"""

from argparse import ArgumentParser

from tbselenium_windows import TorBrowserDriver, launch_tbb_tor_with_stem, USE_STEM


def run_with_stem(tbb_dir):
    """
    Launch Tor from the bundle and browse.

    Args:
        tbb_dir: Path to Tor Browser directory
    """
    url = "https://check.torproject.org"

    print("Launching Tor from the bundle...")

    # Launch Tor using Stem
    tor_process = launch_tbb_tor_with_stem(tbb_path=tbb_dir)

    try:
        print("Tor started successfully!")
        print(f"Starting Tor Browser and loading {url}...")

        with TorBrowserDriver(tbb_dir, tor_cfg=USE_STEM) as driver:
            driver.load_url(url, wait_for_page_body=True)

            print(f"\nPage title: {driver.title}")

            # Get the connection status
            try:
                status = driver.find_element_by("h1.on").text
                print(f"Connection status: {status}")
            except Exception:
                print("Could not determine connection status")

    finally:
        # Always clean up the Tor process
        print("\nStopping Tor process...")
        tor_process.kill()
        print("Done!")


def main():
    """Parse arguments and run the example."""
    desc = "Launch Tor from Tor Browser bundle using Stem"
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

    run_with_stem(args.tbb_path)


if __name__ == '__main__':
    main()
