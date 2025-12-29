#!/usr/bin/env python3
"""
Test runner for tbselenium-windows.

Usage:
    python run_tests.py "C:\\Path\\To\\Tor Browser"

Or with environment variable (Command Prompt):
    set TBB_PATH=C:\\Path\\To\\Tor Browser
    python run_tests.py
"""

import os
import sys
from argparse import ArgumentParser


def main():
    """Run the test suite."""
    parser = ArgumentParser(description="Run tbselenium-windows tests")
    parser.add_argument(
        'tbb_path',
        nargs='?',
        help='Path to Tor Browser directory'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--cov',
        action='store_true',
        help='Run with coverage'
    )
    args = parser.parse_args()

    # Set TBB_PATH if provided
    if args.tbb_path:
        os.environ['TBB_PATH'] = args.tbb_path
    elif 'TBB_PATH' not in os.environ:
        print("Error: TBB_PATH not set.")
        print("Either provide path as argument or set TBB_PATH environment variable.")
        print("\nUsage:")
        print("  python run_tests.py \"C:\\\\Path\\\\To\\\\Tor Browser\"")
        print("  OR")
        print("  set TBB_PATH=C:\\Path\\To\\Tor Browser")
        print("  python run_tests.py")
        sys.exit(1)

    # Build pytest command
    pytest_args = ['pytest', 'tbselenium_windows/test/']

    if args.verbose:
        pytest_args.append('-v')

    if args.cov:
        pytest_args.extend(['--cov=tbselenium_windows', '--cov-report=term-missing'])

    # Always add some useful flags
    pytest_args.extend(['--tb=short', '-x'])  # stop on first failure

    print(f"TBB_PATH: {os.environ['TBB_PATH']}")
    print(f"Running: {' '.join(pytest_args)}")
    print()

    # Run pytest
    import pytest
    sys.exit(pytest.main(pytest_args[1:]))


if __name__ == '__main__':
    main()
