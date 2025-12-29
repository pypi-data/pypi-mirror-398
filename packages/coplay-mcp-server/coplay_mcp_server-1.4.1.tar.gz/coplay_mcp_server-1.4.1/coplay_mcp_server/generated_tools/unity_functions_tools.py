"""Generated MCP tools from unity_functions_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def create_game_object(
    name: Annotated[
        str,
        Field(
            description="""The name of the new GameObject."""
        ),
    ],
    position: Annotated[
        str,
        Field(
            description="""Comma-separated position coordinates (e.g., 'x,y,z')."""
        ),
    ],
    primitive_type: Annotated[
        Literal['Cube', 'Sphere', 'Capsule', 'Cylinder', 'Plane'] | None,
        Field(
            description="""Optional. Type of primitive to create. If not specified, creates an empty GameObject. Keep it empty in 2D mode."""
        ),
    ] = None,
    size: Annotated[
        str | None,
        Field(
            description="""Optional. Comma-separated scale factors (e.g., 'x,y,z')."""
        ),
    ] = None,
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
    use_world_coordinates: Annotated[
        bool | None,
        Field(
            description="""Optional. Whether to use world coordinates (true) or local coordinates (false, default). Defaults to false."""
        ),
    ] = None,
) -> Any:
    """Creates a new GameObject in the Unity scene. If primitive_type is not specified, creates an empty GameObject."""
    try:
        logger.debug(f"Executing create_game_object with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if name is not None:
            params['name'] = str(name)
        if primitive_type is not None:
            params['primitive_type'] = str(primitive_type)
        if position is not None:
            params['position'] = str(position)
        if size is not None:
            params['size'] = str(size)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)
        if use_world_coordinates is not None:
            params['use_world_coordinates'] = str(use_world_coordinates)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('create_game_object', params)
        logger.debug(f"create_game_object completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute create_game_object: {e}")
        raise RuntimeError(f"Tool execution failed for create_game_object: {e}")


async def delete_game_object(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Deletes a GameObject from the Unity scene."""
    try:
        logger.debug(f"Executing delete_game_object with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('delete_game_object', params)
        logger.debug(f"delete_game_object completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute delete_game_object: {e}")
        raise RuntimeError(f"Tool execution failed for delete_game_object: {e}")


async def remove_component(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or path in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    component_type: Annotated[
        str,
        Field(
            description="""Type of component to remove."""
        ),
    ],
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Removes a component from a GameObject in the scene or from a prefab."""
    try:
        logger.debug(f"Executing remove_component with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if component_type is not None:
            params['component_type'] = str(component_type)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('remove_component', params)
        logger.debug(f"remove_component completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute remove_component: {e}")
        raise RuntimeError(f"Tool execution failed for remove_component: {e}")


async def set_transform(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    position: Annotated[
        str | None,
        Field(
            description="""Optional. Comma-separated position coordinates (e.g., 'x,y,z')."""
        ),
    ] = None,
    rotation: Annotated[
        str | None,
        Field(
            description="""Optional. Comma-separated rotation angles (e.g., 'x,y,z')."""
        ),
    ] = None,
    scale: Annotated[
        str | None,
        Field(
            description="""Optional. Comma-separated scale factors (e.g., 'x,y,z')."""
        ),
    ] = None,
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
    use_world_coordinates: Annotated[
        bool | None,
        Field(
            description="""Optional. Whether to use world coordinates (true) or local coordinates (false, default). Defaults to false."""
        ),
    ] = None,
) -> Any:
    """Sets the position, rotation, or scale of a GameObject."""
    try:
        logger.debug(f"Executing set_transform with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if position is not None:
            params['position'] = str(position)
        if rotation is not None:
            params['rotation'] = str(rotation)
        if scale is not None:
            params['scale'] = str(scale)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)
        if use_world_coordinates is not None:
            params['use_world_coordinates'] = str(use_world_coordinates)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('set_transform', params)
        logger.debug(f"set_transform completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute set_transform: {e}")
        raise RuntimeError(f"Tool execution failed for set_transform: {e}")


async def set_property(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    component_type: Annotated[
        str,
        Field(
            description="""Type of the component (e.g., 'Rigidbody')."""
        ),
    ],
    property_name: Annotated[
        str,
        Field(
            description="""Name of the property to set."""
        ),
    ],
    value: Annotated[
        str,
        Field(
            description="""New value for the property. If it's an asset, use the path to the asset from its top level directory e.g. Assets/, Packages/, etc. If it's a gameobject in the hierarchy, use the path to the gameobject from the root of the scene."""
        ),
    ],
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
    asset_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to an asset i.e. files that end in .asset. Example: Assets/MyAsset.asset. Only used when reading/modifying an asset that's not a prefab."""
        ),
    ] = None,
) -> Any:
    """Sets a property of a component on a GameObject."""
    try:
        logger.debug(f"Executing set_property with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if component_type is not None:
            params['component_type'] = str(component_type)
        if property_name is not None:
            params['property_name'] = str(property_name)
        if value is not None:
            params['value'] = str(value)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)
        if asset_path is not None:
            params['asset_path'] = str(asset_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('set_property', params)
        logger.debug(f"set_property completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute set_property: {e}")
        raise RuntimeError(f"Tool execution failed for set_property: {e}")


async def save_scene(
    scene_name: Annotated[
        str,
        Field(
            description="""Name for the saved scene."""
        ),
    ],
) -> Any:
    """Saves the current scene."""
    try:
        logger.debug(f"Executing save_scene with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if scene_name is not None:
            params['scene_name'] = str(scene_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('save_scene', params)
        logger.debug(f"save_scene completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute save_scene: {e}")
        raise RuntimeError(f"Tool execution failed for save_scene: {e}")


async def create_material(
    material_name: Annotated[
        str,
        Field(
            description="""Name of the new material."""
        ),
    ],
    color: Annotated[
        str,
        Field(
            description="""Comma-separated color components (e.g., 'r,g,b,a'). Minimum 0, maximum 1."""
        ),
    ],
    material_path: Annotated[
        str,
        Field(
            description="""The folder path where the material should be created. If the folder doesn't exist, it will be created automatically."""
        ),
    ],
    texture_path: Annotated[
        str | None,
        Field(
            description="""The path to a texture file to be applied to the material."""
        ),
    ] = None,
) -> Any:
    """Creates a new material asset."""
    try:
        logger.debug(f"Executing create_material with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if material_name is not None:
            params['material_name'] = str(material_name)
        if color is not None:
            params['color'] = str(color)
        if material_path is not None:
            params['material_path'] = str(material_path)
        if texture_path is not None:
            params['texture_path'] = str(texture_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('create_material', params)
        logger.debug(f"create_material completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute create_material: {e}")
        raise RuntimeError(f"Tool execution failed for create_material: {e}")


async def assign_material(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    material_name: Annotated[
        str,
        Field(
            description="""Name of the material to assign."""
        ),
    ],
    material_path: Annotated[
        str | None,
        Field(
            description="""The folder path where the material is located."""
        ),
    ] = None,
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Assigns a material to a GameObject or a nested object within a Prefab."""
    try:
        logger.debug(f"Executing assign_material with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if material_name is not None:
            params['material_name'] = str(material_name)
        if material_path is not None:
            params['material_path'] = str(material_path)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('assign_material', params)
        logger.debug(f"assign_material completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute assign_material: {e}")
        raise RuntimeError(f"Tool execution failed for assign_material: {e}")


async def assign_material_to_fbx(
    fbx_path: Annotated[
        str,
        Field(
            description="""Path to the FBX file within the Assets folder (e.g., 'Assets/Models/MyModel.fbx')."""
        ),
    ],
    material_path: Annotated[
        str,
        Field(
            description="""Path to the material within the Assets folder (e.g., 'Assets/Materials/MyMaterial.mat')."""
        ),
    ],
    submesh_index: Annotated[
        str | int | None,
        Field(
            description="""Optional. Index of the submesh to apply the material to. Defaults to 0."""
        ),
    ] = None,
) -> Any:
    """Assigns a material to an FBX model in the project (without requiring it to be in the scene)."""
    try:
        logger.debug(f"Executing assign_material_to_fbx with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if fbx_path is not None:
            params['fbx_path'] = str(fbx_path)
        if material_path is not None:
            params['material_path'] = str(material_path)
        if submesh_index is not None:
            params['submesh_index'] = str(submesh_index)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('assign_material_to_fbx', params)
        logger.debug(f"assign_material_to_fbx completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute assign_material_to_fbx: {e}")
        raise RuntimeError(f"Tool execution failed for assign_material_to_fbx: {e}")


async def add_component(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or path in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    component_type: Annotated[
        str,
        Field(
            description="""Type of component to add (e.g., 'Rigidbody', 'BoxCollider')."""
        ),
    ],
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Adds a component to a GameObject, Prefab, or nested object within a Prefab."""
    try:
        logger.debug(f"Executing add_component with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if component_type is not None:
            params['component_type'] = str(component_type)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('add_component', params)
        logger.debug(f"add_component completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute add_component: {e}")
        raise RuntimeError(f"Tool execution failed for add_component: {e}")


async def duplicate_game_object(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
    new_name: Annotated[
        str | None,
        Field(
            description="""Optional. Name for the duplicated GameObject."""
        ),
    ] = None,
) -> Any:
    """Duplicates a GameObject."""
    try:
        logger.debug(f"Executing duplicate_game_object with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)
        if new_name is not None:
            params['new_name'] = str(new_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('duplicate_game_object', params)
        logger.debug(f"duplicate_game_object completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute duplicate_game_object: {e}")
        raise RuntimeError(f"Tool execution failed for duplicate_game_object: {e}")


async def parent_game_object(
    child_path: Annotated[
        str,
        Field(
            description="""Path to the child GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    parent_path: Annotated[
        str,
        Field(
            description="""Path to the parent GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Sets the parent of a GameObject."""
    try:
        logger.debug(f"Executing parent_game_object with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if child_path is not None:
            params['child_path'] = str(child_path)
        if parent_path is not None:
            params['parent_path'] = str(parent_path)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('parent_game_object', params)
        logger.debug(f"parent_game_object completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute parent_game_object: {e}")
        raise RuntimeError(f"Tool execution failed for parent_game_object: {e}")


async def rename_game_object(
    current_path: Annotated[
        str,
        Field(
            description="""Current path of the GameObject."""
        ),
    ],
    new_name: Annotated[
        str,
        Field(
            description="""New name for the GameObject."""
        ),
    ],
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Renames an existing GameObject."""
    try:
        logger.debug(f"Executing rename_game_object with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if current_path is not None:
            params['current_path'] = str(current_path)
        if new_name is not None:
            params['new_name'] = str(new_name)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('rename_game_object', params)
        logger.debug(f"rename_game_object completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute rename_game_object: {e}")
        raise RuntimeError(f"Tool execution failed for rename_game_object: {e}")


async def set_tag(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    tag_name: Annotated[
        str,
        Field(
            description="""The tag to assign to the GameObject."""
        ),
    ],
    create_if_not_exists: Annotated[
        bool | None,
        Field(
            description="""If true, creates the tag if it doesn't exist. Defaults to true."""
        ),
    ] = None,
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Sets the tag of a GameObject. Can create the tag if it doesn't exist."""
    try:
        logger.debug(f"Executing set_tag with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if tag_name is not None:
            params['tag_name'] = str(tag_name)
        if create_if_not_exists is not None:
            params['create_if_not_exists'] = str(create_if_not_exists)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('set_tag', params)
        logger.debug(f"set_tag completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute set_tag: {e}")
        raise RuntimeError(f"Tool execution failed for set_tag: {e}")


async def set_layer(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    layer: Annotated[
        str | int,
        Field(
            description="""Name or index of the layer to assign."""
        ),
    ],
    create_if_not_exists: Annotated[
        bool | None,
        Field(
            description="""If true, creates the layer if it doesn't exist (only for string layer names). Defaults to true."""
        ),
    ] = None,
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Sets the layer of a GameObject. Can create the layer if it doesn't exist."""
    try:
        logger.debug(f"Executing set_layer with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if layer is not None:
            params['layer'] = str(layer)
        if create_if_not_exists is not None:
            params['create_if_not_exists'] = str(create_if_not_exists)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('set_layer', params)
        logger.debug(f"set_layer completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute set_layer: {e}")
        raise RuntimeError(f"Tool execution failed for set_layer: {e}")


async def generate_3d_model_texture(
    object_prompt: Annotated[
        str,
        Field(
            description="""Describe what kind of object the 3D model is."""
        ),
    ],
    provider: Annotated[
        Literal['meshy'],
        Field(
            description="""The provider to use for generating the texture. Currently only Meshy is supported."""
        ),
    ],
    style_prompt: Annotated[
        str,
        Field(
            description="""Describe your desired style of the object."""
        ),
    ],
    output_path: Annotated[
        str,
        Field(
            description="""The file path where the generated image will be saved."""
        ),
    ],
    model_path: Annotated[
        str,
        Field(
            description="""Path to the 3D model for which the texture will be generated. This should be a .fbx or .glb file path. I.e. the path of where the model is currently located in the project. This model will be uploaded and used to help guide the texture generation."""
        ),
    ],
    quality: Annotated[
        Literal['standard', 'high'] | None,
        Field(
            description="""The quality of the generated image. Defaults to standard."""
        ),
    ] = None,
    size: Annotated[
        Literal['1024x1024', '1792x1024', '1024x1792'] | None,
        Field(
            description="""The size of the generated image. Defaults to 1024x1024."""
        ),
    ] = None,
    style: Annotated[
        Literal['natural', 'vivid'] | None,
        Field(
            description="""The style of the generated image. Defaults to natural."""
        ),
    ] = None,
    resolution: Annotated[
        Literal['1024', '2048', '4096'] | None,
        Field(
            description="""The texture resolution (Meshy-specific). Defaults to 1024."""
        ),
    ] = None,
    art_style: Annotated[
        Literal['realistic', 'japanese_anime', 'cartoon', 'hand_drawn'] | None,
        Field(
            description="""The artistic style for the texture (Meshy-specific). Defaults to realistic."""
        ),
    ] = None,
) -> Any:
    """Generates a texture image based on a text prompt and saves it to a specified path. Before calling this function, ensure that you know where the existing model is located in the project and use it for the model_path parameter."""
    try:
        logger.debug(f"Executing generate_3d_model_texture with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if object_prompt is not None:
            params['object_prompt'] = str(object_prompt)
        if provider is not None:
            params['provider'] = str(provider)
        if style_prompt is not None:
            params['style_prompt'] = str(style_prompt)
        if output_path is not None:
            params['output_path'] = str(output_path)
        if model_path is not None:
            params['model_path'] = str(model_path)
        if quality is not None:
            params['quality'] = str(quality)
        if size is not None:
            params['size'] = str(size)
        if style is not None:
            params['style'] = str(style)
        if resolution is not None:
            params['resolution'] = str(resolution)
        if art_style is not None:
            params['art_style'] = str(art_style)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('generate_3d_model_texture', params)
        logger.debug(f"generate_3d_model_texture completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute generate_3d_model_texture: {e}")
        raise RuntimeError(f"Tool execution failed for generate_3d_model_texture: {e}")


async def create_prefab(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene to turn into a prefab. e.g Body/Head/Eyes"""
        ),
    ],
    prefab_name: Annotated[
        str,
        Field(
            description="""Name for the new prefab file (without extension)."""
        ),
    ],
    prefab_path: Annotated[
        str,
        Field(
            description="""The folder path where the prefab should be saved. If the folder doesn't exist, it will be created automatically."""
        ),
    ],
) -> Any:
    """Creates a prefab from an existing GameObject in the active scene or heirarchy."""
    try:
        logger.debug(f"Executing create_prefab with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if prefab_name is not None:
            params['prefab_name'] = str(prefab_name)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('create_prefab', params)
        logger.debug(f"create_prefab completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute create_prefab: {e}")
        raise RuntimeError(f"Tool execution failed for create_prefab: {e}")


async def assign_shader_to_material(
    material_path: Annotated[
        str,
        Field(
            description="""Path to the material file (e.g. 'Assets/Materials/MyMaterial.mat')."""
        ),
    ],
    shader_path: Annotated[
        str,
        Field(
            description="""Path to the shader file (e.g. 'Assets/Shaders/MyShader.shader')."""
        ),
    ],
) -> Any:
    """Assigns a shader to a material."""
    try:
        logger.debug(f"Executing assign_shader_to_material with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if material_path is not None:
            params['material_path'] = str(material_path)
        if shader_path is not None:
            params['shader_path'] = str(shader_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('assign_shader_to_material', params)
        logger.debug(f"assign_shader_to_material completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute assign_shader_to_material: {e}")
        raise RuntimeError(f"Tool execution failed for assign_shader_to_material: {e}")


async def create_prefab_variant(
    base_prefab_path: Annotated[
        str,
        Field(
            description="""The path to the base prefab asset."""
        ),
    ],
    variant_prefab_name: Annotated[
        str,
        Field(
            description="""Name for the new prefab variant file (without extension)."""
        ),
    ],
    variant_prefab_path: Annotated[
        str,
        Field(
            description="""The folder path where the prefab variant should be saved. If the folder doesn't exist, it will be created automatically."""
        ),
    ],
) -> Any:
    """Creates a variant of an existing prefab asset in the assets folder."""
    try:
        logger.debug(f"Executing create_prefab_variant with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if base_prefab_path is not None:
            params['base_prefab_path'] = str(base_prefab_path)
        if variant_prefab_name is not None:
            params['variant_prefab_name'] = str(variant_prefab_name)
        if variant_prefab_path is not None:
            params['variant_prefab_path'] = str(variant_prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('create_prefab_variant', params)
        logger.debug(f"create_prefab_variant completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute create_prefab_variant: {e}")
        raise RuntimeError(f"Tool execution failed for create_prefab_variant: {e}")


async def duplicate_asset(
    original_asset_path: Annotated[
        str,
        Field(
            description="""The path to the original asset."""
        ),
    ],
    new_asset_name: Annotated[
        str,
        Field(
            description="""Name for the duplicated asset file (without extension)."""
        ),
    ],
    destination_path: Annotated[
        str,
        Field(
            description="""The folder path where the new asset should be saved. If the folder doesn't exist, it will be created automatically."""
        ),
    ],
) -> Any:
    """Duplicates an asset in the assets folder."""
    try:
        logger.debug(f"Executing duplicate_asset with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if original_asset_path is not None:
            params['original_asset_path'] = str(original_asset_path)
        if new_asset_name is not None:
            params['new_asset_name'] = str(new_asset_name)
        if destination_path is not None:
            params['destination_path'] = str(destination_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('duplicate_asset', params)
        logger.debug(f"duplicate_asset completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute duplicate_asset: {e}")
        raise RuntimeError(f"Tool execution failed for duplicate_asset: {e}")


async def rename_asset(
    current_asset_path: Annotated[
        str,
        Field(
            description="""The current path to the asset (including file name and extension) within the Assets folder."""
        ),
    ],
    new_asset_name: Annotated[
        str,
        Field(
            description="""The new name for the asset (including extension if applicable)."""
        ),
    ],
) -> Any:
    """Renames an asset in the Unity Assets folder."""
    try:
        logger.debug(f"Executing rename_asset with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if current_asset_path is not None:
            params['current_asset_path'] = str(current_asset_path)
        if new_asset_name is not None:
            params['new_asset_name'] = str(new_asset_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('rename_asset', params)
        logger.debug(f"rename_asset completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute rename_asset: {e}")
        raise RuntimeError(f"Tool execution failed for rename_asset: {e}")


async def check_compile_errors(
) -> Any:
    """Checks if there are compile errors in Unity project."""
    try:
        logger.debug(f"Executing check_compile_errors with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}

        # Execute Unity RPC call
        result = await _unity_client.execute_request('check_compile_errors', params)
        logger.debug(f"check_compile_errors completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute check_compile_errors: {e}")
        raise RuntimeError(f"Tool execution failed for check_compile_errors: {e}")


async def add_nested_object_to_prefab(
    prefab_path: Annotated[
        str,
        Field(
            description="""Path to the target prefab that will contain the nested object."""
        ),
    ],
    object_path: Annotated[
        str,
        Field(
            description="""Path to the object (e.g., FBX) that will be nested."""
        ),
    ],
    nested_name: Annotated[
        str | None,
        Field(
            description="""Optional new name for the nested object instance."""
        ),
    ] = None,
) -> Any:
    """Adds an object from the Assets folder as a nested object inside an existing prefab."""
    try:
        logger.debug(f"Executing add_nested_object_to_prefab with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)
        if object_path is not None:
            params['object_path'] = str(object_path)
        if nested_name is not None:
            params['nested_name'] = str(nested_name)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('add_nested_object_to_prefab', params)
        logger.debug(f"add_nested_object_to_prefab completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute add_nested_object_to_prefab: {e}")
        raise RuntimeError(f"Tool execution failed for add_nested_object_to_prefab: {e}")


async def create_scene(
    scene_name: Annotated[
        str,
        Field(
            description="""Name of the new scene (with or without .unity extension)."""
        ),
    ],
    scene_path: Annotated[
        str | None,
        Field(
            description="""The folder path where the scene should be created. If the folder doesn't exist, it will be created automatically. Defaults to 'Assets/Scenes'."""
        ),
    ] = None,
    add_to_editor: Annotated[
        bool | None,
        Field(
            description="""Whether to add the scene to the build settings. Defaults to true."""
        ),
    ] = None,
) -> Any:
    """Creates a new Unity scene and optionally adds it to the build settings."""
    try:
        logger.debug(f"Executing create_scene with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if scene_name is not None:
            params['scene_name'] = str(scene_name)
        if scene_path is not None:
            params['scene_path'] = str(scene_path)
        if add_to_editor is not None:
            params['add_to_editor'] = str(add_to_editor)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('create_scene', params)
        logger.debug(f"create_scene completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute create_scene: {e}")
        raise RuntimeError(f"Tool execution failed for create_scene: {e}")


async def generate_3d_model_from_image(
    image_url: Annotated[
        str,
        Field(
            description="""URL of the input image to generate the 3D model from."""
        ),
    ],
    output_path: Annotated[
        str,
        Field(
            description="""The file path where the generated model will be saved. The file extension should be .glb."""
        ),
    ],
    provider: Annotated[
        Literal['Meshy4', 'Meshy5', 'Hunyuan3D21'] | None,
        Field(
            description="""Optional. The AI provider to use for 3D model generation. Options: 'Meshy4' (uses Meshy 4.0 model), 'Meshy5' (uses Meshy 5.0 model), 'Hunyuan3D21' (uses Hunyuan 3D 2.1 model). Defaults to 'Meshy5'."""
        ),
    ] = None,
    provider_options: Annotated[
        str | None,
        Field(
            description="""Optional. JSON string containing provider-specific options. For FAL provider: {"textured_mesh": "true/false", "seed": "12345", "num_inference_steps": "50", "guidance_scale": "7.5", "octree_resolution": "256"}. For Meshy provider (image-to-3D): {"ai_model": "meshy-4/meshy-5", "topology": "triangle/quad", "target_polycount": "50000", "symmetry_mode": "auto/x/y/z", "should_remesh": "true/false", "should_texture": "true/false", "enable_pbr": "true/false", "texture_prompt": "realistic wood texture", "texture_image_url": "url", "moderation": "true/false"}."""
        ),
    ] = None,
) -> Any:
    """Generates a 3D model from an input image using various AI providers. Supports multiple providers with different capabilities and options."""
    try:
        logger.debug(f"Executing generate_3d_model_from_image with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if image_url is not None:
            params['image_url'] = str(image_url)
        if output_path is not None:
            params['output_path'] = str(output_path)
        if provider is not None:
            params['provider'] = str(provider)
        if provider_options is not None:
            params['provider_options'] = str(provider_options)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('generate_3d_model_from_image', params)
        logger.debug(f"generate_3d_model_from_image completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute generate_3d_model_from_image: {e}")
        raise RuntimeError(f"Tool execution failed for generate_3d_model_from_image: {e}")


async def generate_3d_model_from_text(
    prompt: Annotated[
        str,
        Field(
            description="""The text prompt to generate the 3D model from."""
        ),
    ],
    output_path: Annotated[
        str,
        Field(
            description="""The file path where the generated model will be saved. The file extension should be .glb."""
        ),
    ],
    provider_options: Annotated[
        str | None,
        Field(
            description="""Optional. JSON string containing provider-specific options. For Meshy provider (text-to-3D): {"art_style": "realistic/sculpture/pbr", "negative_prompt": "low quality, low resolution", "enable_refinement": "true/false"}. Note: Text-to-3D uses Meshy provider by default."""
        ),
    ] = None,
) -> Any:
    """Generates a 3D model from a text prompt using various AI providers. Supports multiple providers with different capabilities and options for text-to-3D generation."""
    try:
        logger.debug(f"Executing generate_3d_model_from_text with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if prompt is not None:
            params['prompt'] = str(prompt)
        if output_path is not None:
            params['output_path'] = str(output_path)
        if provider_options is not None:
            params['provider_options'] = str(provider_options)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('generate_3d_model_from_text', params)
        logger.debug(f"generate_3d_model_from_text completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute generate_3d_model_from_text: {e}")
        raise RuntimeError(f"Tool execution failed for generate_3d_model_from_text: {e}")


async def add_asset_to_scene(
    asset_path: Annotated[
        str,
        Field(
            description="""Path to the asset within the Assets folder (e.g., 'Models/Chair.fbx' or 'Prefabs/Player.prefab')."""
        ),
    ],
    instance_name: Annotated[
        str | None,
        Field(
            description="""Optional name for the instantiated object in the scene. If not provided, uses the asset's name."""
        ),
    ] = None,
    position: Annotated[
        str | None,
        Field(
            description="""Optional comma-separated position coordinates (e.g., 'x,y,z'). Defaults to '0,0,0'."""
        ),
    ] = None,
) -> Any:
    """Adds an existing asset from the Assets folder into the current scene."""
    try:
        logger.debug(f"Executing add_asset_to_scene with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if instance_name is not None:
            params['instance_name'] = str(instance_name)
        if position is not None:
            params['position'] = str(position)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('add_asset_to_scene', params)
        logger.debug(f"add_asset_to_scene completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute add_asset_to_scene: {e}")
        raise RuntimeError(f"Tool execution failed for add_asset_to_scene: {e}")


async def open_scene(
    scene_path: Annotated[
        str,
        Field(
            description="""Path to the scene file within the Assets folder (e.g., 'Scenes/MainMenu.unity'). The '.unity' extension is optional."""
        ),
    ],
) -> Any:
    """Opens a scene from the Assets folder."""
    try:
        logger.debug(f"Executing open_scene with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if scene_path is not None:
            params['scene_path'] = str(scene_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('open_scene', params)
        logger.debug(f"open_scene completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute open_scene: {e}")
        raise RuntimeError(f"Tool execution failed for open_scene: {e}")


async def set_sibling_index(
    gameobject_path: Annotated[
        str,
        Field(
            description="""Path to the GameObject in the scene or in a prefab asset. e.g Body/Head/Eyes"""
        ),
    ],
    index: Annotated[
        int,
        Field(
            description="""Index to set"""
        ),
    ],
    prefab_path: Annotated[
        str | None,
        Field(
            description="""Optional. Filesystem path to a prefab asset i.e. files that end in .prefab. Example: Assets/MyPrefab.prefab. Only used when reading/modifying a prefab."""
        ),
    ] = None,
) -> Any:
    """Sets the sibling index.

Use this to change the sibling index of the GameObject. If a GameObject shares a parent with other GameObjects and are on the same level (i.e. they share the same direct parent), these GameObjects are known as siblings. The sibling index shows where each GameObject sits in this sibling hierarchy.

Use SetSiblingIndex to change the GameObject's place in this hierarchy. When the sibling index of a GameObject is changed, its order in the Hierarchy window will also change. This is useful if you are intentionally ordering the children of a GameObject such as when using Layout Group components."""
    try:
        logger.debug(f"Executing set_sibling_index with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameobject_path is not None:
            params['gameobject_path'] = str(gameobject_path)
        if index is not None:
            params['index'] = str(index)
        if prefab_path is not None:
            params['prefab_path'] = str(prefab_path)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('set_sibling_index', params)
        logger.debug(f"set_sibling_index completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute set_sibling_index: {e}")
        raise RuntimeError(f"Tool execution failed for set_sibling_index: {e}")


async def create_terrain(
    name: Annotated[
        str,
        Field(
            description="""The name of the new terrain GameObject."""
        ),
    ],
    width: Annotated[
        str | None,
        Field(
            description="""Width of the terrain in world units. Default is 500."""
        ),
    ] = None,
    length: Annotated[
        str | None,
        Field(
            description="""Length of the terrain in world units. Default is 500."""
        ),
    ] = None,
    height: Annotated[
        str | None,
        Field(
            description="""Maximum height of the terrain in world units. Default is 600."""
        ),
    ] = None,
    resolution: Annotated[
        str | None,
        Field(
            description="""Resolution of the terrain's heightmap. Must be 2^n + 1 (e.g., 33, 65, 129, 257, 513). Default is 129."""
        ),
    ] = None,
    position: Annotated[
        str | None,
        Field(
            description="""Optional. Comma-separated position coordinates (e.g., 'x,y,z')."""
        ),
    ] = None,
) -> Any:
    """Creates a new terrain in the Unity scene with specified dimensions and resolution."""
    try:
        logger.debug(f"Executing create_terrain with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if name is not None:
            params['name'] = str(name)
        if width is not None:
            params['width'] = str(width)
        if length is not None:
            params['length'] = str(length)
        if height is not None:
            params['height'] = str(height)
        if resolution is not None:
            params['resolution'] = str(resolution)
        if position is not None:
            params['position'] = str(position)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('create_terrain', params)
        logger.debug(f"create_terrain completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute create_terrain: {e}")
        raise RuntimeError(f"Tool execution failed for create_terrain: {e}")


async def list_objects_with_high_polygon_count(
    threshold: Annotated[
        int | None,
        Field(
            description="""The minimum polygon count threshold to consider an object as having high polygon count. Defaults to 1000."""
        ),
    ] = None,
    max_results: Annotated[
        int | None,
        Field(
            description="""Maximum number of results to return. Defaults to 100."""
        ),
    ] = None,
    include_inactive: Annotated[
        bool | None,
        Field(
            description="""Whether to include inactive GameObjects in the results. Defaults to false."""
        ),
    ] = None,
) -> Any:
    """Lists GameObjects in the active scene that have a high polygon count and select them in editor, useful for performance optimization."""
    try:
        logger.debug(f"Executing list_objects_with_high_polygon_count with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if threshold is not None:
            params['threshold'] = str(threshold)
        if max_results is not None:
            params['max_results'] = str(max_results)
        if include_inactive is not None:
            params['include_inactive'] = str(include_inactive)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('list_objects_with_high_polygon_count', params)
        logger.debug(f"list_objects_with_high_polygon_count completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute list_objects_with_high_polygon_count: {e}")
        raise RuntimeError(f"Tool execution failed for list_objects_with_high_polygon_count: {e}")


async def play_game(
) -> Any:
    """Starts the game in the Unity Editor."""
    try:
        logger.debug(f"Executing play_game with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}

        # Execute Unity RPC call
        result = await _unity_client.execute_request('play_game', params)
        logger.debug(f"play_game completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute play_game: {e}")
        raise RuntimeError(f"Tool execution failed for play_game: {e}")


async def stop_game(
) -> Any:
    """Stops the game in the Unity Editor."""
    try:
        logger.debug(f"Executing stop_game with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}

        # Execute Unity RPC call
        result = await _unity_client.execute_request('stop_game', params)
        logger.debug(f"stop_game completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute stop_game: {e}")
        raise RuntimeError(f"Tool execution failed for stop_game: {e}")


async def create_panel_settings_asset(
    asset_name: Annotated[
        str,
        Field(
            description="""Name of the new PanelSettings asset (without extension)."""
        ),
    ],
    output_path: Annotated[
        str,
        Field(
            description="""The folder path where the PanelSettings asset should be saved. If the folder doesn't exist, it will be created automatically."""
        ),
    ],
    theme_style_sheet_path: Annotated[
        str | None,
        Field(
            description="""Optional. Path to a USS (Unity Style Sheet) file to use as the theme for the panel."""
        ),
    ] = None,
    default_theme_type: Annotated[
        Literal['Default', 'Dark', 'Light', 'Runtime', 'Custom'] | None,
        Field(
            description="""Optional. The default theme type to use. Defaults to 'Default'."""
        ),
    ] = None,
    scale_mode: Annotated[
        Literal['ConstantPixelSize', 'ScaleWithScreenSize', 'ConstantPhysicalSize'] | None,
        Field(
            description="""Optional. The scale mode for the panel. Defaults to 'ConstantPhysicalSize'."""
        ),
    ] = None,
    reference_resolution: Annotated[
        str | None,
        Field(
            description="""Optional. Comma-separated reference resolution (e.g., 'width,height'). Used when scale mode is 'ScaleWithScreenSize'. Defaults to '1920,1080'."""
        ),
    ] = None,
) -> Any:
    """Creates a new PanelSettings asset for UI Toolkit in Unity."""
    try:
        logger.debug(f"Executing create_panel_settings_asset with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_name is not None:
            params['asset_name'] = str(asset_name)
        if output_path is not None:
            params['output_path'] = str(output_path)
        if theme_style_sheet_path is not None:
            params['theme_style_sheet_path'] = str(theme_style_sheet_path)
        if default_theme_type is not None:
            params['default_theme_type'] = str(default_theme_type)
        if scale_mode is not None:
            params['scale_mode'] = str(scale_mode)
        if reference_resolution is not None:
            params['reference_resolution'] = str(reference_resolution)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('create_panel_settings_asset', params)
        logger.debug(f"create_panel_settings_asset completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute create_panel_settings_asset: {e}")
        raise RuntimeError(f"Tool execution failed for create_panel_settings_asset: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from unity_functions_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register create_game_object
    mcp.tool()(create_game_object)
    # Register delete_game_object
    mcp.tool()(delete_game_object)
    # Register remove_component
    mcp.tool()(remove_component)
    # Register set_transform
    mcp.tool()(set_transform)
    # Register set_property
    mcp.tool()(set_property)
    # Register save_scene
    mcp.tool()(save_scene)
    # Register create_material
    mcp.tool()(create_material)
    # Register assign_material
    mcp.tool()(assign_material)
    # Register assign_material_to_fbx
    mcp.tool()(assign_material_to_fbx)
    # Register add_component
    mcp.tool()(add_component)
    # Register duplicate_game_object
    mcp.tool()(duplicate_game_object)
    # Register parent_game_object
    mcp.tool()(parent_game_object)
    # Register rename_game_object
    mcp.tool()(rename_game_object)
    # Register set_tag
    mcp.tool()(set_tag)
    # Register set_layer
    mcp.tool()(set_layer)
    # Register generate_3d_model_texture
    mcp.tool()(generate_3d_model_texture)
    # Register create_prefab
    mcp.tool()(create_prefab)
    # Register assign_shader_to_material
    mcp.tool()(assign_shader_to_material)
    # Register create_prefab_variant
    mcp.tool()(create_prefab_variant)
    # Register duplicate_asset
    mcp.tool()(duplicate_asset)
    # Register rename_asset
    mcp.tool()(rename_asset)
    # Register check_compile_errors
    mcp.tool()(check_compile_errors)
    # Register add_nested_object_to_prefab
    mcp.tool()(add_nested_object_to_prefab)
    # Register create_scene
    mcp.tool()(create_scene)
    # Register generate_3d_model_from_image
    mcp.tool()(generate_3d_model_from_image)
    # Register generate_3d_model_from_text
    mcp.tool()(generate_3d_model_from_text)
    # Register add_asset_to_scene
    mcp.tool()(add_asset_to_scene)
    # Register open_scene
    mcp.tool()(open_scene)
    # Register set_sibling_index
    mcp.tool()(set_sibling_index)
    # Register create_terrain
    mcp.tool()(create_terrain)
    # Register list_objects_with_high_polygon_count
    mcp.tool()(list_objects_with_high_polygon_count)
    # Register play_game
    mcp.tool()(play_game)
    # Register stop_game
    mcp.tool()(stop_game)
    # Register create_panel_settings_asset
    mcp.tool()(create_panel_settings_asset)
