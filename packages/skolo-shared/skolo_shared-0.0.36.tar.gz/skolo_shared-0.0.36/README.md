# skolo-shared

Shared SQLAlchemy models for a school management system. This package contains ORM models designed to be reusable and versioned for use in Python projects.

## Installation

### From PyPI (Recommended - Production)

Install the latest stable version from PyPI:

```bash
pip install skolo-shared
```

Or install a specific version:

```bash
pip install skolo-shared==0.0.35
```

### For Development

For local development, clone the repository and install in editable mode:

```bash
git clone https://github.com/skolo-cloud/skolo-shared.git
cd skolo-shared
pip install -e .
```

## Usage

Import models in your project:

```python
from skolo_shared.models.tenant import Student, Staff
from skolo_shared.models.public import User
from skolo_shared.models.common.enums import PaymentStatusEnum
```

## Features

- 🏫 **Tenant-based Architecture**: Separate models for tenant-specific and public/shared data
- 🕐 **Time Zone Aware**: All DateTime columns are timezone-aware with UTC as default
- 🔒 **Audit Trail**: Built-in audit fields (created_by, updated_by) for tracking changes
- 📦 **Well-structured**: Organized into logical modules (tenant, public, common)

## Documentation

- [Quick Reference Guide](docs/QUICK_REFERENCE.md) - Common tasks and commands
- [PyPI Publishing Guide](docs/PYPI_PUBLISHING_GUIDE.md) - Complete setup and publishing guide
- [Time Zone Guidelines](docs/TIMEZONE_GUIDELINES.md) - Best practices for handling time zones in models

## Time Zone Awareness

All `DateTime` columns in this package are **time zone aware** with **UTC as the default**. When working with datetime values:

- Always use `datetime.now(timezone.utc)` instead of `datetime.now()`
- Convert user input to UTC before storing
- Convert UTC to local time only for display purposes

See [Time Zone Guidelines](docs/TIMEZONE_GUIDELINES.md) for detailed documentation.

## Version Management

This repository uses automated versioning:
- Version numbers follow semantic versioning (MAJOR.MINOR.PATCH)
- On every push to `main`, the version is automatically incremented
- Git tags are automatically created for each version
- Packages are automatically published to PyPI when tags are pushed

## For Maintainers

### Publishing to PyPI

The package is automatically published to PyPI when a version tag is pushed:

1. The versioning workflow automatically creates tags on push to `main`
2. The publish workflow is triggered by the tag and publishes to PyPI
3. Ensure `PYPI_API_TOKEN` secret is configured in GitHub repository settings

**For detailed setup instructions**, see [PyPI Publishing Guide](docs/PYPI_PUBLISHING_GUIDE.md).

### Setting Up PyPI Token

1. Create an account on [PyPI](https://pypi.org/)
2. Generate an API token from your PyPI account settings
3. Add the token as a secret named `PYPI_API_TOKEN` in GitHub repository settings:
   - Go to repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token (starts with `pypi-`)

For complete instructions, see the [PyPI Publishing Guide](docs/PYPI_PUBLISHING_GUIDE.md).

### Manual Publishing (if needed)

If you need to publish manually:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the distribution
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request to `main`
5. The version will be automatically incremented on merge

## Security Note

**Never** include credentials or tokens in installation commands. Always use:

```bash
# ✅ Correct - Secure
pip install skolo-shared==0.0.35

# ❌ Wrong - Insecure
pip install git+https://username:token@github.com/...
```

## License

MIT
