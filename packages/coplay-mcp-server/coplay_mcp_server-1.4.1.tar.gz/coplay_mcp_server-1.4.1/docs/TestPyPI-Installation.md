# Installing from Test PyPI with Mixed Dependencies

When installing from Test PyPI, you may encounter dependency version mismatches. Here are the recommended approaches:

## Method 1: Mixed Index Installation (Recommended)

Install your package from Test PyPI but allow dependencies to come from main PyPI:

```bash
# Using pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ coplay-mcp-server

# Using uvx
uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ coplay-mcp-server
```

## Method 2: Using uv (Modern Python Package Manager)

If you're using `uv`, you can specify multiple indexes:

```bash
# Add both indexes to uv
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ coplay-mcp-server
```

## Verification

After installation, verify everything works:

```bash
# Test the CLI
coplay-mcp-server --help

# Test Python import
python -c "import coplay_mcp_server; print('Import successful')"

# Check installed version
pip show coplay-mcp-server
