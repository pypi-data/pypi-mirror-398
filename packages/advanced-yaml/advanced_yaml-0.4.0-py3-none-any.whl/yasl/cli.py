"""
YASL CLI main entry point.
"""

import argparse
import sys

from common import advanced_yaml_version
from yasl import yasl_eval


def main():
    parser = argparse.ArgumentParser(
        description="YASL - YAML Advanced Schema Language CLI Tool"
    )
    # Removed --project-name argument; 'param' will be used for project name in 'init'
    parser.add_argument(
        "schema",
        nargs="?",
        help="YASL schema file or directory",
    )
    parser.add_argument(
        "yaml",
        nargs="?",
        help="YAML data file or directory",
    )
    parser.add_argument(
        "model_name",
        nargs="?",
        help="YASL schema type name for the yaml data file (optional)",
    )
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
        print(f"YASL version {advanced_yaml_version()}")
        sys.exit(0)

    if not args.schema or not args.yaml:
        print(
            "❌ requires a YASL file, a YAML schema file, and optionally a model name as parameters."
        )
        parser.print_help()
        sys.exit(1)

    yasl = yasl_eval(
        args.schema,
        args.yaml,
        args.model_name,
        disable_log=False,
        quiet_log=args.quiet,
        verbose_log=args.verbose,
        output=args.output,
    )

    if not yasl:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
