#!/usr/bin/env python3
"""
Test runner script for the Telegram File Downloader Bot.
"""

import sys
import subprocess
import os


def run_tests(test_type="all", coverage=True):
    """Run tests with specified options."""

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])

    # Add test type filters
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])

    # Add verbose output
    cmd.append("-v")

    print(f"Running tests: {' '.join(cmd)}")
    print("=" * 60)

    # Run the tests
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    return result.returncode


def main():
    """Main function to run tests."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run tests for Telegram File Downloader Bot"
    )
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "fast"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--no-coverage", action="store_true", help="Disable coverage reporting"
    )

    args = parser.parse_args()

    # Run tests
    exit_code = run_tests(args.type, not args.no_coverage)

    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
