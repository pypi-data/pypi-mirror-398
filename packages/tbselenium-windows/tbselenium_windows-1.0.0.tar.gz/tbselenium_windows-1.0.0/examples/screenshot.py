#!/usr/bin/env python3
"""
Example: Take a screenshot of a webpage through Tor.

Usage:
    python screenshot.py "C:\\Path\\To\\Tor Browser" https://example.com

Requirements:
    - Tor Browser for Windows
    - geckodriver
    - Running Tor
"""

from argparse import ArgumentParser
import os

from tbselenium_windows import TorBrowserDriver


def take_screenshot(tbb_dir, url, output_file="screenshot.png"):
    """
    Take a screenshot of the given URL.

    Args:
        tbb_dir: Path to Tor Browser directory
        url: URL to screenshot
        output_file: Output filename
    """
    with TorBrowserDriver(tbb_dir) as driver:
        driver.load_url(url, wait_for_page_body=True)
        driver.save_screenshot(output_file)
        print(f"Screenshot saved to: {os.path.abspath(output_file)}")


def main():
    """Parse arguments and run the example."""
    desc = "Take a screenshot of a webpage through Tor"
    parser = ArgumentParser(description=desc)
    parser.add_argument(
        'tbb_path',
        help='Path to Tor Browser directory'
    )
    parser.add_argument(
        'url',
        nargs='?',
        default="https://check.torproject.org",
        help='URL to screenshot (default: check.torproject.org)'
    )
    parser.add_argument(
        '-o', '--output',
        default='screenshot.png',
        help='Output filename (default: screenshot.png)'
    )
    args = parser.parse_args()

    take_screenshot(args.tbb_path, args.url, args.output)


if __name__ == '__main__':
    main()
