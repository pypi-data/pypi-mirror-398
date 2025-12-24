# LangGraph Runtime Firestore - Release Checklist

This document outlines the steps to prepare and publish a new release.

## Pre-Release Checklist

- [x] All code follows style guidelines (ruff lint passes)
- [x] All tests pass (if applicable)
- [x] Documentation is up to date
- [x] CHANGELOG is updated with latest changes
- [x] Version number is bumped appropriately
- [x] Security scan completed with no vulnerabilities

## Version Bumping

Use the Makefile command to bump the version:

```bash
# For patch version (1.0.0 -> 1.0.1)
make bump-version VERSION_KIND=patch

# For minor version (1.0.0 -> 1.1.0)
make bump-version VERSION_KIND=minor

# For major version (1.0.0 -> 2.0.0)
make bump-version VERSION_KIND=major
```

## Publishing to PyPI

The package is automatically published to PyPI when a new release is created on GitHub:

1. **Create a Git Tag**
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

2. **Create a GitHub Release**
   - Go to the [Releases page](https://github.com/MarcoFurrer/langgraph_runtime_firestore/releases)
   - Click "Draft a new release"
   - Select the tag you just created
   - Add release notes describing the changes
   - Click "Publish release"

3. **Verify Publication**
   - The GitHub Actions workflow will automatically build and publish to PyPI
   - Check the [Actions tab](https://github.com/MarcoFurrer/langgraph_runtime_firestore/actions) for the workflow status
   - Verify the package on [PyPI](https://pypi.org/project/langgraph-runtime-firestore/)

## Manual Publishing (if needed)

If you need to publish manually:

```bash
# Build the distribution
python -m build

# Upload to PyPI (requires PyPI credentials)
python -m twine upload dist/*
```

## Post-Release Tasks

- [ ] Announce the release (social media, forums, etc.)
- [ ] Update dependent projects
- [ ] Monitor for issues or bug reports
- [ ] Update documentation site (if applicable)

## Troubleshooting

### Build Fails
- Ensure all dependencies are installed: `pip install -e ".[dev]"`
- Check that the version number in `__init__.py` is correct
- Verify pyproject.toml is valid

### Upload to PyPI Fails
- Ensure `PYPI_API_TOKEN` secret is set in GitHub repository settings
- Check that the version number doesn't already exist on PyPI
- Verify the distribution files in `dist/` are valid

## Environment Variables for CI/CD

Required GitHub Secrets:
- `PYPI_API_TOKEN`: PyPI API token for publishing packages

## Support

For help with releases, contact the maintainer or open an issue on GitHub.
