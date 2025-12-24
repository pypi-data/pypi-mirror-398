#!/usr/bin/env python3

import json
import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import requests
import threading
from . import config
from . import utils
from . import query_generator
from . import username_checker
from . import report_generator

def daemon_thread_factory(*args, **kwargs):
    t = threading.Thread(*args, **kwargs)
    t.daemon = True  # thread won’t block program exit
    return t


class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLATFORM_FILE = os.path.join(BASE_DIR, 'platforms.json')
FINGERPRINT_FILE = os.path.join(BASE_DIR, "fingerprints.json")


def generate_fingerprints(platforms):
    """Fetches a fake user page for every platform to see what a 404 looks like."""

    # Load existing fingerprints
    existing_fps = load_fingerprints()
    username_checker.fingerprints.update(existing_fps)

    print("[*] Generating fingerprints to eliminate false positives...")

    to_generate = {name: data for name, data in platforms.items() if name not in username_checker.fingerprints}

    if not to_generate:
        print("[*] All fingerprints already exist. Skipping generation.\n")
        return

    with ThreadPoolExecutor(max_workers=20) as pre_executor:
        futures = []
        for name, data in to_generate.items():
            futures.append(pre_executor.submit(fetch_and_store_fingerprint, name, data))

        # Wait for all
        for future in as_completed(futures):
            pass

    # Save updated fingerprints
    save_fingerprints(username_checker.fingerprints)
    print("[*] Fingerprinting complete. Starting search...\n")


def fetch_and_store_fingerprint(name, data):
    from . import username_checker as uc
    from . import config

    try:
        fake_url = data['url'].format("a1b2c3d4_nonexistent_99")
        headers = {"User-Agent": config.USER_AGENT}
        r = requests.get(fake_url, headers=headers, timeout=5, allow_redirects=True)

        html_clean = uc.clean_html(r.text)[:500]
        html_hash = uc.hash_html(html_clean)
        uc.fingerprints[name] = html_hash
    except:
        uc.fingerprints[name] = None

def load_fingerprints():
    if os.path.exists(FINGERPRINT_FILE):
        with open(FINGERPRINT_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_fingerprints(fingerprints):
    with open(FINGERPRINT_FILE, "w", encoding="utf-8") as f:
        json.dump(fingerprints, f, indent=2)
def main():
    parser = argparse.ArgumentParser(
        description='Canopy - Username Enumeration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Examples:
      canopy -u johndoe
      canopy -u johndoe -t 50 --timeout 15
      canopy -u johndoe -o report.json --format json
      canopy -u johndoe --categories social,gaming
      canopy --list-categories
            """
    )

    # Target group
    target_group = parser.add_argument_group('Target Options')
    target_group.add_argument('-u', '--username', help='Username to search for', type=str)
    target_group.add_argument('-U', '--usernames', help='File containing list of usernames (one per line)', type=str)

    # Performance group
    performance_group = parser.add_argument_group('Performance Options')
    performance_group.add_argument('-t', '--threads', help='Number of concurrent threads (default: 10)', type=int,
                                   default=config.DEFAULT_THREADS)
    performance_group.add_argument('--timeout', help='Request timeout in seconds (default: 10)', type=int,
                                   default=config.DEFAULT_TIMEOUT)
    performance_group.add_argument('--delay', help='Delay between requests in seconds (default: 0)', type=float,
                                   default=0)
    performance_group.add_argument('--rate-limit', help='Max requests per second (default: unlimited)', type=int,
                                   default=None)

    # Filter group
    filter_group = parser.add_argument_group('Filtering Options')
    filter_group.add_argument('-c', '--categories', help='Comma-separated categories to check (e.g., social,gaming)',
                              type=str)
    filter_group.add_argument('-p', '--platforms', help='Comma-separated specific platforms to check', type=str)
    filter_group.add_argument('--exclude', help='Comma-separated platforms to exclude', type=str)
    filter_group.add_argument('--only-found', help='Only show found accounts', action='store_true')
    filter_group.add_argument('--list-categories', help='Show all available platform categories and exit',
                              action='store_true')

    # Output group
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('-o', '--output', help='Output file path', type=str)
    output_group.add_argument('-f', '--format', help='Output format: json, csv, html, txt (default: json)', type=str,
                              choices=['json', 'csv', 'html', 'txt'], default='json')
    output_group.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    output_group.add_argument('-q', '--quiet', help='Minimal output (only results)', action='store_true')
    output_group.add_argument('--print-found', help='Print found accounts in real-time', action='store_true')

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    platform_db = utils.load_platform(PLATFORM_FILE, args.categories, args.exclude, args.platforms)
    generate_fingerprints(platform_db)
    from . import data_collector
    collector = data_collector.DataCollector()

    usernames = [args.username] if args.username else utils.load_usernames(args.usernames)
    platform_db = utils.load_platform('platforms.json', args.categories, args.exclude, args.platforms)
    jobs = query_generator.generate_queries(usernames, platform_db)

    if args.list_categories:
        platforms = utils.load_platform('platforms.json')
        categories = sorted(list(set(info.get('category', 'misc') for info in platforms.values())))
        print("\nAvailable Categories:")
        for cat in categories:
            print(f" - {cat}")
        sys.exit(0)

    if not args.username and not args.usernames:
        print(f"{Color.RED}[!] Error: Provide a username (-u) or file (-U){Color.END}")
        sys.exit(1)

    platform_db = utils.load_platform(PLATFORM_FILE, args.categories, args.exclude, args.platforms)

    if not args.quiet:
        print(
            f"{Color.CYAN}[*] Canopy starting search for {len(usernames)} users across {len(platform_db)} platforms...{Color.END}")
        from concurrent.futures import as_completed, ThreadPoolExecutor

        # Create executor with daemon threads
        executor = ThreadPoolExecutor(max_workers=args.threads)
        executor._thread_factory = daemon_thread_factory  # assign daemon threads

        futures = {executor.submit(username_checker.check_username, job, args.timeout): job for job in jobs}

        try:
            for future in as_completed(futures):
                result = future.result()
                collector.add_result(result)

                if args.delay > 0:
                    time.sleep(args.delay)

                if result['status'] == "FOUND":
                    print(f"{Color.GREEN}[+] FOUND: {result['platform']} | {result['url']}{Color.END}")
                elif result['status'] == "ERROR":
                    if args.verbose:
                        print(f"{Color.YELLOW}[!] ERROR: {result['platform']}{Color.END}")
                else:  # MISSING
                    if args.verbose and not args.only_found:
                        print(f"{Color.RED}[-] NOT FOUND: {result['platform']}{Color.END}")

        except KeyboardInterrupt:
            print(f"\n{Color.YELLOW}[!] Search interrupted. Exiting immediately...{Color.END}")
            executor.shutdown(wait=False, cancel_futures=True)
            sys.exit(0)

    stats = collector.get_stats()
    if not args.quiet:
        print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 40}{Color.END}")
        print(f"{Color.BOLD}SCAN SUMMARY{Color.END}")
        print(f"Total Checked: {stats['total_checked']}")
        print(f"Total Found:   {Color.GREEN}{stats['total_found']}{Color.END}")
        print(f"Success Rate:  {Color.CYAN}{stats['success_rate']}{Color.END}")
        print(f"Duration:      {stats['scan_duration']}")
        print(f"{Color.BOLD}{Color.BLUE}{'=' * 40}{Color.END}")

    if args.output:
        report_generator.export_results(collector.get_results(), args.output, args.format)


if __name__ == "__main__":
    main()
