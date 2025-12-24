#!/usr/bin/env python3
"""
Release script for synth-data-eval package.

This script helps create releases by:
1. Checking if the version is properly updated
2. Running tests and quality checks
3. Creating a git tag
4. Pushing the tag to trigger the release workflow

Usage:
    python scripts/make_release.py [patch|minor|major]

Or to release a specific version:
    python scripts/make_release.py v1.2.3
"""

import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)
    return result


def get_current_version():
    """Get the current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path, "r") as f:
        content = f.read()

    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        print("❌ Could not find version in pyproject.toml")
        sys.exit(1)

    return match.group(1)


def update_version(current_version, bump_type):
    """Update version based on bump type."""
    major, minor, patch = map(int, current_version.split("."))

    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        print(f"❌ Invalid bump type: {bump_type}")
        sys.exit(1)

    return f"{major}.{minor}.{patch}"


def update_pyproject_version(new_version):
    """Update version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path, "r") as f:
        content = f.read()

    # Update version
    content = re.sub(r'version\s*=\s*"[^"]*"', f'version = "{new_version}"', content)

    with open(pyproject_path, "w") as f:
        f.write(content)

    print(f"✅ Updated version to {new_version} in pyproject.toml")


def update_changelog(new_version):
    """Update CHANGELOG.md with new version."""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print("⚠️  CHANGELOG.md not found, skipping update")
        return

    with open(changelog_path, "r") as f:
        content = f.read()

    # Replace [Unreleased] with the new version
    today = subprocess.run(["date", "+%Y-%m-%d"], capture_output=True, text=True).stdout.strip()
    content = content.replace("## [Unreleased]", f"## [Unreleased]\n\n## [{new_version}] - {today}")

    with open(changelog_path, "w") as f:
        f.write(content)

    print(f"✅ Updated CHANGELOG.md with version {new_version}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/make_release.py " "[patch|minor|major|v1.2.3]")
        sys.exit(1)

    arg = sys.argv[1]

    # Check if it's a specific version or a bump type
    if arg.startswith("v"):
        new_version = arg[1:]  # Remove 'v' prefix
        bump_type = None
    elif arg in ["patch", "minor", "major"]:
        current_version = get_current_version()
        new_version = update_version(current_version, arg)
        bump_type = arg
    else:
        print(f"❌ Invalid argument: {arg}")
        print("Usage: python scripts/make_release.py " "[patch|minor|major|v1.2.3]")
        sys.exit(1)

    print(f"🚀 Preparing release {new_version}")

    # Run quality checks
    print("\n🔍 Running quality checks...")
    run_command("pre-commit run --all-files")
    run_command("python -m pytest tests/ -v")

    # Update version if it's a bump
    if bump_type:
        update_pyproject_version(new_version)
        update_changelog(new_version)

    # Build package to ensure it works
    print("\n📦 Building package...")
    run_command("rm -rf dist/")
    run_command("python -m build")

    # Commit changes if any
    if bump_type:
        run_command("git add pyproject.toml CHANGELOG.md")
        run_command(f'git commit -m "Release version {new_version}"')

    # Create and push tag
    tag_name = f"v{new_version}"
    run_command(f"git tag -a {tag_name} -m 'Release {new_version}'")
    run_command(f"git push origin {tag_name}")

    print("\n✅ Release created successfully!")
    print(f"   Version: {new_version}")
    print(f"   Tag: {tag_name}")
    print("   The GitHub Actions workflow will now publish to PyPI")
    print(
        "   Check the Actions tab for progress: "
        "https://github.com/ahmed-fouad-lagha/synth-data-eval/actions"
    )


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
