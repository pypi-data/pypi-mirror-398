"""Generated MCP tools from scene_view_functions_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def scene_view_functions(
    toggle_2d_mode: Annotated[
        bool | None,
        Field(
            description="""Toggle between 2D and 3D Scene View mode. Set to true for 2D mode, false for 3D mode, or null to leave unchanged."""
        ),
    ] = None,
    toggle_lighting: Annotated[
        bool | None,
        Field(
            description="""Toggle Scene View lighting on/off. When enabled, shows realistic lighting in the Scene View. Set to true to enable, false to disable, or null to leave unchanged."""
        ),
    ] = None,
) -> Any:
    """Control Unity Scene View settings including 2D/3D mode, lighting."""
    try:
        logger.debug(f"Executing scene_view_functions with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if toggle_2d_mode is not None:
            params['toggle_2d_mode'] = str(toggle_2d_mode)
        if toggle_lighting is not None:
            params['toggle_lighting'] = str(toggle_lighting)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('scene_view_functions', params)
        logger.debug(f"scene_view_functions completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute scene_view_functions: {e}")
        raise RuntimeError(f"Tool execution failed for scene_view_functions: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from scene_view_functions_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register scene_view_functions
    mcp.tool()(scene_view_functions)
