#!/usr/bin/env python3
import subprocess
import sys

def run_tests():
    """Run all tests"""
    # Run pytest with coverage
    cmd = [
        "pytest",
        "-v",
        "--cov=src/pyenvdoctor",
        "--cov-report=term-missing",
        "tests/"
    ]
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
