#!/usr/bin/env python3
"""
Wisconsin Overlay Map - Main Entry Point
PRD v1.1 compliant
"""

import argparse
from agents.orchestrator import run_county

def main():
    parser = argparse.ArgumentParser(description="Wisconsin Overlay Map Pipeline")
    parser.add_argument("--county", default="Brown", help="County name (e.g. Brown)")
    parser.add_argument("--phase", type=int, default=1, help="Phase number")
    args = parser.parse_args()

    print(f"Starting Wisconsin Overlay Map - Phase {args.phase}")
    run_county(args.county)

if __name__ == "__main__":
    main()