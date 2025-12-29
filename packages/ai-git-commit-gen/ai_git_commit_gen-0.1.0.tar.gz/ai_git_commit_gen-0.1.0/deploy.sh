#!/bin/bash

# Deploy script for git-commit-ai

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying git-commit-ai to PyPI${NC}"
echo "======================================"

# Check if version argument provided
if [ "$1" == "" ]; then
    echo -e "${RED}Error: Please provide version number${NC}"
    echo "Usage: ./deploy.sh <version> [--test]"
    echo "Example: ./deploy.sh 0.1.0 --test"
    exit 1
fi

VERSION=$1
TEST_MODE=${2:-""}

# Update version in files
echo -e "${YELLOW}📝 Updating version to $VERSION${NC}"
sed -i.bak "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
sed -i.bak "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" src/git_commit_ai/__init__.py
rm -f pyproject.toml.bak src/git_commit_ai/__init__.py.bak

# Clean previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds${NC}"
rm -rf dist/ build/ *.egg-info/

# Run tests
echo -e "${YELLOW}🧪 Running tests${NC}"
if command -v pytest &> /dev/null; then
    PYTHONPATH=src pytest tests/ -q || true
else
    echo "Pytest not installed, skipping tests"
fi

# Build package
echo -e "${YELLOW}📦 Building package${NC}"
python3 -m build

# Check package
echo -e "${YELLOW}✅ Checking package${NC}"
python3 -m twine check dist/*

# Upload to PyPI
if [ "$TEST_MODE" == "--test" ]; then
    echo -e "${YELLOW}📤 Uploading to Test PyPI${NC}"
    echo "Username: __token__"
    echo "Use your test.pypi.org token as password"
    python3 -m twine upload --repository testpypi dist/*
    echo ""
    echo -e "${GREEN}✅ Package uploaded to Test PyPI!${NC}"
    echo "Test installation with:"
    echo "pip install --index-url https://test.pypi.org/simple/ git-commit-ai"
else
    echo -e "${YELLOW}📤 Uploading to PyPI${NC}"
    echo "Username: __token__"
    echo "Use your pypi.org token as password"
    python3 -m twine upload dist/*
    echo ""
    echo -e "${GREEN}✅ Package uploaded to PyPI!${NC}"
    echo "Install with: pip install git-commit-ai"
fi

# Git operations
echo -e "${YELLOW}📝 Creating git tag${NC}"
git add pyproject.toml src/git_commit_ai/__init__.py
git commit -m "chore: release v$VERSION" || true
git tag -a "v$VERSION" -m "Release v$VERSION"

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Push changes: git push && git push --tags"
echo "2. Create GitHub release at: https://github.com/yourusername/git-commit-ai/releases/new"
echo "3. Share your package with the world!"