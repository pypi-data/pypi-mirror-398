"""Image processing utilities."""

import base64


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image to base64.

    Args:
        image_path: Path to the image file

    Returns:
        Base64-encoded string
    """
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    return base64.b64encode(image_data).decode("utf-8")
