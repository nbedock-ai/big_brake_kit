#!/usr/bin/env python3
"""
scrape_and_ingest.py - CLI wrapper for BigBrakeKit ingestion pipeline

Simple command-line interface to ingest data from seed URLs into SQLite database.
Wraps database.ingest_pipeline.ingest_all() with argparse.

Usage:
    python scrape_and_ingest.py                    # Ingest all groups
    python scrape_and_ingest.py --only all         # Same as above
    python scrape_and_ingest.py --only rotors      # Rotors only
    python scrape_and_ingest.py --only pads        # Pads only
    python scrape_and_ingest.py --only vehicles    # Vehicles only
"""

import argparse
import sys
from database.ingest_pipeline import ingest_all


def parse_args(argv=None):
    """
    Parse command-line arguments.
    
    Args:
        argv: List of argument strings (for testing). If None, uses sys.argv[1:].
    
    Returns:
        argparse.Namespace with parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="BigBrakeKit - Scrape and ingest brake component data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      Ingest all data types (rotors, pads, vehicles)
  %(prog)s --only rotors        Ingest rotors only
  %(prog)s --only pads          Ingest pads only
  %(prog)s --only vehicles      Ingest vehicles only
        """
    )
    
    parser.add_argument(
        "--only",
        type=str,
        choices=["all", "rotors", "pads", "vehicles"],
        default="all",
        help="Specify which data group to ingest (default: all)"
    )
    
    return parser.parse_args(argv)


def main(argv=None):
    """
    Main entry point for CLI.
    
    Args:
        argv: List of argument strings (for testing). If None, uses sys.argv[1:].
    """
    args = parse_args(argv)
    
    # Map CLI argument to ingest_all parameter
    # "all" → None (ingest everything)
    # specific group → pass group name
    if args.only == "all":
        group_param = None
    else:
        group_param = args.only
    
    # Call ingestion pipeline
    print(f"[CLI] Starting ingestion for: {args.only}")
    ingest_all(group=group_param)
    print(f"[CLI] Ingestion complete")


if __name__ == "__main__":
    main()
