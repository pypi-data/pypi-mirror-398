#!/usr/bin/env python3
"""
Simple test script to verify module validation works correctly.
"""

import sys
import os

# Add the src directory to the path so we can import the SDK
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from zoho_projects_sdk.api.timelogs import TimelogFilters


def test_valid_modules():
    """Test that valid module types work correctly."""
    print("Testing valid module types...")

    # Test valid modules
    valid_modules = ["task", "milestone"]
    for module in valid_modules:
        try:
            filters = TimelogFilters(module=module)
            print(f"✓ Module '{module}' accepted")
        except ValueError as e:
            print(f"✗ Module '{module}' rejected: {e}")
            return False

    return True


def test_invalid_modules():
    """Test that invalid module types are rejected."""
    print("\nTesting invalid module types...")

    # Test invalid modules
    invalid_modules = ["bug", "phase", "general", "invalid"]
    for module in invalid_modules:
        try:
            filters = TimelogFilters(module=module)
            print(f"✗ Module '{module}' was incorrectly accepted")
            return False
        except ValueError as e:
            print(f"✓ Module '{module}' correctly rejected: {e}")

    return True


def test_none_module():
    """Test that None module type works (should use default)."""
    print("\nTesting None module type...")

    try:
        filters = TimelogFilters(module=None)
        print(f"✓ None module type accepted (default: {filters.module})")
        return True
    except ValueError as e:
        print(f"✗ None module type rejected: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing TimelogFilters module validation...\n")

    tests = [
        test_valid_modules,
        test_invalid_modules,
        test_none_module,
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print(f"\n{'='*50}")
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
