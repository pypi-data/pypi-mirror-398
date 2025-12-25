import base64
import logging
import io
from PIL import Image

_logger = logging.getLogger(__name__)


def convert_to_base64(image_bytes: bytes, ext: str) -> str:
    """Convert image bytes to base64 data URL format.

    Args:
        image_bytes: Raw image bytes
        ext: File extension (e.g., "jpg", "png")

    Returns:
        Base64 encoded data URL string

    Usage:
        >>> with open("image.jpg", "rb") as f:
        ...     image_bytes = f.read()
        >>> b64 = convert_to_base64(image_bytes, "jpg")
        >>> print(b64[:50])  # "data:image/jpg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
    """
    ext = ext.replace(".", "")
    return f"data:image/{ext};base64,{base64.b64encode(image_bytes).decode('utf-8')}"


def get_image_cropped_to_context(image_bytes: bytes, padding: int = 10) -> bytes:
    """Crop image to content boundaries with padding.

    Uses threshold-based detection to find the bounding box of content
    and crops the image to that area with optional padding.

    Args:
        image_bytes: Raw image bytes
        padding: Padding to add around content (default: 10)

    Returns:
        Cropped image bytes in JPEG format

    Usage:
        >>> with open("receipt.jpg", "rb") as f:
        ...     image_bytes = f.read()
        >>> cropped = get_image_cropped_to_context(image_bytes)
        >>> with open("cropped.jpg", "wb") as f:
        ...     f.write(cropped)
    """
    image = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if necessary (handles RGBA, P, and other modes)
    if image.mode != "RGB":
        image = image.convert("RGB")

    gray = image.convert("L")

    # Convert to binary image using threshold
    threshold = 180
    binary = gray.point(lambda x: 255 if x > threshold else 0, "1")

    # Find bounding box of content
    bbox = binary.getbbox()

    if bbox:
        # Add padding
        width, height = image.size
        bbox = (
            max(0, bbox[0] - padding),
            max(0, bbox[1] - padding),
            min(width, bbox[2] + padding),
            min(height, bbox[3] + padding),
        )

        cropped = image.crop(bbox)

        # Convert back to bytes
        output_buffer = io.BytesIO()
        cropped.save(output_buffer, format="JPEG")
        return output_buffer.getvalue()

    # Return original image bytes if no content found
    return image_bytes


def get_optimized_image_as_jpeg(image_bytes: bytes, quality: int = 85) -> bytes:
    """Optimize image and convert to JPEG format.

    Args:
        image_bytes: Raw image bytes
        quality: JPEG quality (1-100, default: 85)

    Returns:
        Optimized JPEG image bytes

    Usage:
        >>> with open("large_image.png", "rb") as f:
        ...     image_bytes = f.read()
        >>> optimized = get_optimized_image_as_jpeg(image_bytes)
        >>> print(f"Original: {len(image_bytes)}, Optimized: {len(optimized)}")
    """
    image = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if necessary (handles RGBA, P, and other modes)
    if image.mode != "RGB":
        image = image.convert("RGB")

    output_buffer = io.BytesIO()
    image.save(output_buffer, format="JPEG", quality=quality, optimize=True)
    return output_buffer.getvalue()


def get_image_info(image_bytes: bytes) -> dict:
    """Get basic information about an image.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Dictionary with image information

    Usage:
        >>> with open("image.jpg", "rb") as f:
        ...     image_bytes = f.read()
        >>> info = get_image_info(image_bytes)
        >>> print(f"Size: {info['width']}x{info['height']}, Format: {info['format']}")
    """
    image = Image.open(io.BytesIO(image_bytes))

    return {
        "width": image.width,
        "height": image.height,
        "format": image.format,
        "mode": image.mode,
        "size_bytes": len(image_bytes),
    }
