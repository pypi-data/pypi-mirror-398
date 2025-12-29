"""Generated MCP tools from screenshot_tool_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def get_scene_view_screenshot(
    gameObjectPath: Annotated[
        str | None,
        Field(
            description="""Optional path of a game object in the active hierarchy to focus on before taking the screenshot (e.g. '/Root/Parent/Child'). If provided, the scene view will be focused on this object. If empty or null, no focusing will be performed."""
        ),
    ] = None,
    includeUI: Annotated[
        bool | None,
        Field(
            description="""Optional flag to include UI elements (gizmos, handles, overlays) in the screenshot. Defaults to false if not specified. When false, only the camera view is captured without UI elements."""
        ),
    ] = None,
) -> Any:
    """Captures a screenshot of the current Scene view. Use this tool to inspect or analyze the visual appearance of objects after making visual changes to a scene or prefab. Do not use it for validating UI Canvases."""
    try:
        logger.debug(f"Executing get_scene_view_screenshot with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameObjectPath is not None:
            params['gameObjectPath'] = str(gameObjectPath)
        if includeUI is not None:
            params['includeUI'] = str(includeUI)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('get_scene_view_screenshot', params)
        logger.debug(f"get_scene_view_screenshot completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute get_scene_view_screenshot: {e}")
        raise RuntimeError(f"Tool execution failed for get_scene_view_screenshot: {e}")


async def capture_ui_canvas(
    canvasPath: Annotated[
        str | None,
        Field(
            description="""Optional path to the canvas in the scene hierarchy. If provided, the specified Canvas will be captured. If empty or null, the first Canvas found in the scene will be captured."""
        ),
    ] = None,
) -> Any:
    """Captures a screenshot of a UI Canvas. Use this tool to capture and analyze Unity UI Canvases in the Scene hierarchy after generating UI for validation."""
    try:
        logger.debug(f"Executing capture_ui_canvas with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if canvasPath is not None:
            params['canvasPath'] = str(canvasPath)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('capture_ui_canvas', params)
        logger.debug(f"capture_ui_canvas completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute capture_ui_canvas: {e}")
        raise RuntimeError(f"Tool execution failed for capture_ui_canvas: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from screenshot_tool_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register get_scene_view_screenshot
    mcp.tool()(get_scene_view_screenshot)
    # Register capture_ui_canvas
    mcp.tool()(capture_ui_canvas)
