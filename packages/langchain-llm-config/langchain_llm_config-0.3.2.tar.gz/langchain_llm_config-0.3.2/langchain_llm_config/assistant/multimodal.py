"""
Multimodal utility functions for vision-capable models
"""

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def create_image_content(
    image_path: Optional[Union[str, Path]] = None,
    image_url: Optional[str] = None,
    image_base64: Optional[str] = None,
) -> Dict[str, Any]:
    """Create image content block for multimodal input

    Args:
        image_path: Path to local image file
        image_url: URL to remote image
        image_base64: Base64 encoded image data

    Returns:
        Dict containing image content in LangChain format

    Raises:
        ValueError: If no image source is provided
    """
    if image_url:
        return {"type": "image_url", "image_url": {"url": image_url}}
    elif image_path:
        path = Path(image_path)
        with open(path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode()

        # Detect image format from file extension
        suffix = path.suffix.lower()
        if suffix in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif suffix == ".png":
            mime_type = "image/png"
        elif suffix == ".gif":
            mime_type = "image/gif"
        elif suffix == ".webp":
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"  # Default fallback

        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{base64_data}"},
        }
    elif image_base64:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
        }
    else:
        raise ValueError("Must provide image_path, image_url, or image_base64")


def create_multimodal_query(
    text: str,
    image_path: Optional[Union[str, Path]] = None,
    image_url: Optional[str] = None,
    image_base64: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Create multimodal query content for vision-capable models

    Args:
        text: Text prompt/question
        image_path: Path to local image file
        image_url: URL to remote image
        image_base64: Base64 encoded image data

    Returns:
        List of content blocks in LangChain multimodal format

    Example:
        >>> query = create_multimodal_query(
        ...     text="What do you see in this image?",
        ...     image_path="path/to/image.jpg"
        ... )
        >>> result = await assistant.ask_async(query)
    """
    content = [{"type": "text", "text": text}]

    if any([image_path, image_url, image_base64]):
        image_content = create_image_content(image_path, image_url, image_base64)
        content.append(image_content)

    return content
