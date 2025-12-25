#!/usr/bin/env python3
"""
Smart automated publishing script for perceptron-emulator.
Automatically detects version, builds, and publishes to PyPI and GitHub.
"""

import subprocess
import sys
import re
from pathlib import Path


def run_command(cmd, check=True, capture=True):
    """Run a shell command and return the result."""
    print(f"→ {cmd}")
    result = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=capture, 
        text=True,
        cwd=Path(__file__).parent
    )
    if check and result.returncode != 0:
        print(f"✗ Error: {result.stderr}")
        sys.exit(1)
    if capture:
        return result.stdout.strip()
    return ""


def get_current_version():
    """Get current version from setup.py."""
    setup_py = Path(__file__).parent / "setup.py"
    content = setup_py.read_text()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return None


def check_git_status():
    """Check if git working directory is clean."""
    status = run_command("git status --porcelain", check=False)
    if status:
        print("⚠️  Warning: Uncommitted changes detected:")
        print(status)
        response = input("\nContinue anyway? [y/N]: ").strip().lower()
        if response != 'y':
            print("Publishing cancelled.")
            sys.exit(0)


def check_pypi_credentials():
    """Check if PyPI credentials are configured."""
    try:
        run_command("python -m twine check dist/* 2>/dev/null", check=False)
        return True
    except:
        return False


def main():
    """Main publishing workflow."""
    print("=" * 70)
    print("🚀 Perceptron Emulator - Smart Automated Publishing")
    print("=" * 70)
    
    # Check if we're in the right directory
    if not Path("setup.py").exists():
        print("✗ Error: setup.py not found. Run this script from the project root.")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    if not current_version:
        print("✗ Error: Could not determine current version")
        sys.exit(1)
    
    print(f"\n📦 Current version: {current_version}")
    
    # Check git status
    print("\n🔍 Checking git status...")
    check_git_status()
    
    # Check if tag already exists
    existing_tags = run_command("git tag", check=False)
    tag_name = f"v{current_version}"
    if tag_name in existing_tags.split('\n'):
        print(f"⚠️  Tag {tag_name} already exists!")
        response = input("Overwrite tag? [y/N]: ").strip().lower()
        if response == 'y':
            run_command(f"git tag -d {tag_name}", check=False)
            run_command(f"git push origin :refs/tags/{tag_name}", check=False)
        else:
            print("Publishing cancelled.")
            sys.exit(0)
    
    # Clean previous builds
    print("\n🧹 Cleaning previous builds...")
    run_command("rm -rf dist/ build/ perceptron_emulator.egg-info", check=False)
    
    # Build distribution
    print("\n🔨 Building distribution packages...")
    run_command("python -m build")
    
    # Verify build
    print("\n✓ Build successful!")
    dist_files = list(Path("dist").glob("*"))
    for f in dist_files:
        print(f"  • {f.name}")
    
    # Check packages
    print("\n🔍 Checking package integrity...")
    run_command("python -m twine check dist/*")
    print("✓ Packages are valid!")
    
    # Publish to PyPI
    print("\n" + "=" * 70)
    print("📤 Publishing to PyPI...")
    print("=" * 70)
    
    # Check if already published
    try:
        import requests
        response = requests.get(f"https://pypi.org/pypi/perceptron-emulator/{current_version}/json")
        if response.status_code == 200:
            print(f"⚠️  Version {current_version} already exists on PyPI!")
            print("You need to bump the version number before publishing.")
            sys.exit(1)
    except:
        pass  # Network error or package doesn't exist yet
    
    print("\n⚠️  You will need your PyPI credentials (or API token)")
    print("Tip: Use API token for better security")
    print("     Create one at: https://pypi.org/manage/account/token/\n")
    
    response = input("Publish to PyPI now? [Y/n]: ").strip().lower()
    if response in ['', 'y', 'yes']:
        try:
            run_command("python -m twine upload dist/*", capture=False)
            print("\n✓ Successfully published to PyPI!")
            print(f"   https://pypi.org/project/perceptron-emulator/{current_version}/")
        except:
            print("\n✗ PyPI upload failed. You can retry manually:")
            print("   python -m twine upload dist/*")
    else:
        print("⊘ Skipped PyPI publishing")
    
    # Push to GitHub
    print("\n" + "=" * 70)
    print("📤 Pushing to GitHub...")
    print("=" * 70)
    
    response = input("\nPush commits and tags to GitHub? [Y/n]: ").strip().lower()
    if response in ['', 'y', 'yes']:
        # Create tag if it doesn't exist
        if tag_name not in existing_tags.split('\n'):
            print(f"\n🏷️  Creating tag {tag_name}...")
            run_command(f'git tag -a {tag_name} -m "Version {current_version}"')
        
        print("\n📤 Pushing to GitHub...")
        run_command("git push origin main", check=False)
        run_command("git push origin --tags", check=False)
        print("✓ Pushed to GitHub!")
        print(f"   https://github.com/rexackermann/perceptron-emulator")
    else:
        print("⊘ Skipped GitHub push")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ Publishing Complete!")
    print("=" * 70)
    print(f"\n📦 Version: {current_version}")
    print(f"🏷️  Tag: {tag_name}")
    print("\n🔗 Links:")
    print(f"   PyPI: https://pypi.org/project/perceptron-emulator/{current_version}/")
    print(f"   GitHub: https://github.com/rexackermann/perceptron-emulator/releases/tag/{tag_name}")
    print("\n💡 Next steps:")
    print("   • Create GitHub release with release notes")
    print("   • Test installation: pip install --upgrade perceptron-emulator")
    print("   • Share on social media! 🎉")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⊘ Publishing cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
