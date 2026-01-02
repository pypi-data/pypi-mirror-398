"""
YAQL CLI main entry point.
"""

import argparse
import sys

from common import advanced_yaml_version


def main():
    parser = argparse.ArgumentParser(
        description="YAQL - YAML Advanced Query Language CLI Tool"
    )
    # Removed --project-name argument; 'param' will be used for project name in 'init'

    parser.add_argument(
        "--version", action="store_true", help="Show version information and exit"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress output except for errors"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--output",
        choices=["text", "json", "yaml"],
        default="text",
        help="Set output format (text, json, yaml). Default is text.",
    )

    args = parser.parse_args()

    if args.verbose and args.quiet:
        print("❌ Cannot use both --quiet and --verbose.")
        sys.exit(1)

    if args.version:
        print(f"YAQL version {advanced_yaml_version()}")
        sys.exit(0)

    print(
        "❌ This is a placeholder for the YAQL CLI tool. Functionality to be implemented."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
