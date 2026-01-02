# PyPI Release Guide - v1.1.0a1

This document provides step-by-step instructions for publishing Todo CLI v1.1.0a1 to PyPI.

## Pre-Release Checklist

### ✅ Completed

- [x] Version updated to 1.1.0a1 in `pyproject.toml`
- [x] Version updated to 1.1.0a1 in `todo_cli/__init__.py`
- [x] CHANGELOG.md updated with release notes
- [x] README.md updated with Epic 1 features
- [x] MIGRATION_GUIDE.md created
- [x] All tests passing (313 tests, 87% coverage)
- [x] Git commit created for release
- [x] Git tag created (v1.1.0a1)
- [x] Documentation complete and accurate

### 🔲 To Complete Before Release

- [ ] Install build tools
- [ ] Build distribution packages
- [ ] Test installation locally
- [ ] Upload to TestPyPI (recommended)
- [ ] Test from TestPyPI
- [ ] Upload to production PyPI
- [ ] Verify PyPI page
- [ ] Test installation from PyPI

---

## Step-by-Step Release Process

### 1. Install Build Tools

```bash
# Install/upgrade build tools
pip install --upgrade build twine
```

**Verify installation:**
```bash
python -m build --version
twine --version
```

### 2. Build Distribution Packages

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build

# You should see:
# Successfully built todo-cli-1.1.0a1.tar.gz and todo_cli-1.1.0a1-py3-none-any.whl
```

**Verify build outputs:**
```bash
ls -lh dist/

# Should show:
# todo-cli-1.1.0a1.tar.gz
# todo_cli-1.1.0a1-py3-none-any.whl
```

### 3. Test Installation Locally

```bash
# Create test virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from local wheel
pip install dist/todo_cli-1.1.0a1-py3-none-any.whl

# Verify installation
todo version  # Should show: Todo CLI v1.1.0a1

# Test basic functionality
todo add "Test task"
todo list
todo project create "Test Project"
todo project list

# Cleanup
deactivate
rm -rf test_env
```

### 4. Upload to TestPyPI (Recommended)

TestPyPI is a separate PyPI instance for testing. Highly recommended before production release.

**Setup TestPyPI account:**
1. Create account at https://test.pypi.org/account/register/
2. Verify email
3. Generate API token at https://test.pypi.org/manage/account/token/
4. Save token securely

**Configure authentication:**
```bash
# Create/edit ~/.pypirc
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR-PYPI-TOKEN-HERE
EOF

