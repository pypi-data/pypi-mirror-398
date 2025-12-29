#!/usr/bin/env python3
"""
Script to verify 95%+ test coverage for the Zoho Creator SDK.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def run_tests_with_coverage() -> int:
    """
    Run tests with coverage reporting.

    Returns:
        Exit code from pytest (0 for success, non-zero for failure)
    """
    try:
        # Run pytest with coverage using uv
        result = subprocess.run(
            [
                "uv",
                "run",
                "pytest",
                "--cov=zoho_creator_sdk",
                "--cov-report=term-missing",
                "--cov-report=xml",
                "--cov-fail-under=95",
                "-v",
            ],
            capture_output=True,
            text=True,
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Please install pytest and pytest-cov.")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def parse_coverage_xml() -> None:
    """
    Parse the coverage XML report and display detailed information.
    """
    coverage_file = Path("coverage.xml")
    if not coverage_file.exists():
        print("Coverage XML file not found.")
        return

    try:
        tree = ET.parse(coverage_file)
        root = tree.getroot()

        # Get overall coverage
        line_rate = float(root.get("line-rate", 0))
        overall_coverage = line_rate * 100

        print(f"\nOverall Coverage: {overall_coverage:.2f}%")

        # Get packages
        packages = root.find("packages")
        if packages is not None:
            for package in packages.findall("package"):
                package_name = package.get("name", "")
                package_line_rate = float(package.get("line-rate", 0)) * 100
                print(f"\nPackage: {package_name}")
                print(f"  Coverage: {package_line_rate:.2f}%")

                # Get classes in package
                for cls in package.findall("classes/class"):
                    class_name = cls.get("name", "")
                    class_filename = cls.get("filename", "")
                    class_line_rate = float(cls.get("line-rate", 0)) * 100
                    print(f"    Class: {class_name}")
                    print(f"      File: {class_filename}")
                    print(f"      Coverage: {class_line_rate:.2f}%")

                    # Show missing lines if any
                    if class_line_rate < 100:
                        lines_element = cls.find("lines")
                        if lines_element is not None:
                            missing_lines = []
                            for line in lines_element.findall("line"):
                                hits = int(line.get("hits", 0))
                                if hits == 0:
                                    line_number = line.get("number", "")
                                    missing_lines.append(line_number)

                            if missing_lines:
                                print(
                                    f"      Missing lines: {', '.join(missing_lines)}"
                                )

    except ET.ParseError as e:
        print(f"Error parsing coverage XML: {e}")
    except Exception as e:
        print(f"Error processing coverage data: {e}")


def main() -> int:
    """
    Main function to verify 95%+ coverage.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("Verifying 95%+ test coverage for Zoho Creator SDK...")
    print("=" * 50)

    # Run tests with coverage
    exit_code = run_tests_with_coverage()

    if exit_code == 0:
        print("\n✓ All tests passed with 95%+ coverage!")
    else:
        print("\n✗ Tests failed or coverage is below 95%")

        # Parse and display detailed coverage information
        print("\nDetailed Coverage Information:")
        print("-" * 30)
        parse_coverage_xml()

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
