#!/usr/bin/env python3
"""
Coverage Summary Script for Zoho Projects SDK

This script runs the test suite with coverage and provides a summary of the results.
It can be used to generate coverage reports and check if coverage meets the required threshold.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_coverage() -> bool:
    """Run the coverage command and return the result."""
    print("Running tests with coverage...")

    # Run pytest with coverage using uv
    cmd = [
        "uv",
        "run",
        "pytest",
        "tests/unit",
        "tests/integration",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-branch",
        "--cov-fail-under=100",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Coverage check passed! All modules have 100% coverage.")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("Coverage check failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main() -> None:
    """Main function to run the coverage summary."""
    print("Zoho Projects SDK - Coverage Summary")
    print("=" * 40)

    success = run_coverage()

    if success:
        print("\n✅ All coverage requirements met (100% line and branch coverage)!")
        print("HTML coverage report generated in 'htmlcov/' directory")
        print("XML coverage report generated as 'coverage.xml'")
    else:
        print("\n❌ Coverage requirements not met! Current coverage is below 100%.")
        print("HTML coverage report generated in 'htmlcov/' directory")
        print("XML coverage report generated as 'coverage.xml'")
        print("Note: The configuration correctly enforces 100% coverage as required.")
        sys.exit(1)


if __name__ == "__main__":
    main()