chmod 600 ~/.pypirc
```

**Upload to TestPyPI:**
```bash
# Upload using twine
twine upload --repository testpypi dist/*

# You should see:
# Uploading todo-cli-1.1.0a1.tar.gz
# Uploading todo_cli-1.1.0a1-py3-none-any.whl
# View at: https://test.pypi.org/project/todo-cli/1.1.0a1/
```

### 5. Test from TestPyPI

```bash
# Create test environment
python -m venv testpypi_env
source testpypi_env/bin/activate

# Install from TestPyPI
# Note: Dependencies come from regular PyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            todo-cli==1.1.0a1

# Verify version
todo version

# Run comprehensive tests
todo add "Integration test task" -p p0 --tags test
todo project create "Test Project" --description "Testing from TestPyPI"
todo add "Project task" -P "Test Project"
todo list
todo list --project "Test Project"
todo start 1
sleep 5
todo stop
todo done 1
todo stats
todo export json test_export.json

# Verify export file
cat test_export.json

# Cleanup
deactivate
rm -rf testpypi_env test_export.json
```

### 6. Upload to Production PyPI

**⚠️ Warning:** This step is irreversible. Once uploaded, you cannot replace or delete a release.

**Final verification before upload:**
```bash
# Double-check version
grep "version = " pyproject.toml
grep "__version__" todo_cli/__init__.py

# Verify CHANGELOG is complete
head -50 CHANGELOG.md

# Verify README is accurate
head -100 README.md

# Ensure all tests pass
pytest --cov=todo_cli
```

**Setup PyPI account:**
1. Create account at https://pypi.org/account/register/
2. Verify email
3. Generate API token at https://pypi.org/manage/account/token/
4. Save token in `~/.pypirc` (see step 4)

**Upload to PyPI:**
```bash
# Upload using twine
twine upload dist/*

# You should see:
# Uploading todo-cli-1.1.0a1.tar.gz
# Uploading todo_cli-1.1.0a1-py3-none-any.whl
# View at: https://pypi.org/project/todo-cli/1.1.0a1/
```

### 7. Verify PyPI Page

Visit https://pypi.org/project/todo-cli/1.1.0a1/ and verify:

- [ ] Project description renders correctly (from README.md)
- [ ] Version shows as 1.1.0a1
- [ ] All metadata is correct (author, license, keywords)
- [ ] Project links work (homepage, repository, issues)
- [ ] Classifiers are appropriate
- [ ] Download files are present (tar.gz and .whl)

### 8. Test Installation from PyPI

```bash
# Create fresh environment
python -m venv pypi_test_env
source pypi_test_env/bin/activate

# Install from PyPI
pip install agile-todo-cli==1.1.0a1

# Verify version
todo version  # Should show: Todo CLI v1.1.0a1

# Run smoke tests
todo add "Production test"
todo list
todo project create "PyPI Test"
todo add "Task in project" -P "PyPI Test"
todo list --project "PyPI Test"
todo stats

# Cleanup
deactivate
rm -rf pypi_test_env
```

---

## Post-Release Tasks

### 1. Push Git Changes

```bash
# Push commit
git push origin main

# Push tag
git push origin v1.1.0a1
```

### 2. Create GitHub Release

1. Go to https://github.com/AgileInnov8tor/todo-cli/releases/new
2. Choose tag: `v1.1.0a1`
3. Release title: `v1.1.0a1 - Epic 1: Foundation (Alpha)`
4. Description: Copy from `.github/RELEASE_NOTES_v1.1.0a1.md`
5. Check "This is a pre-release" (important for alpha)
6. Publish release

### 3. Announce Release

Post announcement to GitHub Discussions (use template from `ANNOUNCEMENT_TEMPLATE.md`)

### 4. Monitor for Issues

- Watch GitHub Issues for bug reports
- Monitor PyPI downloads
- Check CI/CD builds
- Respond to user feedback

---

## Troubleshooting

### Build Fails

```bash
# Clean everything
rm -rf dist/ build/ *.egg-info __pycache__ todo_cli/__pycache__

# Upgrade build tools
pip install --upgrade build setuptools wheel

# Try build again
python -m build
```

### Upload Fails - "File already exists"

This error means the version is already on PyPI. You cannot re-upload the same version.

**Solution:**
- Increment version (e.g., 1.1.0a2) if this is a mistake
- Or use TestPyPI for testing before production release

### Upload Fails - Authentication Error

```bash
# Verify ~/.pypirc exists and has correct token
cat ~/.pypirc

# Ensure permissions are restricted
chmod 600 ~/.pypirc

# Regenerate API token if needed
```

### README Doesn't Render on PyPI

**Common causes:**
- Unsupported Markdown syntax
- Missing README.md reference in pyproject.toml
- Invalid RST formatting (if using .rst)

**Fix:**
```bash
# Validate README renders correctly
pip install readme-renderer
python -m readme_renderer README.md
```

### Dependencies Not Installing

Ensure `pyproject.toml` has correct dependencies:
```toml
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
    "pyyaml>=6.0",
]
```

---

## Rollback Procedure

**You cannot delete or replace a PyPI release.** If you need to fix issues:

### Option 1: Yanking (Hide from default pip install)

```bash
# Yank the release (requires PyPI maintainer permissions)
# This hides it from default installs but keeps it available
```

Via PyPI web interface:
1. Go to https://pypi.org/project/todo-cli/1.1.0a1/
2. Click "Options" → "Yank release"
3. Provide reason

### Option 2: Release Patch Version

If critical bugs found:
1. Fix the issues
2. Increment version to 1.1.0a2
3. Follow release process again
4. Announce in release notes that 1.1.0a1 has issues

---

## Version Numbering

For future releases:

- **Alpha:** 1.1.0a1, 1.1.0a2, 1.1.0a3, ...
- **Beta:** 1.1.0b1, 1.1.0b2, 1.1.0b3, ...
- **Release Candidate:** 1.1.0rc1, 1.1.0rc2, ...
- **Stable:** 1.1.0

---

## Checklist Summary

Pre-release:
- [x] Version updated
- [x] CHANGELOG updated
- [x] Tests passing
- [x] Git tagged

Build:
- [ ] Install build tools
- [ ] Build distributions
- [ ] Test locally

TestPyPI (recommended):
- [ ] Upload to TestPyPI
- [ ] Test from TestPyPI
- [ ] Verify functionality

Production:
- [ ] Upload to PyPI
- [ ] Verify PyPI page
- [ ] Test from PyPI

Post-release:
- [ ] Push git changes
- [ ] Create GitHub release
- [ ] Announce release
- [ ] Monitor issues

---

**Estimated Time:** 30-45 minutes (first time), 15-20 minutes (subsequent releases)

**Ready to release?** Follow the steps above in order. Good luck! 🚀
