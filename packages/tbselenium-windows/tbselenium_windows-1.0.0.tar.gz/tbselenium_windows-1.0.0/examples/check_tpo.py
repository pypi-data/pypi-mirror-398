#!/usr/bin/env python3
"""
Example: Check Tor Project connection status.

This script visits check.torproject.org to verify Tor connectivity
and displays the connection status in multiple languages.

Usage:
    python check_tpo.py "C:\\Path\\To\\Tor Browser"

Requirements:
    - Tor Browser for Windows
    - geckodriver
    - Running Tor
"""

from argparse import ArgumentParser
from time import sleep

from tbselenium_windows import TorBrowserDriver
from selenium.webdriver.support.ui import Select


def visit(tbb_dir):
    """
    Visit check.torproject.org and display connection status in multiple languages.

    Args:
        tbb_dir: Path to Tor Browser directory
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
        default=None,
        help='Path to Tor Browser directory (e.g., "C:\\Tor Browser")'
    )
    args = parser.parse_args()

    if args.tbb_path is None:
        from tbselenium_windows.utils import find_tor_browser_dir
        args.tbb_path = find_tor_browser_dir()
        if args.tbb_path is None:
            print("Error: Could not find Tor Browser.")
            print("Please provide the path as an argument.")
            return

    visit(args.tbb_path)


if __name__ == '__main__':
    main()
