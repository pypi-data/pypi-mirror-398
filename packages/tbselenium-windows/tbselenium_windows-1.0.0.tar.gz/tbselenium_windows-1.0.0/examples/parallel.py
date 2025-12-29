#!/usr/bin/env python3
"""
Example: Run multiple Tor Browser instances in parallel.

This example demonstrates running multiple Tor Browser instances
concurrently using Python's multiprocessing.

Usage:
    python parallel.py "C:\\Path\\To\\Tor Browser"

Requirements:
    - Tor Browser for Windows
    - geckodriver
    - Running Tor

Note: Each browser instance will use the same Tor circuit by default.
For different exit nodes, you would need multiple Tor processes.
"""

from argparse import ArgumentParser
from multiprocessing import Process, Queue
import time

from tbselenium_windows import TorBrowserDriver


def browse_url(tbb_dir, url, result_queue, worker_id):
    """
    Visit a URL and report the result.

    Args:
        tbb_dir: Path to Tor Browser directory
        url: URL to visit
        result_queue: Queue for reporting results
        worker_id: Identifier for this worker
    """
    try:
        print(f"[Worker {worker_id}] Starting browser...")

        with TorBrowserDriver(tbb_dir) as driver:
            print(f"[Worker {worker_id}] Loading {url}...")
            driver.load_url(url, wait_for_page_body=True)

            title = driver.title
            result_queue.put({
                'worker_id': worker_id,
                'url': url,
                'title': title,
                'success': True
            })

    except Exception as e:
        result_queue.put({
            'worker_id': worker_id,
            'url': url,
            'error': str(e),
            'success': False
        })


def run_parallel(tbb_dir, urls):
    """
    Visit multiple URLs in parallel.

    Args:
        tbb_dir: Path to Tor Browser directory
        urls: List of URLs to visit
    """
    result_queue = Queue()
    processes = []

    print(f"Starting {len(urls)} parallel browser instances...")
    start_time = time.time()

    # Start a process for each URL
    for i, url in enumerate(urls):
        p = Process(target=browse_url, args=(tbb_dir, url, result_queue, i))
        processes.append(p)
        p.start()
        # Small delay between starts to avoid resource contention
        time.sleep(2)

    # Wait for all processes to complete
    for p in processes:
        p.join()

    elapsed_time = time.time() - start_time

    # Collect results
    print("\n" + "=" * 50)
    print("RESULTS:")
    print("=" * 50)

    while not result_queue.empty():
        result = result_queue.get()
        if result['success']:
            print(f"[Worker {result['worker_id']}] SUCCESS")
            print(f"  URL: {result['url']}")
            print(f"  Title: {result['title']}")
        else:
            print(f"[Worker {result['worker_id']}] FAILED")
            print(f"  URL: {result['url']}")
            print(f"  Error: {result['error']}")

    print(f"\nTotal time: {elapsed_time:.2f} seconds")


def main():
    """Parse arguments and run the example."""
    desc = "Run multiple Tor Browser instances in parallel"
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

    # URLs to visit in parallel
    urls = [
        "https://check.torproject.org",
        "https://duckduckgo.com",
        "https://www.wikipedia.org",
    ]

    run_parallel(args.tbb_path, urls)


if __name__ == '__main__':
    main()
