"""MCP Server for Image Zoom-In Tool.

This server provides image cropping and zooming capabilities through MCP protocol.
It allows AI models to focus on specific regions of an image for detailed analysis.
"""

import base64
import io
import math
import os
import tempfile
import uuid
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP
from PIL import Image

# Initialize MCP server
mcp = FastMCP(
    name="Image Zoom-In Tool",
    instructions="Crop and zoom into specific regions of images for detailed analysis",
)


def round_by_factor(number: int, factor: int) -> int:
    """Returns the closest integer to 'number' that is divisible by 'factor'."""
    return round(number / factor) * factor


def ceil_by_factor(number: int, factor: int) -> int:
    """Returns the smallest integer >= 'number' that is divisible by 'factor'."""
    return math.ceil(number / factor) * factor


def floor_by_factor(number: int, factor: int) -> int:
    """Returns the largest integer <= 'number' that is divisible by 'factor'."""
    return math.floor(number / factor) * factor


def smart_resize(
    height: int,
    width: int,
    factor: int = 32,
    min_pixels: int = 256 * 32 * 32,
    max_pixels: int = 12845056,
) -> tuple[int, int]:
    """Smart resize image dimensions based on factor and pixel constraints.

    Ensures output dimensions are divisible by factor and within pixel limits.
    This is important for Vision Transformer models that require specific patch sizes.
    """
    h_bar = max(factor, round_by_factor(height, factor))
    w_bar = max(factor, round_by_factor(width, factor))

    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = floor_by_factor(int(height / beta), factor)
        w_bar = floor_by_factor(int(width / beta), factor)
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = ceil_by_factor(int(height * beta), factor)
        w_bar = ceil_by_factor(int(width * beta), factor)

    return h_bar, w_bar


def maybe_resize_bbox(
    left: float,
    top: float,
    right: float,
    bottom: float,
    img_width: int,
    img_height: int,
) -> list[float]:
    """Validate and resize bbox to ensure minimum size of 32x32 pixels.

    If the bbox is too small, it will be expanded from the center while
    staying within image bounds.
    """
    left = max(0, left)
    top = max(0, top)
    right = min(img_width, right)
    bottom = min(img_height, bottom)

    height = bottom - top
    width = right - left

    if height < 32 or width < 32:
        center_x = (left + right) / 2.0
        center_y = (top + bottom) / 2.0
        ratio = 32 / min(height, width)
        new_half_height = math.ceil(height * ratio * 0.5)
        new_half_width = math.ceil(width * ratio * 0.5)

        new_left = math.floor(center_x - new_half_width)
        new_right = math.ceil(center_x + new_half_width)
        new_top = math.floor(center_y - new_half_height)
        new_bottom = math.ceil(center_y + new_half_height)

        new_left = max(0, new_left)
        new_top = max(0, new_top)
        new_right = min(img_width, new_right)
        new_bottom = min(img_height, new_bottom)

        new_height = new_bottom - new_top
        new_width = new_right - new_left

        if new_height > 32 and new_width > 32:
            return [new_left, new_top, new_right, new_bottom]

    return [left, top, right, bottom]


def load_image_from_source(image_source: str) -> Image.Image:
    """Load image from URL, file path, or base64 string.

    Supports:
    - HTTP/HTTPS URLs
    - Local file paths
    - Base64 encoded strings (with or without data URI prefix)
    """
    # Base64 encoded image
    if image_source.startswith("data:image"):
        # data:image/png;base64,xxxxx
        base64_data = image_source.split(",", 1)[1]
        image_bytes = base64.b64decode(base64_data)
        return Image.open(io.BytesIO(image_bytes))
    elif len(image_source) > 500 and not image_source.startswith(("http", "/")):
        # Likely raw base64 without prefix
        image_bytes = base64.b64decode(image_source)
        return Image.open(io.BytesIO(image_bytes))
    # HTTP URL
    elif image_source.startswith("http"):
        response = requests.get(image_source, timeout=30)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    # Local file path
    elif os.path.exists(image_source):
        return Image.open(image_source)
    else:
        raise ValueError(f"Cannot load image from: {image_source[:100]}...")


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Convert PIL Image to base64 string with data URI prefix."""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    mime_type = f"image/{format.lower()}"
    return f"data:{mime_type};base64,{base64_data}"


@mcp.tool()
def image_zoom_in(
    image_source: str,
    bbox_x1: float,
    bbox_y1: float,
    bbox_x2: float,
    bbox_y2: float,
    label: str = "region",
) -> dict[str, Any]:
    """Zoom in on a specific region of an image by cropping based on bounding box.

    This tool crops the specified region from the image and returns a zoomed-in view.
    Useful for analyzing small details or specific areas of interest.

    Args:
        image_source: The image to crop. Can be:
            - HTTP/HTTPS URL
            - Local file path
            - Base64 encoded string (with data:image prefix)
        bbox_x1: Left edge of bounding box (0-1000 relative coordinates)
        bbox_y1: Top edge of bounding box (0-1000 relative coordinates)
        bbox_x2: Right edge of bounding box (0-1000 relative coordinates)
        bbox_y2: Bottom edge of bounding box (0-1000 relative coordinates)
        label: Optional label describing the region being zoomed

    Returns:
        dict containing:
            - cropped_image: Base64 encoded cropped image
            - original_size: [width, height] of original image
            - crop_region: [x1, y1, x2, y2] absolute pixel coordinates
            - output_size: [width, height] of output image
            - label: The label provided

    Note:
        Coordinates use relative system [0, 1000] where:
        - (0, 0) is top-left corner
        - (1000, 1000) is bottom-right corner
    """
    try:
        # Load image
        image = load_image_from_source(image_source)
        img_width, img_height = image.size

        # Convert relative coordinates [0, 1000] to absolute pixels
        abs_x1 = bbox_x1 / 1000.0 * img_width
        abs_y1 = bbox_y1 / 1000.0 * img_height
        abs_x2 = bbox_x2 / 1000.0 * img_width
        abs_y2 = bbox_y2 / 1000.0 * img_height

        # Validate and potentially resize bbox
        validated_bbox = maybe_resize_bbox(
            abs_x1, abs_y1, abs_x2, abs_y2, img_width, img_height
        )
        left, top, right, bottom = validated_bbox

        # Crop the image
        cropped_image = image.crop((left, top, right, bottom))

        # Smart resize for Vision Transformer compatibility
        crop_width = right - left
        crop_height = bottom - top
        new_w, new_h = smart_resize(int(crop_height), int(crop_width), factor=32)
        cropped_image = cropped_image.resize((new_w, new_h), resample=Image.BICUBIC)

        # Convert to base64
        cropped_base64 = image_to_base64(cropped_image)

        return {
            "cropped_image": cropped_base64,
            "original_size": [img_width, img_height],
            "crop_region": [int(left), int(top), int(right), int(bottom)],
            "output_size": [new_w, new_h],
            "label": label,
        }

    except Exception as e:
        return {
            "error": str(e),
            "cropped_image": None,
        }


@mcp.tool()
def get_image_info(image_source: str) -> dict[str, Any]:
    """Get basic information about an image.

    Args:
        image_source: The image to analyze. Can be URL, file path, or base64.

    Returns:
        dict containing:
            - width: Image width in pixels
            - height: Image height in pixels
            - format: Image format (PNG, JPEG, etc.)
            - mode: Color mode (RGB, RGBA, L, etc.)
    """
    try:
        image = load_image_from_source(image_source)
        return {
            "width": image.size[0],
            "height": image.size[1],
            "format": image.format or "unknown",
            "mode": image.mode,
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
