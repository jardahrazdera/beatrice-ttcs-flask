#!/usr/bin/env python3
"""
Test runner for Hot Water Tank Temperature Control System.

This script runs all test suites and provides a comprehensive test report.
"""

import unittest
import sys
import os
from io import StringIO


def run_tests(verbosity=2):
    """
    Run all test suites and return results.

    Args:
        verbosity: Test output verbosity level (0-2)

    Returns:
        TestResult object
    """
    # Discover and load all tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run tests with specified verbosity
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)

    return result


def print_summary(result):
    """
    Print a comprehensive test summary.

    Args:
        result: TestResult object from unittest
    """
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    successful = total_tests - failures - errors - skipped

    print(f"\nTotal Tests Run:  {total_tests}")
    print(f"Successful:       {successful} ({successful/total_tests*100:.1f}%)")
    print(f"Failures:         {failures}")
    print(f"Errors:           {errors}")
    print(f"Skipped:          {skipped}")

    # Print failure details
    if failures > 0:
        print("\n" + "-"*70)
        print("FAILURES:")
        print("-"*70)
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)

    # Print error details
    if errors > 0:
        print("\n" + "-"*70)
        print("ERRORS:")
        print("-"*70)
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)

    print("\n" + "="*70)

    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")

    print("="*70 + "\n")


def run_specific_test(test_module, verbosity=2):
    """
    Run a specific test module.

    Args:
        test_module: Name of test module (e.g., 'test_control')
        verbosity: Test output verbosity level (0-2)
    """
    loader = unittest.TestLoader()
    # Prepend 'tests.' if not already included
    if not test_module.startswith('tests.'):
        test_module = f'tests.{test_module}'
    suite = loader.loadTestsFromName(test_module)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    return result


def main():
    """Main entry point for test runner."""
    import argparse

    parser = argparse.ArgumentParser(description='Run tests for Water Tank Control System')
    parser.add_argument('-v', '--verbosity', type=int, choices=[0, 1, 2], default=2,
                       help='Test output verbosity (0=quiet, 1=normal, 2=verbose)')
    parser.add_argument('-m', '--module', type=str,
                       help='Run specific test module (e.g., test_control)')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Minimal output (equivalent to -v 0)')
    parser.add_argument('--no-summary', action='store_true',
                       help='Skip summary output')

    args = parser.parse_args()

    # Set verbosity
    verbosity = 0 if args.quiet else args.verbosity

    print("="*70)
    print("HOT WATER TANK TEMPERATURE CONTROL SYSTEM - TEST SUITE")
    print("="*70)
    print()

    # Run tests
    if args.module:
        print(f"Running tests from module: {args.module}\n")
        result = run_specific_test(args.module, verbosity)
    else:
        print("Running all tests...\n")
        result = run_tests(verbosity)

    # Print summary
    if not args.no_summary:
        print_summary(result)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
