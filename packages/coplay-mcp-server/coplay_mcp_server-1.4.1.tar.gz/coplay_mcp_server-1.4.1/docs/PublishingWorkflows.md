# MCP Server Publishing Workflows

This directory contains GitHub Actions workflows for publishing the Coplay MCP Server to PyPI and Test PyPI.

## Workflows Overview

### 1. Common Workflow (`publish-mcp-server-common.yml`)
A reusable workflow that contains all the publishing logic. It's configurable via environment variables and can be used by both PyPI and Test PyPI workflows.

### 2. Test PyPI Workflow (`publish-mcp-server-testpypi.yml`)
Publishes the MCP server to Test PyPI for testing purposes. This is safe to run frequently during development.

### 3. Production PyPI Workflow (`publish-mcp-server-pypi.yml`)
Publishes the MCP server to the main PyPI repository. Includes additional safety checks and requires explicit confirmation.

## Required GitHub Secrets

You need to set up the following secrets in your GitHub repository:

### For Test PyPI
- `TEST_PYPI_API_TOKEN`: API token for Test PyPI
  - Go to https://test.pypi.org/manage/account/token/
  - Create a new API token
  - Scope: Entire account (or specific to coplay-mcp-server project)

### For Production PyPI
- `PYPI_API_TOKEN`: API token for main PyPI
  - Go to https://pypi.org/manage/account/token/
  - Create a new API token
  - Scope: Entire account (or specific to coplay-mcp-server project)

## GitHub Environments (Optional but Recommended)

For additional security, you can set up GitHub environments:

1. Go to your repository Settings → Environments
2. Create two environments:
   - `testpypi` - for Test PyPI deployments
   - `pypi` - for production PyPI deployments
3. Configure protection rules (e.g., required reviewers for production)
4. Add the respective secrets to each environment

## How to Use

### Publishing to Test PyPI

1. Go to the "Actions" tab in your GitHub repository
2. Select "Publish MCP Server to Test PyPI"
3. Click "Run workflow"
4. Optionally specify a version override
5. Click "Run workflow" to start the process

### Publishing to Production PyPI

1. Go to the "Actions" tab in your GitHub repository
2. Select "Publish MCP Server to PyPI"
3. Click "Run workflow"
4. **IMPORTANT**: Type "CONFIRM" in the confirmation field
5. Optionally specify a version override
6. Click "Run workflow" to start the process

## Workflow Features

- **Automatic building**: Uses `python -m build` to create wheel and source distributions
- **Package verification**: Runs `twine check` to validate the package
- **Installation testing**: Verifies the package can be installed and imported after publishing
- **Detailed logging**: Provides comprehensive output for debugging
- **Safety checks**: Production workflow requires explicit confirmation
- **Environment support**: Uses GitHub environments for secret management
- **Modern tooling**: Uses `uv` for fast Python package management

## Version Management

The workflows use the version specified in `CoplayMCPServer/coplay_mcp_server/__init__.py`. 

To publish a new version:
1. Update the `__version__` in `CoplayMCPServer/coplay_mcp_server/__init__.py`
2. Commit and push the changes
3. Run the appropriate workflow

## Troubleshooting

### Common Issues

1. **"File already exists" error**: You're trying to upload a version that already exists. Update the version number.

2. **Authentication failed**: Check that your API tokens are correctly set in GitHub secrets.

3. **Package verification failed**: There might be issues with your `pyproject.toml` or package structure.

4. **Installation test failed**: The package was uploaded but can't be installed. This might be due to dependency issues.

### Debug Steps

1. Check the workflow logs for detailed error messages
2. Verify your `pyproject.toml` configuration
3. Test building locally: `cd CoplayMCPServer && python -m build`
4. Test package validation: `twine check dist/*`

## Local Testing

Before using the workflows, you can test the build process locally:

```bash
cd CoplayMCPServer

# Install build dependencies
pip install build twine

# Build the package
python -m build

# Check the package
twine check dist/*

# Test upload to Test PyPI (optional)
twine upload --repository testpypi dist/*
