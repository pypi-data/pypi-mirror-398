"""
Test runner script for the polerisk package.

This script provides a convenient way to run different types of tests
with various configurations and reporting options.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """Run a command and handle the output."""
    logger.debug(f"\n{'='*60}")
    logger.debug(f"Running: {description}")
    logger.debug(f"Command: {' '.join(cmd)}")
    logger.debug(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(result.stdout)
        if result.stderr:
            logger.debug("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR: {description} failed with exit code {e.returncode}")
        logger.debug("STDOUT:", e.stdout)
        logger.debug("STDERR:", e.stderr)
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Run tests for the polerisk package"
    )

    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all", "performance"],
        default="all",
        help="Type of tests to run (default: all)",
    )

    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage reporting"
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Run tests in verbose mode"
    )

    parser.add_argument("--fast", action="store_true", help="Skip slow tests")

    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")

    parser.add_argument(
        "--html-report", action="store_true", help="Generate HTML coverage report"
    )

    parser.add_argument(
        "--lint", action="store_true", help="Run linting checks before tests"
    )

    parser.add_argument(
        "--format", action="store_true", help="Run code formatting checks"
    )

    args = parser.parse_args()

    # Change to project directory
    project_root = Path(__file__).parent
    logger.debug(f"Running tests from: {project_root}")

    success = True

    # Run linting if requested
    if args.lint:
        lint_cmd = ["flake8", "polerisk/", "--max-line-length=88"]
        success &= run_command(lint_cmd, "Code linting (flake8)")

        isort_cmd = ["isort", "polerisk/", "--check-only", "--profile=black"]
        success &= run_command(isort_cmd, "Import sorting check (isort)")

    # Run formatting checks if requested
    if args.format:
        black_cmd = ["black", "polerisk/", "--check", "--line-length=88"]
        success &= run_command(black_cmd, "Code formatting check (black)")

    # Build test command
    test_cmd = ["python", "-m", "pytest"]

    # Add test directory
    test_cmd.append("tests/")

    # Add test type markers
    if args.type == "unit":
        test_cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        test_cmd.extend(["-m", "integration"])
    elif args.type == "performance":
        test_cmd.extend(["-m", "performance"])
    # For "all", don't add any markers

    # Add fast option (skip slow tests)
    if args.fast:
        test_cmd.extend(["-m", "not slow"])

    # Add verbose option
    if args.verbose:
        test_cmd.append("-v")

    # Add parallel option
    if args.parallel:
        test_cmd.extend(["-n", "auto"])

    # Add coverage options
    if args.coverage:
        test_cmd.extend(
            ["--cov=polerisk", "--cov-report=term-missing", "--cov-report=xml"]
        )

        if args.html_report:
            test_cmd.append("--cov-report=html")

    # Run the tests
    success &= run_command(test_cmd, f"Running {args.type} tests")

    # Print summary
    logger.debug(f"\n{'='*60}")
    if success:
        logger.debug(" All tests and checks passed!")
    else:
        logger.error(" Some tests or checks failed!")
        sys.exit(1)

    # Print coverage report location if generated
    if args.coverage and args.html_report:
        html_report = project_root / "htmlcov" / "index.html"
        if html_report.exists():
            logger.debug(f" HTML coverage report: {html_report}")


if __name__ == "__main__":
    main()
