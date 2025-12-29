# Publishing Coplay MCP Server to PyPI

This document provides step-by-step instructions for building and publishing the Coplay MCP Server package to PyPI.

## Prerequisites

Before publishing, ensure you have:

1. **Python 3.11+** installed
2. **Build tools** installed:
   ```bash
   pip install build twine
   ```
3. **PyPI accounts** set up:
   - [Test PyPI account](https://test.pypi.org/account/register/)
   - [PyPI account](https://pypi.org/account/register/)
4. **API tokens** configured (recommended over passwords):
   - [Test PyPI API token](https://test.pypi.org/manage/account/token/)
   - [PyPI API token](https://pypi.org/manage/account/token/)

## Version Management

The package uses dynamic versioning from `coplay_mcp_server/__init__.py`. To release a new version:

1. Update the version in `coplay_mcp_server/__init__.py`:
   ```python
   __version__ = "1.2.0"  # Update this line
   ```

2. The version will automatically be picked up by the build system.

## Building the Package

1. **Clean previous builds** (if any):
   ```bash
   rm -rf dist/ build/ *.egg-info/
   ```

2. **Build the package**:
   ```bash
   python -m build
   ```

   This creates:
   - `dist/coplay_mcp_server-{version}-py3-none-any.whl` (wheel distribution)
   - `dist/coplay_mcp_server-{version}.tar.gz` (source distribution)

3. **Verify the build**:
   ```bash
   python -m twine check dist/*
   ```

   You should see:
   ```
   Checking dist/coplay_mcp_server-{version}-py3-none-any.whl: PASSED
   Checking dist/coplay_mcp_server-{version}.tar.gz: PASSED
   ```

## Publishing to Test PyPI (Recommended First)

Test PyPI is a separate instance of PyPI for testing packages before publishing to the main index.

1. **Configure Test PyPI credentials**:
   
   Create or update `~/.pypirc`:
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-your-test-api-token-here
   ```

2. **Upload to Test PyPI**:
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

3. **Test installation from Test PyPI**:
   
   **Note**: Test PyPI may have outdated dependency versions. Use mixed index installation:
   
   ```bash
   # Install from Test PyPI with dependencies from main PyPI
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ coplay-mcp-server

   # Test the CLI command
   coplay-mcp-server --help
   ```

4. **Test with uvx** (recommended installation method):
   ```bash
   # Use mixed indexes with uvx
   uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ coplay-mcp-server
   ```
   
   **Alternative**: If you encounter dependency issues, see `docs/TestPyPI-Installation.md` for detailed solutions.

## Publishing to PyPI (Production)

Once you've verified the package works correctly on Test PyPI:

1. **Configure PyPI credentials**:
   
   Update `~/.pypirc`:
   ```ini
   [pypi]
   repository = https://upload.pypi.org/legacy/
   username = __token__
   password = pypi-your-production-api-token-here
   ```

2. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

3. **Verify the upload**:
   - Visit https://pypi.org/project/coplay-mcp-server/
   - Check that the version, description, and links are correct

4. **Test installation**:
   ```bash
   # Install from PyPI
   pip install coplay-mcp-server

   # Or with uvx (recommended)
   uvx coplay-mcp-server
   ```

## Alternative: Using Environment Variables

Instead of storing credentials in `~/.pypirc`, you can use environment variables:

```bash
# For Test PyPI
export TWINE_REPOSITORY=testpypi
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-test-api-token-here
python -m twine upload dist/*

# For PyPI
export TWINE_REPOSITORY=pypi
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-production-api-token-here
python -m twine upload dist/*
```

## Complete Publishing Workflow

Here's the complete workflow for publishing a new version:

```bash
# 1. Update version in coplay_mcp_server/__init__.py
# 2. Clean and build
rm -rf dist/ build/ *.egg-info/
python -m build

# 3. Check the build
python -m twine check dist/*

# 4. Upload to Test PyPI first
python -m twine upload --repository testpypi dist/*

# 5. Test installation (use mixed indexes for dependencies)
uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ --index-strategy unsafe-best-match coplay-mcp-server@latest

# 6. If everything works, upload to PyPI
python -m twine upload dist/*

# 7. Test final installation
uvx coplay-mcp-server
```

## Troubleshooting

### Common Issues

1. **"File already exists" error**:
   - You're trying to upload a version that already exists
   - Increment the version number in `__init__.py`

2. **Authentication errors**:
   - Verify your API tokens are correct
   - Ensure tokens have the correct permissions

3. **Build failures**:
   - Check that all required files are present
   - Verify `pyproject.toml` syntax
   - Run `python -m twine check dist/*` for detailed errors

4. **Import errors after installation**:
   - Verify package structure is correct
   - Check that all dependencies are properly declared

### Package Information

- **Package name**: `coplay-mcp-server`
- **Import name**: `coplay_mcp_server`
- **CLI command**: `coplay-mcp-server`
- **Repository**: https://github.com/CoplayDev/coplay-unity-plugin
- **Homepage**: https://coplay.dev/
- **Documentation**: https://docs.coplay.dev/

## Security Notes

- Never commit API tokens to version control
- Use API tokens instead of passwords for better security
- Consider using GitHub Actions for automated publishing
- Regularly rotate your API tokens
