"""Utility functions for image processing in MCP server."""

import base64
import logging
import mimetypes
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def convert_image_to_base64_url(image_path: str) -> Optional[str]:
    """Convert local image path to base64 data URL for MCP compatibility.

    Args:
        image_path: Local file path to the image

    Returns:
        Base64 data URL string (e.g., 'data:image/jpeg;base64,/9j/4AAQ...') or None if conversion fails
    """
    try:
        path = Path(image_path)
        if not path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return None

        if not path.is_file():
            logger.warning(f"Path is not a file: {image_path}")
            return None

        # Determine MIME type from file extension
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type or not mime_type.startswith("image/"):
            # Default to JPEG for unknown image types
            mime_type = "image/jpeg"
            logger.debug(
                f"Unknown MIME type for {image_path}, defaulting to {mime_type}"
            )

        # Read and encode image to base64
        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        data_url = f"data:{mime_type};base64,{image_data}"
        logger.debug(
            f"Successfully converted {image_path} to base64 data URL ({len(data_url)} chars)"
        )
        return data_url

    except Exception as e:
        logger.error(f"Failed to convert image to base64: {e}")
        return None


def is_image_file(file_path: str) -> bool:
    """Check if a file path points to an image file.

    Args:
        file_path: Path to check

    Returns:
        True if the file appears to be an image based on extension
    """
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type is not None and mime_type.startswith("image/")
    except Exception:
        return False


def get_image_info(image_path: str) -> Optional[dict]:
    """Get basic information about an image file.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with image info or None if file cannot be read
    """
    try:
        path = Path(image_path)
        if not path.exists():
            return None

        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))

        return {
            "path": str(path),
            "size_bytes": stat.st_size,
            "mime_type": mime_type,
            "is_image": is_image_file(str(path)),
        }
    except Exception as e:
        logger.error(f"Failed to get image info for {image_path}: {e}")
        return None
