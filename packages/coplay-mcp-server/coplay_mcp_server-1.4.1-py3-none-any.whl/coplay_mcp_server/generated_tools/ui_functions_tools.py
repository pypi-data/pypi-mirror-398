"""Generated MCP tools from ui_functions_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def set_rect_transform(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    anchor_min: Annotated[
        str | None,
        Field(
            description="""Comma-separated anchor minimum values (x,y)."""
        ),
    ] = None,
    anchor_max: Annotated[
        str | None,
        Field(
            description="""Comma-separated anchor maximum values (x,y)."""
        ),
    ] = None,
    pivot: Annotated[
        str | None,
        Field(
            description="""Comma-separated pivot point values (x,y)."""
        ),
    ] = None,
    size_delta: Annotated[
        str | None,
        Field(
            description="""Comma-separated size delta values (width,height)."""
        ),
    ] = None,
    anchored_position: Annotated[
        str | None,
        Field(
            description="""Comma-separated anchored position values (x,y)."""
        ),
    ] = None,
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Sets RectTransform properties of a UI GameObject."""
    try:
        logger.debug(f"Executing set_rect_transform with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if anchor_min is not None:
            params['anchor_min'] = str(anchor_min)
        if anchor_max is not None:
            params['anchor_max'] = str(anchor_max)
        if pivot is not None:
            params['pivot'] = str(pivot)
        if size_delta is not None:
            params['size_delta'] = str(size_delta)
        if anchored_position is not None:
            params['anchored_position'] = str(anchored_position)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('set_rect_transform', params)
        logger.debug(f"set_rect_transform completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute set_rect_transform: {e}")
        raise RuntimeError(f"Tool execution failed for set_rect_transform: {e}")


async def create_ui_element(
    element_type: Annotated[
        Literal['button', 'text', 'image', 'panel', 'inputfield', 'dropdown', 'toggle', 'scrollview'],
        Field(
            description="""Type of UI element to create"""
        ),
    ],
    element_name: Annotated[
        str,
        Field(
            description="""Name for the new UI element"""
        ),
    ],
    parent_path: Annotated[
        str | None,
        Field(
            description="""Path to the parent GameObject e.g Body/Head/Eyes"""
        ),
    ] = None,
) -> Any:
    """Creates a new UI element in the scene and returns scene path where the object was created."""
    try:
        logger.debug(f"Executing create_ui_element with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if element_type is not None:
            params['element_type'] = str(element_type)
        if element_name is not None:
            params['element_name'] = str(element_name)
        if parent_path is not None:
            params['parent_path'] = str(parent_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('create_ui_element', params)
        logger.debug(f"create_ui_element completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute create_ui_element: {e}")
        raise RuntimeError(f"Tool execution failed for create_ui_element: {e}")


async def set_ui_text(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    text: Annotated[
        str | None,
        Field(
            description="""Text content to set"""
        ),
    ] = None,
    font_size: Annotated[
        int | None,
        Field(
            description="""Font size"""
        ),
    ] = None,
    color: Annotated[
        str | None,
        Field(
            description="""Color in r,g,b,a format (0-1 values)"""
        ),
    ] = None,
    alignment: Annotated[
        Literal['left', 'center', 'right'] | None,
        Field(
            description="""Text alignment"""
        ),
    ] = None,
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Sets properties of a UI Text component."""
    try:
        logger.debug(f"Executing set_ui_text with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if text is not None:
            params['text'] = str(text)
        if font_size is not None:
            params['font_size'] = str(font_size)
        if color is not None:
            params['color'] = str(color)
        if alignment is not None:
            params['alignment'] = str(alignment)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('set_ui_text', params)
        logger.debug(f"set_ui_text completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute set_ui_text: {e}")
        raise RuntimeError(f"Tool execution failed for set_ui_text: {e}")


async def set_ui_layout(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    layout_type: Annotated[
        Literal['vertical', 'horizontal', 'grid'],
        Field(
            description="""Type of layout to apply"""
        ),
    ],
    spacing: Annotated[
        str | None,
        Field(
            description="""Spacing between elements (single value for vertical/horizontal, 'x,y' for grid)"""
        ),
    ] = None,
    padding: Annotated[
        str | None,
        Field(
            description="""Padding in 'left,right,top,bottom' format"""
        ),
    ] = None,
    alignment: Annotated[
        Literal['upper_left', 'upper_center', 'upper_right', 'middle_left', 'middle_center', 'middle_right', 'lower_left', 'lower_center', 'lower_right'] | None,
        Field(
            description="""Alignment of children elements"""
        ),
    ] = None,
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Sets layout properties for UI elements."""
    try:
        logger.debug(f"Executing set_ui_layout with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if layout_type is not None:
            params['layout_type'] = str(layout_type)
        if spacing is not None:
            params['spacing'] = str(spacing)
        if padding is not None:
            params['padding'] = str(padding)
        if alignment is not None:
            params['alignment'] = str(alignment)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('set_ui_layout', params)
        logger.debug(f"set_ui_layout completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute set_ui_layout: {e}")
        raise RuntimeError(f"Tool execution failed for set_ui_layout: {e}")


async def add_persistent_listener(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes, containing the component with the event."""
        ),
    ],
    component_type: Annotated[
        str,
        Field(
            description="""Type of component containing the event (e.g., 'Button', 'Toggle')."""
        ),
    ],
    event_name: Annotated[
        str,
        Field(
            description="""Name of the event property (e.g., 'onClick', 'onValueChanged')."""
        ),
    ],
    target_gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or path in a prefab asset, containing the component with the method to call."""
        ),
    ],
    target_component_type: Annotated[
        str,
        Field(
            description="""Type of component containing the method to call."""
        ),
    ],
    method_name: Annotated[
        str,
        Field(
            description="""Name of the method to call when the event is triggered."""
        ),
    ],
    parameter_type: Annotated[
        Literal['_none', '_bool', '_int', '_float', '_string', '_void'],
        Field(
            description="""Type of parameter the method accepts. Defaults to none."""
        ),
    ],
    parameter_value: Annotated[
        str | None,
        Field(
            description="""Value to pass to the method when called. Should match the parameter_type."""
        ),
    ] = None,
) -> Any:
    """Adds a persistent listener to a UnityEvent on a component. This allows configuring event callbacks like Button.onClick events."""
    try:
        logger.debug(f"Executing add_persistent_listener with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if component_type is not None:
            params['component_type'] = str(component_type)
        if event_name is not None:
            params['event_name'] = str(event_name)
        if target_gameobject_path is not None:
            params['target_gameobject_path'] = str(target_gameobject_path)
        if target_component_type is not None:
            params['target_component_type'] = str(target_component_type)
        if method_name is not None:
            params['method_name'] = str(method_name)
        if parameter_type is not None:
            params['parameter_type'] = str(parameter_type)
        if parameter_value is not None:
            params['parameter_value'] = str(parameter_value)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('add_persistent_listener', params)
        logger.debug(f"add_persistent_listener completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute add_persistent_listener: {e}")
        raise RuntimeError(f"Tool execution failed for add_persistent_listener: {e}")


async def remove_persistent_listener(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes, containing the component with the event."""
        ),
    ],
    component_type: Annotated[
        str,
        Field(
            description="""Type of component containing the event (e.g., 'Button', 'Toggle')."""
        ),
    ],
    event_name: Annotated[
        str,
        Field(
            description="""Name of the event property (e.g., 'onClick', 'onValueChanged')."""
        ),
    ],
    listener_index: Annotated[
        int,
        Field(
            description="""Index of the listener to remove (0-based)."""
        ),
    ],
) -> Any:
    """Removes a persistent listener from a UnityEvent on a component."""
    try:
        logger.debug(f"Executing remove_persistent_listener with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if component_type is not None:
            params['component_type'] = str(component_type)
        if event_name is not None:
            params['event_name'] = str(event_name)
        if listener_index is not None:
            params['listener_index'] = str(listener_index)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('remove_persistent_listener', params)
        logger.debug(f"remove_persistent_listener completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute remove_persistent_listener: {e}")
        raise RuntimeError(f"Tool execution failed for remove_persistent_listener: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from ui_functions_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register set_rect_transform
    mcp.tool()(set_rect_transform)
    # Register create_ui_element
    mcp.tool()(create_ui_element)
    # Register set_ui_text
    mcp.tool()(set_ui_text)
    # Register set_ui_layout
    mcp.tool()(set_ui_layout)
    # Register add_persistent_listener
    mcp.tool()(add_persistent_listener)
    # Register remove_persistent_listener
    mcp.tool()(remove_persistent_listener)
