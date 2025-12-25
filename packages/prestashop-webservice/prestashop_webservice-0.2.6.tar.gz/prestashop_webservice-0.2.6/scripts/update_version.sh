#!/bin/bash

# Script to update version in pyproject.toml and __init__.py, and create a git tag
# Usage: ./scripts/update_version.sh <new_version>
# Example: ./scripts/update_version.sh 0.2.5

set -e  # Exit on error

# Check if version argument is provided
if [ -z "$1" ]; then
    echo "Error: Version number required"
    echo "Usage: ./scripts/update_version.sh <version>"
    echo "Example: ./scripts/update_version.sh 0.2.5"
    exit 1
fi

NEW_VERSION="$1"

# Validate version format (basic semver)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format X.Y.Z (e.g., 0.2.5)"
    exit 1
fi

echo "📦 Updating version to $NEW_VERSION..."

# Get the project root directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Files to update
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"
INIT_FILE="$PROJECT_ROOT/src/prestashop_webservice/__init__.py"

# Check if files exist
if [ ! -f "$PYPROJECT_FILE" ]; then
    echo "Error: pyproject.toml not found at $PYPROJECT_FILE"
    exit 1
fi

if [ ! -f "$INIT_FILE" ]; then
    echo "Error: __init__.py not found at $INIT_FILE"
    exit 1
fi

# Update pyproject.toml
echo "📝 Updating $PYPROJECT_FILE..."
sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$PYPROJECT_FILE"

# Update __init__.py
echo "📝 Updating $INIT_FILE..."
sed -i "s/^__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" "$INIT_FILE"

# Show the changes
echo ""
echo "✅ Updated files:"
echo "   - pyproject.toml: version = \"$NEW_VERSION\""
echo "   - __init__.py: __version__ = \"$NEW_VERSION\""
echo ""

# Stage the changes
echo "📋 Staging changes..."
git add "$PYPROJECT_FILE" "$INIT_FILE"

# Amend the last commit with version changes
echo "💾 Amending last commit with version changes..."
git commit --amend --no-edit

# Create the tag
TAG_NAME="v$NEW_VERSION"
echo "🏷️  Creating tag $TAG_NAME..."
git tag "$TAG_NAME"

echo ""
echo "✨ Version update complete!"
echo ""
echo "📤 To push changes and tag to remote, run:"
echo "   git push origin main && git push origin $TAG_NAME"
echo ""
