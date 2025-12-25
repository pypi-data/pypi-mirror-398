# Inoopa's helpers

This repo contains helper functions we use in all of our python projects.

## This is pushed publicly to Pypi, so NEVER commit any secret here

## How to use this package in your code

```bash
pip install inoopa_utils
```

```python
from inoopa_utils.mongodb_helpers import DbManagerMongo

db_manager = DbManagerMongo()
```

## Development Setup

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install development dependencies
uv sync --dev

# Add a new dependency
uv add <package-name>

# Add a new development dependency
uv add --dev <package-name>
```

## How to publish package to Pypi

### Automatic Publishing (Recommended)

The package is automatically published to PyPI when you push changes to `pyproject.toml` on the `main` branch, **but only if the version has been bumped**.

1. Make your code changes
2. **Update the package version** in [pyproject.toml](./pyproject.toml) at the key `version`
3. Commit and push to `main`
4. GitHub Actions will automatically:
   - Verify the version was bumped
   - Build the package
   - Publish to PyPI
   - Create a GitHub release

**Required Setup:**

- Add your PyPI API token as a GitHub secret named `PYPI_API_TOKEN`

### Manual Publishing

If you need to publish manually:

```bash
# Export your PyPI token
export UV_PUBLISH_TOKEN="..."

# Build project
uv build

# Publish (requires PyPI token to be configured)
uv publish
```

Note: You'll need to configure your PyPI credentials. You can either:

- Set the `UV_PUBLISH_TOKEN` environment variable with your PyPI token
- Use `uv publish --username __token__ --password <your-token>`
