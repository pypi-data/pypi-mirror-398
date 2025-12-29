"""Generated MCP tools from snapping_functions_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def snap_to_grid(
    gameObjectPath: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    prefabPath: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
    gridSize: Annotated[
        float | None,
        Field(
            description="""Uniform grid size for all axes. Defaults to 1.0 if null."""
        ),
    ] = None,
    gridSizeX: Annotated[
        float | None,
        Field(
            description="""Grid size for the X axis (overrides gridSize if specified)."""
        ),
    ] = None,
    gridSizeY: Annotated[
        float | None,
        Field(
            description="""Grid size for the Y axis (overrides gridSize if specified)."""
        ),
    ] = None,
    gridSizeZ: Annotated[
        float | None,
        Field(
            description="""Grid size for the Z axis (overrides gridSize if specified)."""
        ),
    ] = None,
    snapX: Annotated[
        bool | None,
        Field(
            description="""Whether to snap on the X axis. Defaults to true if not specified."""
        ),
    ] = None,
    snapY: Annotated[
        bool | None,
        Field(
            description="""Whether to snap on the Y axis. Defaults to true if not specified."""
        ),
    ] = None,
    snapZ: Annotated[
        bool | None,
        Field(
            description="""Whether to snap on the Z axis. Defaults to true if not specified."""
        ),
    ] = None,
    gridOrigin: Annotated[
        str | None,
        Field(
            description="""Grid origin point in 'x,y,z' format. Defaults to '0,0,0' if not specified."""
        ),
    ] = None,
) -> Any:
    """Snaps a GameObject to a grid with configurable grid size and axes."""
    try:
        logger.debug(f"Executing snap_to_grid with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameObjectPath is not None:
            params['gameObjectPath'] = str(gameObjectPath)
        if prefabPath is not None:
            params['prefabPath'] = str(prefabPath)
        if gridSize is not None:
            params['gridSize'] = str(gridSize)
        if gridSizeX is not None:
            params['gridSizeX'] = str(gridSizeX)
        if gridSizeY is not None:
            params['gridSizeY'] = str(gridSizeY)
        if gridSizeZ is not None:
            params['gridSizeZ'] = str(gridSizeZ)
        if snapX is not None:
            params['snapX'] = str(snapX)
        if snapY is not None:
            params['snapY'] = str(snapY)
        if snapZ is not None:
            params['snapZ'] = str(snapZ)
        if gridOrigin is not None:
            params['gridOrigin'] = str(gridOrigin)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('snap_to_grid', params)
        logger.debug(f"snap_to_grid completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute snap_to_grid: {e}")
        raise RuntimeError(f"Tool execution failed for snap_to_grid: {e}")


async def snap_to_surface(
    gameObjectPath: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    prefabPath: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
    raycastDirection: Annotated[
        str | None,
        Field(
            description="""Raycast direction. Can be 'Down', 'Up', 'Forward', 'Back', 'Left', 'Right', or custom 'x,y,z' format. Defaults to 'Down'."""
        ),
    ] = None,
    maxDistance: Annotated[
        float | None,
        Field(
            description="""Maximum raycast distance. Defaults to 100 if not specified."""
        ),
    ] = None,
    surfaceOffset: Annotated[
        float | None,
        Field(
            description="""Offset distance from the surface. Defaults to 0 if not specified."""
        ),
    ] = None,
    alignToSurfaceNormal: Annotated[
        bool | None,
        Field(
            description="""Whether to align the object's rotation to the surface normal. Defaults to false if not specified."""
        ),
    ] = None,
    layerMask: Annotated[
        int | None,
        Field(
            description="""Layer mask for raycast filtering. Defaults to -1 (all layers) if not specified."""
        ),
    ] = None,
    targetTag: Annotated[
        str | None,
        Field(
            description="""Optional target tag filter. Only hit objects with this tag."""
        ),
    ] = None,
    raycastOriginOffset: Annotated[
        str | None,
        Field(
            description="""Optional raycast origin offset in 'x,y,z' format."""
        ),
    ] = None,
) -> Any:
    """Snaps a GameObject to the nearest surface using raycasting."""
    try:
        logger.debug(f"Executing snap_to_surface with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameObjectPath is not None:
            params['gameObjectPath'] = str(gameObjectPath)
        if prefabPath is not None:
            params['prefabPath'] = str(prefabPath)
        if raycastDirection is not None:
            params['raycastDirection'] = str(raycastDirection)
        if maxDistance is not None:
            params['maxDistance'] = str(maxDistance)
        if surfaceOffset is not None:
            params['surfaceOffset'] = str(surfaceOffset)
        if alignToSurfaceNormal is not None:
            params['alignToSurfaceNormal'] = str(alignToSurfaceNormal)
        if layerMask is not None:
            params['layerMask'] = str(layerMask)
        if targetTag is not None:
            params['targetTag'] = str(targetTag)
        if raycastOriginOffset is not None:
            params['raycastOriginOffset'] = str(raycastOriginOffset)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('snap_to_surface', params)
        logger.debug(f"snap_to_surface completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute snap_to_surface: {e}")
        raise RuntimeError(f"Tool execution failed for snap_to_surface: {e}")


async def snap_to_vertex(
    gameObjectPath: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    targetObjectPath: Annotated[
        str,
        Field(
            description="""Path to the target GameObject whose vertices to snap to."""
        ),
    ],
    prefabPath: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
    maxDistance: Annotated[
        float | None,
        Field(
            description="""Maximum distance to search for vertices. Defaults to 10 if not specified."""
        ),
    ] = None,
    snapToClosest: Annotated[
        bool | None,
        Field(
            description="""Whether to snap to the closest vertex (true) or first found within range (false). Defaults to true if not specified."""
        ),
    ] = None,
    referencePoint: Annotated[
        str | None,
        Field(
            description="""Reference point on the object to use for distance calculation. Can be 'Center', 'Pivot', or 'x,y,z' offset. Defaults to 'Pivot'."""
        ),
    ] = None,
) -> Any:
    """Snaps a GameObject to the nearest vertex of another GameObject."""
    try:
        logger.debug(f"Executing snap_to_vertex with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameObjectPath is not None:
            params['gameObjectPath'] = str(gameObjectPath)
        if prefabPath is not None:
            params['prefabPath'] = str(prefabPath)
        if targetObjectPath is not None:
            params['targetObjectPath'] = str(targetObjectPath)
        if maxDistance is not None:
            params['maxDistance'] = str(maxDistance)
        if snapToClosest is not None:
            params['snapToClosest'] = str(snapToClosest)
        if referencePoint is not None:
            params['referencePoint'] = str(referencePoint)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('snap_to_vertex', params)
        logger.debug(f"snap_to_vertex completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute snap_to_vertex: {e}")
        raise RuntimeError(f"Tool execution failed for snap_to_vertex: {e}")


async def snap_to_bounds(
    gameObjectPath: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    targetObjectPath: Annotated[
        str,
        Field(
            description="""Path to the target GameObject whose bounds to snap to."""
        ),
    ],
    prefabPath: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
    targetReferenceX: Annotated[
        str | None,
        Field(
            description="""X-axis reference point for the target object. Can be 'minX', 'centerX', 'maxX', or a custom numeric value. Defaults to 'centerX' if not specified."""
        ),
    ] = None,
    targetReferenceY: Annotated[
        str | None,
        Field(
            description="""Y-axis reference point for the target object. Can be 'minY', 'centerY', 'maxY', or a custom numeric value. Defaults to 'centerY' if not specified."""
        ),
    ] = None,
    targetReferenceZ: Annotated[
        str | None,
        Field(
            description="""Z-axis reference point for the target object. Can be 'minZ', 'centerZ', 'maxZ', or a custom numeric value. Defaults to 'centerZ' if not specified."""
        ),
    ] = None,
    sourceReferenceX: Annotated[
        str | None,
        Field(
            description="""X-axis reference point for the source object. Can be 'minX', 'centerX', 'maxX', or a custom numeric value. Defaults to 'centerX' if not specified."""
        ),
    ] = None,
    sourceReferenceY: Annotated[
        str | None,
        Field(
            description="""Y-axis reference point for the source object. Can be 'minY', 'centerY', 'maxY', or a custom numeric value. Defaults to 'centerY' if not specified."""
        ),
    ] = None,
    sourceReferenceZ: Annotated[
        str | None,
        Field(
            description="""Z-axis reference point for the source object. Can be 'minZ', 'centerZ', 'maxZ', or a custom numeric value. Defaults to 'centerZ' if not specified."""
        ),
    ] = None,
    snapX: Annotated[
        bool | None,
        Field(
            description="""Whether to snap on the X axis. Defaults to true if not specified."""
        ),
    ] = None,
    snapY: Annotated[
        bool | None,
        Field(
            description="""Whether to snap on the Y axis. Defaults to true if not specified."""
        ),
    ] = None,
    snapZ: Annotated[
        bool | None,
        Field(
            description="""Whether to snap on the Z axis. Defaults to true if not specified."""
        ),
    ] = None,
    offset: Annotated[
        str | None,
        Field(
            description="""Additional offset to apply after snapping in 'x,y,z' format."""
        ),
    ] = None,
) -> Any:
    """Snaps a GameObject to the bounds of another GameObject with per-axis reference point control for both source and target objects. Useful for aligning objects based on their bounding boxes."""
    try:
        logger.debug(f"Executing snap_to_bounds with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameObjectPath is not None:
            params['gameObjectPath'] = str(gameObjectPath)
        if prefabPath is not None:
            params['prefabPath'] = str(prefabPath)
        if targetObjectPath is not None:
            params['targetObjectPath'] = str(targetObjectPath)
        if targetReferenceX is not None:
            params['targetReferenceX'] = str(targetReferenceX)
        if targetReferenceY is not None:
            params['targetReferenceY'] = str(targetReferenceY)
        if targetReferenceZ is not None:
            params['targetReferenceZ'] = str(targetReferenceZ)
        if sourceReferenceX is not None:
            params['sourceReferenceX'] = str(sourceReferenceX)
        if sourceReferenceY is not None:
            params['sourceReferenceY'] = str(sourceReferenceY)
        if sourceReferenceZ is not None:
            params['sourceReferenceZ'] = str(sourceReferenceZ)
        if snapX is not None:
            params['snapX'] = str(snapX)
        if snapY is not None:
            params['snapY'] = str(snapY)
        if snapZ is not None:
            params['snapZ'] = str(snapZ)
        if offset is not None:
            params['offset'] = str(offset)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('snap_to_bounds', params)
        logger.debug(f"snap_to_bounds completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute snap_to_bounds: {e}")
        raise RuntimeError(f"Tool execution failed for snap_to_bounds: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from snapping_functions_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register snap_to_grid
    mcp.tool()(snap_to_grid)
    # Register snap_to_surface
    mcp.tool()(snap_to_surface)
    # Register snap_to_vertex
    mcp.tool()(snap_to_vertex)
    # Register snap_to_bounds
    mcp.tool()(snap_to_bounds)
