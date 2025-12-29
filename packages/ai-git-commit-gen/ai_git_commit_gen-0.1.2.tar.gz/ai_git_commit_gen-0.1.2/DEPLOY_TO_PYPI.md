# 🚀 Deploying git-commit-ai to PyPI

## 📋 Pre-Deployment Checklist

- [ ] Update version number in `pyproject.toml` and `__init__.py`
- [ ] Test the package locally
- [ ] Update README.md with latest features
- [ ] Create GitHub release tag
- [ ] Ensure all tests pass
- [ ] Update CHANGELOG.md (if exists)

## 🔧 Step 1: Prepare Your Environment

### Install Required Tools

```bash
# Install build tools
pip install --upgrade pip
pip install --upgrade build twine

# Install development dependencies (optional but recommended)
pip install pytest pytest-cov ruff
```

## 📦 Step 2: Update Package Metadata

### Update Version Number

Edit `pyproject.toml`:
```toml
[project]
name = "git-commit-ai"
version = "0.1.0"  # Update this for each release (0.1.1, 0.2.0, etc.)
```

Edit `src/git_commit_ai/__init__.py`:
```python
__version__ = "0.1.0"  # Keep in sync with pyproject.toml
```

### Update Author Information

Edit `pyproject.toml`:
```toml
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]

[project.urls]
Homepage = "https://github.com/yourusername/git-commit-ai"
Repository = "https://github.com/yourusername/git-commit-ai"
Issues = "https://github.com/yourusername/git-commit-ai/issues"
```

## 🧪 Step 3: Test Locally

### Run Tests

```bash
# Run unit tests
pytest tests/

# Check code quality
ruff check src tests

# Test the CLI
python -m src.git_commit_ai.main --help
```

### Test Package Build

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

# Check the built files
ls -la dist/
# You should see:
# git_commit_ai-0.1.0-py3-none-any.whl
# git_commit_ai-0.1.0.tar.gz
```

### Test Installation from Built Package

```bash
# Create a test virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from the built wheel
pip install dist/git_commit_ai-0.1.0-py3-none-any.whl

# Test the installed package
gcai --version
gcai --help

# Clean up
deactivate
rm -rf test_env
```

## 📤 Step 4: Upload to PyPI

### Option A: Upload to Test PyPI First (Recommended)

Test PyPI lets you practice without affecting the real package index.

#### 1. Create Test PyPI Account
- Go to https://test.pypi.org/account/register/
- Create an account and verify email

#### 2. Create API Token
- Go to https://test.pypi.org/manage/account/token/
- Create a new API token (scope: "Entire account")
- Save the token securely

#### 3. Upload to Test PyPI

```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# You'll be prompted for credentials:
# Username: __token__
# Password: <paste your test.pypi.org token>
```

#### 4. Test Installation from Test PyPI

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps git-commit-ai

# Test it works
gcai --version
```

### Option B: Upload to Production PyPI

#### 1. Create PyPI Account
- Go to https://pypi.org/account/register/
- Create an account and verify email
- Enable 2FA (highly recommended)

#### 2. Create API Token
- Go to https://pypi.org/manage/account/token/
- Create a new API token
- Scope: "Entire account" (or project-specific after first upload)
- Save the token securely

#### 3. Configure Authentication

Create `~/.pypirc` file:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZwIkZDlkYzMxMzctN2E2My00OTJlLWE4ZDAtZGMxZjQzNGJmYmMwAAIqWzMsIjYyYzE1YTM1LTc4YzEtNDgxNS04NTgyLTUyYTRiZDhiNTkzMyJdAAAGIAJUSEGH7mDHlQdrzPqCBMADpDpyOJB-0dBV-WT93OKpv

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZwIkZDlkYzMxMzctN2E2My00OTJlLWE4ZDAtZGMxZjQzNGJmYmMwAAIqWzMsIjYyYzE1YTM1LTc4YzEtNDgxNS04NTgyLTUyYTRiZDhiNTkzMyJdAAAGIAJUSEGH7mDHlQdrzPqCBMADpDpyOJB-0dBV-WT93OKp
```

**Security Note:** chmod 600 ~/.pypirc to protect your tokens

#### 4. Upload to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*

# Or if using .pypirc:
python -m twine upload --repository pypi dist/*
```

