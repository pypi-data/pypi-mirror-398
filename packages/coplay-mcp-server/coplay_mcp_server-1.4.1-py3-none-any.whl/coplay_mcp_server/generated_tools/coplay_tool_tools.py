"""Generated MCP tools from coplay_tool_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def generate_scene(
    description: Annotated[
        str,
        Field(
            description="""A natural language description of the scene to generate. Be specific about objects, their positions, colors, and relationships. Use the original user prompt, or an enhanced version of it."""
        ),
    ],
    num_iterations: Annotated[
        int | None,
        Field(
            description="""Optional. Controls the number of iterations of scene generation. Higher values (e.g., 5) generate larger and more detailed scenes. Default is 2."""
        ),
    ] = None,
) -> Any:
    """Generates a 3D scene in Unity based on a text description using AI. This function is useful for generating game levels, environments, and other 3D scenes."""
    try:
        logger.debug(f"Executing generate_scene with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if description is not None:
            params['description'] = str(description)
        if num_iterations is not None:
            params['num_iterations'] = str(num_iterations)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('generate_scene', params)
        logger.debug(f"generate_scene completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute generate_scene: {e}")
        raise RuntimeError(f"Tool execution failed for generate_scene: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from coplay_tool_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register generate_scene
    mcp.tool()(generate_scene)
