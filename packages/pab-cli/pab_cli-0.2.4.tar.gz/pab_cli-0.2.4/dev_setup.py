#!/usr/bin/env python3
"""
Development setup script for PAB
"""

import os
import subprocess
import sys


def run_command(command, description):
    """Run a command and print its status"""
    print(f"\n🔧 {description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ {description} failed")
        if result.stderr:
            print(result.stderr)
        return False
    return True


def main():
    """Main setup function"""
    print("🚀 Setting up PAB development environment...")

    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  It's recommended to run this in a virtual environment")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled")
            return

    # Install development dependencies
    dev_deps = [
        "pytest>=6.0.0",
        "pytest-cov>=2.0.0",
        "black>=21.0.0",
        "flake8>=3.8.0",
        "mypy>=0.800",
        "twine>=3.0.0",
        "build>=0.3.0"
    ]

    print("\n📦 Installing development dependencies...")
    for dep in dev_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            print(f"Failed to install {dep}")
            return

    # Install package in development mode
    if not run_command("pip install -e .", "Installing PAB in development mode"):
        return

    # Run tests
    if not run_command("python -m pytest tests/ -v", "Running tests"):
        print("⚠️  Some tests failed, but setup continued")

    # Check code style
    if not run_command("flake8 pab --max-line-length=88 --ignore=E203,W503", "Checking code style"):
        print("⚠️  Code style issues found, but setup continued")

    print("\n🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Run 'pab --help' to see available commands")
    print("2. Run 'python -m pytest' to run tests")
    print("3. Run 'black pab/' to format code")
    print("4. Run 'flake8 pab/' to check code style")


if __name__ == "__main__":
    main()