## 🤖 Step 5: Automate with GitHub Actions

### Create GitHub Secrets

1. Go to your GitHub repo → Settings → Secrets → Actions
2. Add new secret: `PYPI_API_TOKEN` with your PyPI token

### GitHub Action is Already Configured

The `.github/workflows/publish.yml` file is already set up to:
- Trigger on GitHub releases
- Build the package
- Upload to PyPI automatically

### To Publish via GitHub:

```bash
# 1. Commit all changes
git add .
git commit -m "chore: prepare for v0.1.0 release"
git push

# 2. Create and push a tag
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# 3. Create a GitHub release
# Go to https://github.com/yourusername/git-commit-ai/releases
# Click "Create a new release"
# Choose the tag v0.1.0
# Add release notes
# Publish release

# The GitHub Action will automatically:
# - Build the package
# - Upload to PyPI
# - Users can now: pip install git-commit-ai
```

## 📊 Step 6: Verify Deployment

### Check PyPI Page

Visit: https://pypi.org/project/git-commit-ai/

You should see:
- Package description
- Installation command
- Project links
- Release history

### Test Installation

```bash
# Test on a clean environment
pip install git-commit-ai

# Verify it works
gcai --version
gcai --help
```

## 🔄 Step 7: Updates and New Releases

For each new release:

1. **Update version** in `pyproject.toml` and `__init__.py`
2. **Update README** if needed
3. **Run tests** to ensure everything works
4. **Build package**: `python -m build`
5. **Create git tag**: `git tag -a v0.2.0 -m "Release v0.2.0"`
6. **Push tag**: `git push origin v0.2.0`
7. **Create GitHub release** → Auto-publishes to PyPI

## ⚠️ Common Issues and Solutions

### Issue: "Package name already taken"
**Solution:** The name `git-commit-ai` might be taken. Try:
- `git-commit-ai-tool`
- `gitcommit-ai`
- `git-commit-assistant`

Update the name in `pyproject.toml`:
```toml
[project]
name = "git-commit-ai-tool"  # New unique name
```

### Issue: "Invalid token"
**Solution:**
- Make sure to use `__token__` as username
- Paste token including the `pypi-` prefix
- Check token hasn't expired

### Issue: "Module not found after installation"
**Solution:** Check your `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/git_commit_ai"]  # Must match your structure
```

### Issue: "Command 'gcai' not found"
**Solution:** Check the entry point in `pyproject.toml`:
```toml
[project.scripts]
gcai = "git_commit_ai.main:main"  # Must match your main function
```

## 📈 Post-Deployment

### Monitor Your Package

- Check download stats: https://pypistats.org/packages/git-commit-ai
- Monitor issues: GitHub Issues page
- Respond to user feedback
- Regular updates and bug fixes

### Announce Your Package

1. **GitHub README**: Add PyPI badge
```markdown
[![PyPI version](https://badge.fury.io/py/git-commit-ai.svg)](https://badge.fury.io/py/git-commit-ai)
```

2. **Social Media**: Share on Twitter/LinkedIn
3. **Dev Communities**: Post on Reddit (r/Python), Dev.to, Hacker News
4. **Documentation**: Create docs on ReadTheDocs or GitHub Pages

## 🎉 Success!

Once deployed, users worldwide can install your package with:

```bash
pip install git-commit-ai
```

And start using it immediately:

```bash
gcai generate
```

---

## Quick Deploy Commands (Summary)

```bash
# 1. Update version in pyproject.toml and __init__.py

# 2. Build
python -m build

# 3. Check
twine check dist/*

# 4. Upload to Test PyPI
twine upload --repository testpypi dist/*

# 5. Test
pip install --index-url https://test.pypi.org/simple/ git-commit-ai

# 6. Upload to Production PyPI
twine upload dist/*

# 7. Celebrate! 🎉
```