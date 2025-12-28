#!/usr/bin/env python3
"""
Git Exposure Scanner - CLI Interface
"""

import argparse
import sys
from ctm_git_exposure.core import GitExposureScanner, BannerDisplay, Theme


def main():
    """Main CLI entry point"""
    BannerDisplay.show_header()
    
    parser = argparse.ArgumentParser(
        description="Git Exposure Scanner - Find exposed .git directories and extract sensitive information"
    )
    parser.add_argument(
        "-t", "--target",
        required=True,
        help="Target URL (e.g., https://example.com)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="Download entire .git directory to reconstruct repository"
    )
    parser.add_argument(
        "-o", "--output",
        default="./dumped-git",
        help="Output directory for dumped .git files (default: ./dumped-git)"
    )
    
    args = parser.parse_args()
    
    # Show configuration
    BannerDisplay.show_config(args.target)
    
    # Create scanner and execute
    scanner = GitExposureScanner(args.target, timeout=args.timeout)
    success, status, findings = scanner.scan()
    
    # If dump requested and .git is exposed
    if args.dump and findings.get('exposed'):
        print(f"\n{Theme.OKCYAN}[*] Starting .git directory dump...{Theme.ENDC}")
        dump_success = scanner.dump_repository(args.output)
        if dump_success:
            print(f"{Theme.OKGREEN}[+] Repository dumped to: {args.output}{Theme.ENDC}")
            print(f"{Theme.WARNING}[*] To explore: cd {args.output} && git log{Theme.ENDC}")
    
    # Show results
    if success:
        BannerDisplay.show_success(findings)
        sys.exit(0)
    else:
        BannerDisplay.show_failure(status, findings)
        sys.exit(1)


if __name__ == "__main__":
    main()
