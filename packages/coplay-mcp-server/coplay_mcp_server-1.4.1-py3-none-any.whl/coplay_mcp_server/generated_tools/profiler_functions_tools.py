"""Generated MCP tools from profiler_functions_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def get_worst_cpu_frames(
) -> Any:
    """Identifies the worst CPU frames in profiling data, formats their function calls and timings, and returns the result as a string."""
    try:
        logger.debug(f"Executing get_worst_cpu_frames with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}

        # Execute Unity RPC call
        result = await _unity_client.execute_request('get_worst_cpu_frames', params)
        logger.debug(f"get_worst_cpu_frames completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute get_worst_cpu_frames: {e}")
        raise RuntimeError(f"Tool execution failed for get_worst_cpu_frames: {e}")


async def get_worst_gc_frames(
) -> Any:
    """Identifies the worst GC frames in profiling data, formats their function calls and allocation sizes, and returns the result as a string."""
    try:
        logger.debug(f"Executing get_worst_gc_frames with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}

        # Execute Unity RPC call
        result = await _unity_client.execute_request('get_worst_gc_frames', params)
        logger.debug(f"get_worst_gc_frames completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute get_worst_gc_frames: {e}")
        raise RuntimeError(f"Tool execution failed for get_worst_gc_frames: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from profiler_functions_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register get_worst_cpu_frames
    mcp.tool()(get_worst_cpu_frames)
    # Register get_worst_gc_frames
    mcp.tool()(get_worst_gc_frames)
