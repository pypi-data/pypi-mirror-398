"""Generated MCP tools from agent_tool_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def get_unity_logs(
    skip_newest_n_logs: Annotated[
        int | None,
        Field(
            description="""Number of the *most recent* log entries to skip before returning results. Default is 0 (start with the newest)."""
        ),
    ] = None,
    limit: Annotated[
        int | None,
        Field(
            description="""The maximum number of log entries to return after applying the offset. Default is 100."""
        ),
    ] = None,
    show_logs: Annotated[
        bool | None,
        Field(
            description="""Include INFO level logs. Defaults to true if not specified."""
        ),
    ] = None,
    show_warnings: Annotated[
        bool | None,
        Field(
            description="""Include WARNING level logs. Defaults to true if not specified."""
        ),
    ] = None,
    show_errors: Annotated[
        bool | None,
        Field(
            description="""Include ERROR and EXCEPTION level logs. Defaults to true if not specified."""
        ),
    ] = None,
    show_stack_traces: Annotated[
        bool | None,
        Field(
            description="""Include stack traces. Defaults to true if not specified."""
        ),
    ] = None,
    search_term: Annotated[
        str | None,
        Field(
            description="""Only include logs containing this text (case-insensitive). Defaults to empty (no search filter)."""
        ),
    ] = None,
) -> Any:
    """Get logs from the Unity Editor console buffer, ordered chronologically (oldest first). Allows filtering by type and content, and pagination based on the most recent logs."""
    try:
        logger.debug(f"Executing get_unity_logs with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if skip_newest_n_logs is not None:
            params['skip_newest_n_logs'] = str(skip_newest_n_logs)
        if limit is not None:
            params['limit'] = str(limit)
        if show_logs is not None:
            params['show_logs'] = str(show_logs)
        if show_warnings is not None:
            params['show_warnings'] = str(show_warnings)
        if show_errors is not None:
            params['show_errors'] = str(show_errors)
        if show_stack_traces is not None:
            params['show_stack_traces'] = str(show_stack_traces)
        if search_term is not None:
            params['search_term'] = str(search_term)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('get_unity_logs', params)
        logger.debug(f"get_unity_logs completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute get_unity_logs: {e}")
        raise RuntimeError(f"Tool execution failed for get_unity_logs: {e}")


async def get_unity_editor_state(
) -> Any:
    """Retrieve the current state of the Unity Editor, excluding scene hierarchy."""
    try:
        logger.debug(f"Executing get_unity_editor_state with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}

        # Execute Unity RPC call
        result = await _unity_client.execute_request('get_unity_editor_state', params)
        logger.debug(f"get_unity_editor_state completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute get_unity_editor_state: {e}")
        raise RuntimeError(f"Tool execution failed for get_unity_editor_state: {e}")


async def list_game_objects_in_hierarchy(
    referenceObjectPath: Annotated[
        str | None,
        Field(
            description="""Optional path of a reference game object to search relative to (e.g. 'Root/Parent/Child'). If specified, the search will be performed relative to this object instead of the entire hierarchy. This is not the file path."""
        ),
    ] = None,
    nameFilter: Annotated[
        str | None,
        Field(
            description="""Optional filter to match game objects by name (case-insensitive substring match)"""
        ),
    ] = None,
    tagFilter: Annotated[
        str | None,
        Field(
            description="""Optional filter to match game objects by tag"""
        ),
    ] = None,
    componentFilter: Annotated[
        str | None,
        Field(
            description="""Optional filter to match game objects by component type (e.g. 'Transform', 'MeshRenderer')"""
        ),
    ] = None,
    includeInactive: Annotated[
        bool | None,
        Field(
            description="""Optional flag to include inactive game objects in the results. Defaults to false if not specified."""
        ),
    ] = None,
    limit: Annotated[
        int | None,
        Field(
            description="""Optional maximum number of objects to return. Defaults to 200 if not specified."""
        ),
    ] = None,
    skip: Annotated[
        int | None,
        Field(
            description="""Optional number of objects to skip (for pagination). Defaults to 0 if not specified."""
        ),
    ] = None,
    onlyPaths: Annotated[
        bool | None,
        Field(
            description="""Optional flag to return only the paths of the game objects. Defaults to true if not specified. If false, the components and children will also be returned."""
        ),
    ] = None,
) -> Any:
    """List game objects in the hierarchy with optional filtering capabilities. Uses breadth-first traversal to prioritize objects closer to the root. Results are truncated if they exceed the limit, with a message indicating the truncation. Only works for the active scene or prefab."""
    try:
        logger.debug(f"Executing list_game_objects_in_hierarchy with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if referenceObjectPath is not None:
            params['referenceObjectPath'] = str(referenceObjectPath)
        if nameFilter is not None:
            params['nameFilter'] = str(nameFilter)
        if tagFilter is not None:
            params['tagFilter'] = str(tagFilter)
        if componentFilter is not None:
            params['componentFilter'] = str(componentFilter)
        if includeInactive is not None:
            params['includeInactive'] = str(includeInactive)
        if limit is not None:
            params['limit'] = str(limit)
        if skip is not None:
            params['skip'] = str(skip)
        if onlyPaths is not None:
            params['onlyPaths'] = str(onlyPaths)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('list_game_objects_in_hierarchy', params)
        logger.debug(f"list_game_objects_in_hierarchy completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute list_game_objects_in_hierarchy: {e}")
        raise RuntimeError(f"Tool execution failed for list_game_objects_in_hierarchy: {e}")


async def execute_script(
    filePath: Annotated[
        str,
        Field(
            description="""The path to the C# file to execute. Can be absolute or relative to the Unity project root."""
        ),
    ],
    methodName: Annotated[
        str | None,
        Field(
            description="""Optional name of the public static method to execute as the entry point. Defaults to 'Execute' if not specified."""
        ),
    ] = None,
    arguments: Annotated[
        str | None,
        Field(
            description="""Optional JSON string containing arguments to pass to the method. Must be a valid JSON object that can be parsed into a JObject."""
        ),
    ] = None,
) -> Any:
    """Executes arbitrary C# code within the Unity Editor environment. The provided code must define a class that includes a public static method, which serves as the entry point for execution. The code can access any classes and APIs available in Unity's editor mode."""
    try:
        logger.debug(f"Executing execute_script with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if filePath is not None:
            params['filePath'] = str(filePath)
        if methodName is not None:
            params['methodName'] = str(methodName)
        if arguments is not None:
            params['arguments'] = str(arguments)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('execute_script', params)
        logger.debug(f"execute_script completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute execute_script: {e}")
        raise RuntimeError(f"Tool execution failed for execute_script: {e}")


async def invoke_mcp_tool(
    mcp_server: Annotated[
        str,
        Field(
            description="""The name of the MCP server to execute the command on."""
        ),
    ],
    tool: Annotated[
        str,
        Field(
            description="""The name of the tool to invoke."""
        ),
    ],
    args: Annotated[
        str,
        Field(
            description="""The arguments to pass to the tool as a JSON encoded string. The json object must match the args schema of the tool."""
        ),
    ],
) -> Any:
    """Invoke a tool on an MCP server. The tool must be valid for the server."""
    try:
        logger.debug(f"Executing invoke_mcp_tool with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if mcp_server is not None:
            params['mcp_server'] = str(mcp_server)
        if tool is not None:
            params['tool'] = str(tool)
        if args is not None:
            params['args'] = str(args)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('invoke_mcp_tool', params)
        logger.debug(f"invoke_mcp_tool completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute invoke_mcp_tool: {e}")
        raise RuntimeError(f"Tool execution failed for invoke_mcp_tool: {e}")


async def get_game_object_info(
    gameObjectPath: Annotated[
        str,
        Field(
            description="""Path of the game object in the hierarchy (e.g. 'Root/Parent/Child')."""
        ),
    ],
    componentFilter: Annotated[
        str | None,
        Field(
            description="""Optional filter for a specific component type in the returned information (e.g. 'Transform', 'MeshRenderer')"""
        ),
    ] = None,
    includeInactive: Annotated[
        bool | None,
        Field(
            description="""Optional flag to include inactive game objects in the results. Defaults to false if not specified."""
        ),
    ] = None,
    prefabPath: Annotated[
        str | None,
        Field(
            description="""Optional path to a prefab asset. If provided, the gameObjectPath will be resolved within this prefab. Required when seeking game object details within a prefab."""
        ),
    ] = None,
) -> Any:
    """Get information about a game object with optional filtering capabilities. Results include the AABB information of the game object. Use this tool to list all the details of a game object."""
    try:
        logger.debug(f"Executing get_game_object_info with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameObjectPath is not None:
            params['gameObjectPath'] = str(gameObjectPath)
        if componentFilter is not None:
            params['componentFilter'] = str(componentFilter)
        if includeInactive is not None:
            params['includeInactive'] = str(includeInactive)
        if prefabPath is not None:
            params['prefabPath'] = str(prefabPath)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('get_game_object_info', params)
        logger.debug(f"get_game_object_info completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute get_game_object_info: {e}")
        raise RuntimeError(f"Tool execution failed for get_game_object_info: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from agent_tool_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register get_unity_logs
    mcp.tool()(get_unity_logs)
    # Register get_unity_editor_state
    mcp.tool()(get_unity_editor_state)
    # Register list_game_objects_in_hierarchy
    mcp.tool()(list_game_objects_in_hierarchy)
    # Register execute_script
    mcp.tool()(execute_script)
    # Register invoke_mcp_tool
    mcp.tool()(invoke_mcp_tool)
    # Register get_game_object_info
    mcp.tool()(get_game_object_info)
