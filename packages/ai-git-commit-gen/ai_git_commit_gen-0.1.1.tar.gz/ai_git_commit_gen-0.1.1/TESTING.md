# 🧪 Testing Guide for git-commit-ai

## 📋 Prerequisites

Ensure you have Python 3.9+ and Git installed:
```bash
python3 --version
git --version
```

## 🚀 Quick Test Setup

### Option 1: Run Directly (Without Installation)

```bash
# Run the tool directly from source
python3 -m src.git_commit_ai.main --help

# Create an alias for easier testing
alias gcai="python3 -m src.git_commit_ai.main"
```

### Option 2: Install in Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install the package
pip install -e .

# Now you can use gcai command
gcai --help
```

## 🎯 Testing Scenarios

### Test 1: Basic Functionality Check

```bash
# Check version
python3 -m src.git_commit_ai.main --version

# Check help
python3 -m src.git_commit_ai.main --help

# Check available commands
python3 -m src.git_commit_ai.main generate --help
```

### Test 2: Initialize a Test Git Repository

```bash
# Create test directory
mkdir test-repo
cd test-repo

# Initialize git
git init

# Create test files
echo "def hello():\n    print('Hello World')" > hello.py
echo "# Test Project\nThis is a test" > README.md

# Stage files
git add .

# Test the check command
python3 -m ../src.git_commit_ai.main check
```

### Test 3: Generate Commit Messages

```bash
# In the test-repo directory with staged changes
python3 -m ../src.git_commit_ai.main generate

# Try different options:

# Auto-commit with first suggestion
python3 -m ../src.git_commit_ai.main generate --auto --dry-run

# Generate 5 suggestions
python3 -m ../src.git_commit_ai.main generate --num 5

# Use Gitmoji style
python3 -m ../src.git_commit_ai.main generate --style gitmoji

# Use Simple style
python3 -m ../src.git_commit_ai.main generate --style simple
```

### Test 4: Test with Real Code Changes

```bash
# Make some real changes
echo "def goodbye():\n    print('Goodbye')" >> hello.py
echo "\n## Features\n- Hello function" >> README.md

# Stage changes
git add .

# Generate messages for modifications
python3 -m ../src.git_commit_ai.main generate
```

### Test 5: Test Error Handling

```bash
# Test outside git repository
cd /tmp
python3 -m /path/to/git-commit-ai/src.git_commit_ai.main generate
# Should show: "❌ Error: Not a git repository"

# Test with no staged changes
cd /path/to/test-repo
git reset  # Unstage all files
python3 -m ../src.git_commit_ai.main generate
# Should show: "❌ No staged changes found"
```

### Test 6: Interactive Mode Testing

When you run generate without `--auto`, test these interactions:
- Press `1-3` to select a message
- Press `r` to regenerate new suggestions
- Press `e` to edit a message
- Press `q` to quit without committing

## 🔬 Unit Tests

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=git_commit_ai --cov-report=term-missing

# Run specific test file
pytest tests/test_cli.py -v

# Run specific test
pytest tests/test_cli.py::test_version -v
```

## 🐛 Debugging Tips

### 1. Enable Verbose Output

Add print statements in the code or use Python debugger:
```python
import pdb; pdb.set_trace()
```

### 2. Check API Connectivity

Test if HuggingFace API is accessible:
```python
import httpx
response = httpx.get("https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3")
print(response.status_code)
```

### 3. Test Cache System

```bash
# Check if cache is created
ls -la ~/.cache/git-commit-ai/

# Clear cache if needed
rm -rf ~/.cache/git-commit-ai/
```

## 📝 Manual Testing Checklist

- [ ] Tool installs successfully
- [ ] `--help` shows all commands
- [ ] `check` command identifies git repo correctly
- [ ] `check` command shows staged files
- [ ] `generate` produces 3 suggestions by default
- [ ] `--num` option changes suggestion count
- [ ] `--style` changes message format
- [ ] Interactive selection works (1-3, r, e, q)
- [ ] `--auto` commits automatically
- [ ] `--dry-run` prevents actual commit
- [ ] Error messages are clear and helpful
- [ ] Caching works for identical changes
- [ ] Fallback messages work when API fails

## 🎨 Sample Test Output

When everything works correctly:

```
$ python3 -m src.git_commit_ai.main generate

🔍 Analyzing staged changes...

📁 Files changed:
   ✨ hello.py (added)
   ✨ README.md (added)

✨ Generating commit messages...

✨ Suggested commit messages:

  [1] feat: add hello function and project documentation
  [2] chore: initialize project with hello module
  [3] docs: add README and hello world implementation

Select [1-3], [r]egenerate, [e]dit, or [q]uit:
```

## 🚨 Common Issues & Solutions

### Issue: "Not a git repository"
**Solution:** Make sure you're in a directory with `.git` folder

### Issue: "No staged changes found"
**Solution:** Stage files with `git add .` first

### Issue: "API is busy, retrying..."
**Solution:** Wait a moment, the tool will retry automatically

### Issue: Module not found errors
**Solution:** Make sure you're in the project root directory or adjust the Python path

## 🎉 Success Indicators

✅ Tool runs without errors
✅ Generates meaningful commit messages
✅ Interactive mode works smoothly
✅ All test commands produce expected output
✅ Unit tests pass with good coverage