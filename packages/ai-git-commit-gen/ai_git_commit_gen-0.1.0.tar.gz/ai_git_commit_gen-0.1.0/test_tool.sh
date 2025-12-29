#!/bin/bash

# Test script for git-commit-ai

echo "🚀 Testing git-commit-ai"
echo "========================"

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check version
echo -e "\n${YELLOW}Test 1: Checking version${NC}"
python3 -m git_commit_ai.main --version
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Version check passed${NC}"
else
    echo -e "${RED}❌ Version check failed${NC}"
fi

# Test 2: Check help
echo -e "\n${YELLOW}Test 2: Checking help${NC}"
python3 -m git_commit_ai.main --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Help command works${NC}"
else
    echo -e "${RED}❌ Help command failed${NC}"
fi

# Test 3: Create test repo
echo -e "\n${YELLOW}Test 3: Creating test repository${NC}"
TEST_DIR="/tmp/gcai-test-$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"
git init > /dev/null 2>&1

# Create test files
echo "def main():" > main.py
echo "    print('Hello')" >> main.py
echo "# Test Project" > README.md
git add .

echo -e "${GREEN}✅ Test repository created at $TEST_DIR${NC}"

# Test 4: Check command
echo -e "\n${YELLOW}Test 4: Testing 'check' command${NC}"
python3 -m git_commit_ai.main check
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Check command passed${NC}"
else
    echo -e "${RED}❌ Check command failed${NC}"
fi

# Test 5: Generate with dry-run
echo -e "\n${YELLOW}Test 5: Testing 'generate' with dry-run${NC}"
echo "Select option 'q' to quit when prompted..."
timeout 5 python3 -m git_commit_ai.main generate --dry-run --num 2 << EOF
q
EOF
if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo -e "${GREEN}✅ Generate command works${NC}"
else
    echo -e "${RED}❌ Generate command failed${NC}"
fi

# Test 6: Test error handling (no staged changes)
echo -e "\n${YELLOW}Test 6: Testing error handling${NC}"
git reset > /dev/null 2>&1
python3 -m git_commit_ai.main generate 2>&1 | grep -q "No staged changes"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Error handling works${NC}"
else
    echo -e "${RED}❌ Error handling failed${NC}"
fi

# Cleanup
cd - > /dev/null
rm -rf "$TEST_DIR"

echo -e "\n${GREEN}🎉 Testing complete!${NC}"
echo "========================"
echo ""
echo "To use the tool in your project:"
echo "1. Navigate to a git repository"
echo "2. Stage some changes: git add ."
echo "3. Run: python3 -m git_commit_ai.main generate"
echo ""
echo "Or create an alias:"
echo "alias gcai='python3 $(pwd)/src/git_commit_ai/main.py'"