#!/bin/bash
# Release script for py-mcp-installer-service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

# Detect Python executable
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)

# Get bump type (default: patch)
BUMP_TYPE="${1:-patch}"

# Get current version
CURRENT_VERSION=$($PYTHON scripts/manage_version.py)
echo "Current version: $CURRENT_VERSION"

# Bump version
NEW_VERSION=$($PYTHON scripts/manage_version.py bump "$BUMP_TYPE")
echo "New version: $NEW_VERSION"

# Commit version changes
git add VERSION src/py_mcp_installer/__init__.py
git commit -m "chore: bump version to $NEW_VERSION"

# Create git tag
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"

# Push changes and tag
git push origin main
git push origin "v$NEW_VERSION"

# Create GitHub release
gh release create "v$NEW_VERSION" \
    --title "py-mcp-installer-service v$NEW_VERSION" \
    --notes "See CHANGELOG.md for details" \
    --repo bobmatnyc/py-mcp-installer-service

echo "✅ Released py-mcp-installer-service v$NEW_VERSION"
