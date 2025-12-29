"""Generated MCP tools from input_action_tool_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def create_input_action_asset(
    asset_name: Annotated[
        str,
        Field(
            description="""The name of the new InputActionAsset."""
        ),
    ],
    asset_path: Annotated[
        str,
        Field(
            description="""The folder path where the InputActionAsset should be created. If the folder doesn't exist, it will be created automatically."""
        ),
    ],
    map_name: Annotated[
        str | None,
        Field(
            description="""The name of the new InputActionMap within the InputActionAsset."""
        ),
    ] = None,
    action_name: Annotated[
        str | None,
        Field(
            description="""The name of the new InputAction within the InputActionMap."""
        ),
    ] = None,
    action_type: Annotated[
        Literal['Value', 'Button', 'PassThrough'] | None,
        Field(
            description="""The type of the new InputAction."""
        ),
    ] = None,
) -> Any:
    """Creates a new InputActionAsset in the Unity project."""
    try:
        logger.debug(f"Executing create_input_action_asset with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_name is not None:
            params['asset_name'] = str(asset_name)
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if map_name is not None:
            params['map_name'] = str(map_name)
        if action_name is not None:
            params['action_name'] = str(action_name)
        if action_type is not None:
            params['action_type'] = str(action_type)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('create_input_action_asset', params)
        logger.debug(f"create_input_action_asset completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute create_input_action_asset: {e}")
        raise RuntimeError(f"Tool execution failed for create_input_action_asset: {e}")


async def get_input_action_asset(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
) -> Any:
    """Returns the contents of the input action asset in JSON format"""
    try:
        logger.debug(f"Executing get_input_action_asset with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('get_input_action_asset', params)
        logger.debug(f"get_input_action_asset completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute get_input_action_asset: {e}")
        raise RuntimeError(f"Tool execution failed for get_input_action_asset: {e}")


async def generate_input_action_wrapper_code(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    class_name: Annotated[
        str | None,
        Field(
            description="""Optional. The name of the generated class."""
        ),
    ] = None,
    namespace: Annotated[
        str | None,
        Field(
            description="""Optional. The namespace for the generated code."""
        ),
    ] = None,
) -> Any:
    """Generates C# wrapper code for an input action asset"""
    try:
        logger.debug(f"Executing generate_input_action_wrapper_code with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if class_name is not None:
            params['class_name'] = str(class_name)
        if namespace is not None:
            params['namespace'] = str(namespace)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('generate_input_action_wrapper_code', params)
        logger.debug(f"generate_input_action_wrapper_code completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute generate_input_action_wrapper_code: {e}")
        raise RuntimeError(f"Tool execution failed for generate_input_action_wrapper_code: {e}")


async def add_action_map(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    map_name: Annotated[
        str,
        Field(
            description="""The name of the new action map."""
        ),
    ],
) -> Any:
    """Adds a new action map to an existing input action asset"""
    try:
        logger.debug(f"Executing add_action_map with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if map_name is not None:
            params['map_name'] = str(map_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('add_action_map', params)
        logger.debug(f"add_action_map completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute add_action_map: {e}")
        raise RuntimeError(f"Tool execution failed for add_action_map: {e}")


async def remove_action_map(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    map_name: Annotated[
        str,
        Field(
            description="""The name of the action map to remove."""
        ),
    ],
) -> Any:
    """Removes an action map from an input action asset"""
    try:
        logger.debug(f"Executing remove_action_map with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if map_name is not None:
            params['map_name'] = str(map_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('remove_action_map', params)
        logger.debug(f"remove_action_map completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute remove_action_map: {e}")
        raise RuntimeError(f"Tool execution failed for remove_action_map: {e}")


async def add_action(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    map_name: Annotated[
        str,
        Field(
            description="""The name of the action map."""
        ),
    ],
    action_name: Annotated[
        str,
        Field(
            description="""The name of the new action."""
        ),
    ],
    action_type: Annotated[
        Literal['Value', 'Button', 'PassThrough'] | None,
        Field(
            description="""The type of the new action."""
        ),
    ] = None,
    control_layout: Annotated[
        Literal['Analog', 'Axis', 'Bone', 'Delta', 'Digital', 'Double', 'Dpad', 'Eyes', 'Integer', 'Pose', 'Quaternion', 'Stick', 'Touch', 'Vector2', 'Vector3'] | None,
        Field(
            description="""Optional. The expected control layout for the action."""
        ),
    ] = None,
    binding: Annotated[
        str | None,
        Field(
            description="""Optional. The binding path for the action."""
        ),
    ] = None,
    interactions: Annotated[
        str | None,
        Field(
            description="""Optional. The interactions for the action."""
        ),
    ] = None,
    processors: Annotated[
        str | None,
        Field(
            description="""Optional. The processors for the action."""
        ),
    ] = None,
    groups: Annotated[
        str | None,
        Field(
            description="""Optional. The groups for the action."""
        ),
    ] = None,
) -> Any:
    """Adds a new action to an action map"""
    try:
        logger.debug(f"Executing add_action with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if map_name is not None:
            params['map_name'] = str(map_name)
        if action_name is not None:
            params['action_name'] = str(action_name)
        if action_type is not None:
            params['action_type'] = str(action_type)
        if control_layout is not None:
            params['control_layout'] = str(control_layout)
        if binding is not None:
            params['binding'] = str(binding)
        if interactions is not None:
            params['interactions'] = str(interactions)
        if processors is not None:
            params['processors'] = str(processors)
        if groups is not None:
            params['groups'] = str(groups)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('add_action', params)
        logger.debug(f"add_action completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute add_action: {e}")
        raise RuntimeError(f"Tool execution failed for add_action: {e}")


async def remove_action(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    map_name: Annotated[
        str,
        Field(
            description="""The name of the action map."""
        ),
    ],
    action_name: Annotated[
        str,
        Field(
            description="""The name of the action to remove."""
        ),
    ],
) -> Any:
    """Removes an action from an action map"""
    try:
        logger.debug(f"Executing remove_action with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if map_name is not None:
            params['map_name'] = str(map_name)
        if action_name is not None:
            params['action_name'] = str(action_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('remove_action', params)
        logger.debug(f"remove_action completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute remove_action: {e}")
        raise RuntimeError(f"Tool execution failed for remove_action: {e}")


async def rename_action(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    map_name: Annotated[
        str,
        Field(
            description="""The name of the action map."""
        ),
    ],
    old_action_name: Annotated[
        str,
        Field(
            description="""The current name of the action."""
        ),
    ],
    new_action_name: Annotated[
        str,
        Field(
            description="""The new name for the action."""
        ),
    ],
) -> Any:
    """Renames an action in an action map"""
    try:
        logger.debug(f"Executing rename_action with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if map_name is not None:
            params['map_name'] = str(map_name)
        if old_action_name is not None:
            params['old_action_name'] = str(old_action_name)
        if new_action_name is not None:
            params['new_action_name'] = str(new_action_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('rename_action', params)
        logger.debug(f"rename_action completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute rename_action: {e}")
        raise RuntimeError(f"Tool execution failed for rename_action: {e}")


async def add_control_scheme(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    scheme_name: Annotated[
        str,
        Field(
            description="""The name of the new control scheme."""
        ),
    ],
    required_devices: Annotated[
        str | None,
        Field(
            description="""Comma-separated list of required device types."""
        ),
    ] = None,
    optional_devices: Annotated[
        str | None,
        Field(
            description="""Comma-separated list of optional device types."""
        ),
    ] = None,
) -> Any:
    """Adds a new control scheme to an input action asset"""
    try:
        logger.debug(f"Executing add_control_scheme with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if scheme_name is not None:
            params['scheme_name'] = str(scheme_name)
        if required_devices is not None:
            params['required_devices'] = str(required_devices)
        if optional_devices is not None:
            params['optional_devices'] = str(optional_devices)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('add_control_scheme', params)
        logger.debug(f"add_control_scheme completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute add_control_scheme: {e}")
        raise RuntimeError(f"Tool execution failed for add_control_scheme: {e}")


async def remove_control_scheme(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    scheme_name: Annotated[
        str,
        Field(
            description="""The name of the control scheme to remove."""
        ),
    ],
) -> Any:
    """Removes a control scheme from an input action asset"""
    try:
        logger.debug(f"Executing remove_control_scheme with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if scheme_name is not None:
            params['scheme_name'] = str(scheme_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('remove_control_scheme', params)
        logger.debug(f"remove_control_scheme completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute remove_control_scheme: {e}")
        raise RuntimeError(f"Tool execution failed for remove_control_scheme: {e}")


async def add_bindings(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    map_name: Annotated[
        str,
        Field(
            description="""The name of the action map."""
        ),
    ],
    action_name: Annotated[
        str,
        Field(
            description="""The name of the action."""
        ),
    ],
    bindings: Annotated[
        str,
        Field(
            description="""Comma-separated list of binding paths to add."""
        ),
    ],
    groups: Annotated[
        str | None,
        Field(
            description="""Optional. Semicolon-separated list of control scheme groups this binding belongs to (e.g. 'Keyboard&Mouse;Gamepad'). If not specified, binding will be available in all groups."""
        ),
    ] = None,
    interactions: Annotated[
        str | None,
        Field(
            description="""Optional. The interactions for the binding."""
        ),
    ] = None,
    processors: Annotated[
        str | None,
        Field(
            description="""Optional. The processors for the binding."""
        ),
    ] = None,
) -> Any:
    """Adds new bindings to an action in an input action asset"""
    try:
        logger.debug(f"Executing add_bindings with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if map_name is not None:
            params['map_name'] = str(map_name)
        if action_name is not None:
            params['action_name'] = str(action_name)
        if bindings is not None:
            params['bindings'] = str(bindings)
        if groups is not None:
            params['groups'] = str(groups)
        if interactions is not None:
            params['interactions'] = str(interactions)
        if processors is not None:
            params['processors'] = str(processors)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('add_bindings', params)
        logger.debug(f"add_bindings completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute add_bindings: {e}")
        raise RuntimeError(f"Tool execution failed for add_bindings: {e}")


async def remove_bindings(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    map_name: Annotated[
        str,
        Field(
            description="""The name of the action map."""
        ),
    ],
    action_name: Annotated[
        str,
        Field(
            description="""The name of the action."""
        ),
    ],
    bindings: Annotated[
        str,
        Field(
            description="""Comma-separated list of binding paths to remove."""
        ),
    ],
) -> Any:
    """Removes bindings from an action in an input action asset by modifying the JSON directly"""
    try:
        logger.debug(f"Executing remove_bindings with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if map_name is not None:
            params['map_name'] = str(map_name)
        if action_name is not None:
            params['action_name'] = str(action_name)
        if bindings is not None:
            params['bindings'] = str(bindings)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('remove_bindings', params)
        logger.debug(f"remove_bindings completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute remove_bindings: {e}")
        raise RuntimeError(f"Tool execution failed for remove_bindings: {e}")


async def add_composite_binding(
    asset_path: Annotated[
        str,
        Field(
            description="""The path to the input action asset."""
        ),
    ],
    map_name: Annotated[
        str,
        Field(
            description="""The name of the action map."""
        ),
    ],
    action_name: Annotated[
        str,
        Field(
            description="""The name of the action to add the composite binding to."""
        ),
    ],
    composite_type: Annotated[
        Literal['1DAxis', '2DVector', 'ButtonWithOneModifier', 'ButtonWithTwoModifiers'],
        Field(
            description="""The type of composite binding to create."""
        ),
    ],
    bindings: Annotated[
        str,
        Field(
            description="""JSON array of part bindings for the composite binding. Array items must have 'path' and 'composite_part' properties, and optionally a 'processors' property."""
        ),
    ],
    interactions: Annotated[
        str | None,
        Field(
            description="""Optional. Interactions to add to the composite binding."""
        ),
    ] = None,
    processors: Annotated[
        str | None,
        Field(
            description="""Optional. Processors to add to the composite binding."""
        ),
    ] = None,
) -> Any:
    """Adds a composite binding to an action in an input action asset using Unity's InputSystem API"""
    try:
        logger.debug(f"Executing add_composite_binding with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if map_name is not None:
            params['map_name'] = str(map_name)
        if action_name is not None:
            params['action_name'] = str(action_name)
        if composite_type is not None:
            params['composite_type'] = str(composite_type)
        if bindings is not None:
            params['bindings'] = str(bindings)
        if interactions is not None:
            params['interactions'] = str(interactions)
        if processors is not None:
            params['processors'] = str(processors)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('add_composite_binding', params)
        logger.debug(f"add_composite_binding completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute add_composite_binding: {e}")
        raise RuntimeError(f"Tool execution failed for add_composite_binding: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from input_action_tool_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register create_input_action_asset
    mcp.tool()(create_input_action_asset)
    # Register get_input_action_asset
    mcp.tool()(get_input_action_asset)
    # Register generate_input_action_wrapper_code
    mcp.tool()(generate_input_action_wrapper_code)
    # Register add_action_map
    mcp.tool()(add_action_map)
    # Register remove_action_map
    mcp.tool()(remove_action_map)
    # Register add_action
    mcp.tool()(add_action)
    # Register remove_action
    mcp.tool()(remove_action)
    # Register rename_action
    mcp.tool()(rename_action)
    # Register add_control_scheme
    mcp.tool()(add_control_scheme)
    # Register remove_control_scheme
    mcp.tool()(remove_control_scheme)
    # Register add_bindings
    mcp.tool()(add_bindings)
    # Register remove_bindings
    mcp.tool()(remove_bindings)
    # Register add_composite_binding
    mcp.tool()(add_composite_binding)
