# Quick Reference Guide

## For Users

### Installing the Package

```bash
# Install latest version
pip install skolo-shared

# Install specific version
pip install skolo-shared==0.0.33

# Upgrade to latest version
pip install --upgrade skolo-shared
```

### Using the Package

```python
# Import models
from skolo_shared.models.tenant import Student, Staff, School
from skolo_shared.models.public import User, Permission
from skolo_shared.models.common.enums import PaymentStatusEnum, FileTypeEnum

# Use models in your code
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://...')
Session = sessionmaker(bind=engine)
session = Session()

# Query students
students = session.query(Student).filter_by(school_id=school_id).all()
```

## For Contributors

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/skolo-cloud/skolo-shared.git
cd skolo-shared

# Install in editable mode
pip install -e .

# Make your changes
# ...

# Test locally
python -c "from skolo_shared.models.tenant import Student; print('Success!')"
```

### Contributing Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. **Make your changes**
4. **Commit with meaningful messages**
   ```bash
   git add .
   git commit -m "feat: add new payment model"
   ```
5. **Push to your fork**
   ```bash
   git push origin feature/my-new-feature
   ```
6. **Create a Pull Request** to the `main` branch
   - Use a clear title (it will appear in the changelog)
   - Describe your changes

### After Your PR is Merged

- The version is automatically incremented
- A new tag is created
- The package is published to PyPI
- You can install it with `pip install skolo-shared`

## For Maintainers

### Normal Publishing (Automated)

```bash
# Just merge PRs to main - everything else is automatic!
# The automation will:
# 1. Increment version (patch)
# 2. Update VERSION, pyproject.toml, setup.py
# 3. Create a git tag
# 4. Publish to PyPI
```

### Bumping Minor or Major Version

```bash
# For minor version bump (0.0.x → 0.1.0)
echo "v0.1.0" > VERSION
sed -i 's/version = ".*"/version = "0.1.0"/' pyproject.toml
sed -i 's/version="[^"]*"/version="0.1.0"/' setup.py
git add VERSION pyproject.toml setup.py
git commit -m "chore: bump version to 0.1.0"
git push

# For major version bump (0.x.x → 1.0.0)
echo "v1.0.0" > VERSION
sed -i 's/version = ".*"/version = "1.0.0"/' pyproject.toml
sed -i 's/version="[^"]*"/version="1.0.0"/' setup.py
git add VERSION pyproject.toml setup.py
git commit -m "chore: bump version to 1.0.0 - breaking changes"
git push
```

### Manual Build & Test

```bash
# Build the package locally
pip install build
python -m build

# Check the package
pip install twine
twine check dist/*

# Test installation
pip install dist/skolo_shared-*.whl

# Clean up
rm -rf dist/ build/ *.egg-info
```

### Emergency Manual Publish

```bash
# Only if GitHub Actions is down
pip install build twine
python -m build
twine upload dist/*
# Enter: __token__
# Enter: pypi-your-token-here
```

## Common Tasks

### Check Current Version

```bash
# In repository
cat VERSION

# Installed package
pip show skolo-shared | grep Version
```

### View Changelog

```bash
# In repository
cat CHANGES.md

# Online
# https://github.com/skolo-cloud/skolo-shared/blob/main/CHANGES.md
```

### Check Package on PyPI

- Package page: https://pypi.org/project/skolo-shared/
- All versions: https://pypi.org/project/skolo-shared/#history
- Download statistics: https://pypistats.org/packages/skolo-shared

## Troubleshooting

### Import Error

```python
# ❌ Wrong
from skolo-shared import models

# ✅ Correct
from skolo_shared.models.tenant import Student
```

### Installation with Git (Don't Do This)

```bash
# ❌ Wrong - Insecure, exposes credentials
pip install git+https://username:token@github.com/skolo-cloud/skolo-shared

# ✅ Correct - Use PyPI
pip install skolo-shared
```

### Package Not Found

```bash
# Make sure you're using the correct package name
pip install skolo-shared  # ✅ With hyphen
# not
pip install skolo_shared  # ❌ With underscore
```

## Getting Help

- **Issues**: https://github.com/skolo-cloud/skolo-shared/issues
- **Discussions**: https://github.com/skolo-cloud/skolo-shared/discussions
- **Documentation**: https://github.com/skolo-cloud/skolo-shared/tree/main/docs

## Additional Documentation

- [PyPI Publishing Guide](PYPI_PUBLISHING_GUIDE.md) - Complete setup and troubleshooting
- [Time Zone Guidelines](TIMEZONE_GUIDELINES.md) - Working with datetime fields
- [README](../README.md) - Main documentation
