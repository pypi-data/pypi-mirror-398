#!/usr/bin/env python3
"""
Automated publishing script for perceptron-emulator.
Bumps version, builds distribution, and publishes to PyPI and GitHub.
"""

import subprocess
import sys
import re
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def get_current_version():
    """Get current version from setup.py."""
    setup_py = Path("setup.py").read_text()
    match = re.search(r'version="([^"]+)"', setup_py)
    if match:
        return match.group(1)
    return None


def bump_version(current_version, bump_type="patch"):
    """Bump version number (major.minor.patch)."""
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"


def update_version_in_files(new_version):
    """Update version in setup.py and pyproject.toml."""
    # Update setup.py
    setup_py = Path("setup.py")
    content = setup_py.read_text()
    content = re.sub(r'version="[^"]+"', f'version="{new_version}"', content)
    setup_py.write_text(content)
    
    # Update pyproject.toml
    pyproject = Path("pyproject.toml")
    content = pyproject.read_text()
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    pyproject.write_text(content)
    
    print(f"Updated version to {new_version}")


def main():
    """Main publishing workflow."""
    print("=" * 60)
    print("Perceptron Emulator - Automated Publishing")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("setup.py").exists():
        print("Error: setup.py not found. Run this script from the project root.")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    if not current_version:
        print("Error: Could not determine current version")
        sys.exit(1)
    
    print(f"\nCurrent version: {current_version}")
    
    # Ask for bump type
    print("\nVersion bump type:")
    print("  1. Patch (x.x.X) - Bug fixes")
    print("  2. Minor (x.X.0) - New features")
    print("  3. Major (X.0.0) - Breaking changes")
    
    choice = input("\nSelect bump type [1/2/3] (default: 1): ").strip() or "1"
    
    bump_types = {"1": "patch", "2": "minor", "3": "major"}
    bump_type = bump_types.get(choice, "patch")
    
    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    print(f"\nNew version will be: {new_version}")
    
    # Confirm
    confirm = input("\nProceed with publishing? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Publishing cancelled.")
        sys.exit(0)
    
    # Update version in files
    update_version_in_files(new_version)
    
    # Git commit and tag
    print("\n" + "=" * 60)
    print("Committing version bump...")
    print("=" * 60)
    run_command(f'git add setup.py pyproject.toml')
    run_command(f'git commit -m "Bump version to {new_version}"')
    run_command(f'git tag -a v{new_version} -m "Version {new_version}"')
    
    # Build distribution
    print("\n" + "=" * 60)
    print("Building distribution...")
    print("=" * 60)
    run_command('rm -rf dist/ build/ *.egg-info')
    run_command('python -m build')
    
    # Publish to PyPI
    print("\n" + "=" * 60)
    print("Publishing to PyPI...")
    print("=" * 60)
    publish = input("Publish to PyPI? [y/N]: ").strip().lower()
    if publish == 'y':
        run_command('twine upload dist/*')
        print("✓ Published to PyPI")
    else:
        print("Skipped PyPI publishing")
    
    # Push to GitHub
    print("\n" + "=" * 60)
    print("Pushing to GitHub...")
    print("=" * 60)
    push = input("Push to GitHub? [y/N]: ").strip().lower()
    if push == 'y':
        run_command('git push origin main')
        run_command('git push origin --tags')
        print("✓ Pushed to GitHub")
    else:
        print("Skipped GitHub push")
    
    print("\n" + "=" * 60)
    print(f"✓ Publishing complete! Version {new_version}")
    print("=" * 60)
    print("\nNext steps:")
    if publish != 'y':
        print("  - Run: twine upload dist/*")
    if push != 'y':
        print("  - Run: git push origin main --tags")
    print(f"  - Create GitHub release: https://github.com/rexackermann/perceptron-emulator/releases/new?tag=v{new_version}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPublishing cancelled by user.")
        sys.exit(1)
