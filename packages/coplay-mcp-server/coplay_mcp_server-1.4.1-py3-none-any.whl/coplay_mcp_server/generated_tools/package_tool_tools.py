"""Generated MCP tools from package_tool_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def export_package(
    asset_paths: Annotated[
        str,
        Field(
            description="""Comma-separated list of asset paths to include."""
        ),
    ],
    package_name: Annotated[
        str,
        Field(
            description="""Name of the package file."""
        ),
    ],
) -> Any:
    """Exports selected assets as a Unity package."""
    try:
        logger.debug(f"Executing export_package with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_paths is not None:
            params['asset_paths'] = str(asset_paths)
        if package_name is not None:
            params['package_name'] = str(package_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('export_package', params)
        logger.debug(f"export_package completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute export_package: {e}")
        raise RuntimeError(f"Tool execution failed for export_package: {e}")


async def install_unity_package(
    package_name: Annotated[
        str,
        Field(
            description="""The name of the Unity package to install."""
        ),
    ],
    version: Annotated[
        str | None,
        Field(
            description="""Optional version of the package. If not specified, the latest version will be installed."""
        ),
    ] = None,
) -> Any:
    """Installs a Unity package by name and optional version."""
    try:
        logger.debug(f"Executing install_unity_package with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if package_name is not None:
            params['package_name'] = str(package_name)
        if version is not None:
            params['version'] = str(version)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('install_unity_package', params)
        logger.debug(f"install_unity_package completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute install_unity_package: {e}")
        raise RuntimeError(f"Tool execution failed for install_unity_package: {e}")


async def install_git_package(
    repository_url: Annotated[
        str,
        Field(
            description="""The URL of the public Git repository containing the Unity package."""
        ),
    ],
    branch: Annotated[
        str | None,
        Field(
            description="""Optional branch to use. Defaults to the main or master branch."""
        ),
    ] = None,
    package_name: Annotated[
        str | None,
        Field(
            description="""Optional name for the package."""
        ),
    ] = None,
) -> Any:
    """Installs a Unity package from a public Git repository."""
    try:
        logger.debug(f"Executing install_git_package with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if repository_url is not None:
            params['repository_url'] = str(repository_url)
        if branch is not None:
            params['branch'] = str(branch)
        if package_name is not None:
            params['package_name'] = str(package_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('install_git_package', params)
        logger.debug(f"install_git_package completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute install_git_package: {e}")
        raise RuntimeError(f"Tool execution failed for install_git_package: {e}")


async def remove_unity_package(
    package_name: Annotated[
        str,
        Field(
            description="""The name of the Unity package to remove."""
        ),
    ],
) -> Any:
    """Removes a Unity package by its name."""
    try:
        logger.debug(f"Executing remove_unity_package with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if package_name is not None:
            params['package_name'] = str(package_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('remove_unity_package', params)
        logger.debug(f"remove_unity_package completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute remove_unity_package: {e}")
        raise RuntimeError(f"Tool execution failed for remove_unity_package: {e}")


async def list_packages(
) -> Any:
    """Retrieves a list of installed packages in this project."""
    try:
        logger.debug(f"Executing list_packages with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}

        # Execute Unity RPC call
        result = await _unity_client.execute_request('list_packages', params)
        logger.debug(f"list_packages completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute list_packages: {e}")
        raise RuntimeError(f"Tool execution failed for list_packages: {e}")


async def search_installed_packages(
    package_name: Annotated[
        str,
        Field(
            description="""The name of the package to search for."""
        ),
    ],
) -> Any:
    """Searches for installed packages in this project."""
    try:
        logger.debug(f"Executing search_installed_packages with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if package_name is not None:
            params['package_name'] = str(package_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('search_installed_packages', params)
        logger.debug(f"search_installed_packages completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute search_installed_packages: {e}")
        raise RuntimeError(f"Tool execution failed for search_installed_packages: {e}")


async def search_all_packages(
) -> Any:
    """Searches for packages in the Unity registry."""
    try:
        logger.debug(f"Executing search_all_packages with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}

        # Execute Unity RPC call
        result = await _unity_client.execute_request('search_all_packages', params)
        logger.debug(f"search_all_packages completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute search_all_packages: {e}")
        raise RuntimeError(f"Tool execution failed for search_all_packages: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from package_tool_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register export_package
    mcp.tool()(export_package)
    # Register install_unity_package
    mcp.tool()(install_unity_package)
    # Register install_git_package
    mcp.tool()(install_git_package)
    # Register remove_unity_package
    mcp.tool()(remove_unity_package)
    # Register list_packages
    mcp.tool()(list_packages)
    # Register search_installed_packages
    mcp.tool()(search_installed_packages)
    # Register search_all_packages
    mcp.tool()(search_all_packages)
