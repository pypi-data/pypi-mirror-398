"""Generated MCP tools from image_tool_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def image_functions(
    is_edit: Annotated[
        bool,
        Field(
            description="""True for editing existing images (requires image_path), false for generating new images from scratch."""
        ),
    ],
    prompt: Annotated[
        str,
        Field(
            description="""Text prompt describing the image to generate or the edits to apply to existing images. Be specific and detailed."""
        ),
    ],
    save_path: Annotated[
        str | None,
        Field(
            description="""Optional file path to save the generated image. Should be relative to the Unity project Assets folder (e.g., 'Images/generated_image.png'). Defaults to Assets/ folder."""
        ),
    ],
    image_path: Annotated[
        str | None,
        Field(
            description="""Path to the image file to edit. Required when is_edit is true. Should be a file path to an existing image file in the project."""
        ),
    ] = None,
    provider: Annotated[
        Literal['gpt_image_1', 'gemini'] | None,
        Field(
            description="""AI model provider for image generation. 'gpt_image_1' provides streaming partial previews, 'gemini' provides high-quality final results with no preview. Defaults to gpt_image_1."""
        ),
    ] = None,
    size: Annotated[
        Literal['1K', '2K', '4K', 'auto'] | None,
        Field(
            description="""Target image resolution. Default is 'auto'."""
        ),
    ] = None,
    quality: Annotated[
        Literal['low', 'medium', 'high', 'auto'] | None,
        Field(
            description="""Rendering quality. Higher quality takes longer but produces better results. 'auto' lets the model choose. Defaults to auto."""
        ),
    ] = None,
    format: Annotated[
        Literal['png', 'jpeg', 'webp'] | None,
        Field(
            description="""Output image format. PNG supports transparency, JPEG is faster, WebP offers good compression. Defaults to png."""
        ),
    ] = None,
    compression: Annotated[
        int | None,
        Field(
            description="""Compression level for JPEG and WebP formats (0-100%). Higher values mean less compression and larger file sizes. Defaults to 100."""
        ),
    ] = None,
    transparent_background: Annotated[
        bool | None,
        Field(
            description="""Enable transparent background. Only supported with PNG and WebP formats. Works best with medium or high quality. Defaults to false."""
        ),
    ] = None,
    object_size: Annotated[
        str | None,
        Field(
            description="""Optional size of the generated object (opaque area of the image), specified in pixels as a comma-separated width,height vector (e.g., '512,512'). Defaults to null (no object size)."""
        ),
    ] = None,
    scale_mode: Annotated[
        Literal['fit_canvas', 'trim', 'crop'] | None,
        Field(
            description="""How to scale the image to object_size. 'fit_canvas' (default) scales and centers the image on a transparent canvas of exact object_size. 'trim' scales the image to fit within object_size bounds without adding padding. 'crop' scales the image to fully cover object_size and crops overflow to exact dimensions. Only applies when object_size is specified. Defaults to fit_canvas."""
        ),
    ] = None,
    aspect: Annotated[
        Literal['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9', 'auto'] | None,
        Field(
            description="""Aspect ratio for the generated image. Options include common ratios like 1:1 (square), 16:9 (widescreen), 9:16 (portrait), etc. 'auto' lets the model choose. Defaults to auto."""
        ),
    ] = None,
) -> Any:
    """Generate new images from text prompts or edit existing images."""
    try:
        logger.debug(f"Executing image_functions with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if is_edit is not None:
            params['is_edit'] = str(is_edit)
        if image_path is not None:
            params['image_path'] = str(image_path)
        if prompt is not None:
            params['prompt'] = str(prompt)
        if provider is not None:
            params['provider'] = str(provider)
        if size is not None:
            params['size'] = str(size)
        if quality is not None:
            params['quality'] = str(quality)
        if format is not None:
            params['format'] = str(format)
        if compression is not None:
            params['compression'] = str(compression)
        if transparent_background is not None:
            params['transparent_background'] = str(transparent_background)
        if save_path is not None:
            params['save_path'] = str(save_path)
        if object_size is not None:
            params['object_size'] = str(object_size)
        if scale_mode is not None:
            params['scale_mode'] = str(scale_mode)
        if aspect is not None:
            params['aspect'] = str(aspect)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('image_functions', params)
        logger.debug(f"image_functions completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute image_functions: {e}")
        raise RuntimeError(f"Tool execution failed for image_functions: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from image_tool_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register image_functions
    mcp.tool()(image_functions)
