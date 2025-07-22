#!/usr/bin/env python3
"""Test runner for blobify with xunit output support."""

import argparse
import sys
import unittest
from pathlib import Path


def discover_and_run_tests(
    test_dir: Path,
    pattern: str = "test_*.py",
    verbosity: int = 2,
    xunit_file: str = None,
) -> bool:
    """Discover and run tests with optional xunit output."""

    # Discover tests
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern=pattern)

    # Set up test runner
    if xunit_file:
        try:
            import xmlrunner

            runner = xmlrunner.XMLTestRunner(
                output=str(Path(xunit_file).parent), outsuffix=""
            )
        except ImportError:
            print("Warning: xmlrunner not available, falling back to standard runner")
            runner = unittest.TextTestRunner(verbosity=verbosity)
    else:
        runner = unittest.TextTestRunner(verbosity=verbosity)

    # Run tests
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Run blobify tests")
    parser.add_argument("--xunit-file", help="Output xunit XML file for CI integration")
    parser.add_argument(
        "--pattern", default="test_*.py", help="Test file pattern (default: test_*.py)"
    )
    parser.add_argument(
        "--verbosity", type=int, default=2, help="Test verbosity level (default: 2)"
    )

    args = parser.parse_args()

    # Find test directory
    test_dir = Path(__file__).parent / "tests"
    if not test_dir.exists():
        print(f"Error: Test directory {test_dir} not found")
        sys.exit(1)

    # Run tests
    success = discover_and_run_tests(
        test_dir, args.pattern, args.verbosity, args.xunit_file
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
