"""Tests for image processing functions."""

import base64
import tempfile
import os
import pytest

from zerox_sync.processor.image import encode_image_to_base64


class TestEncodeImageToBase64:
    """Tests for encode_image_to_base64 function."""

    def test_encode_valid_image(self):
        # Create a temporary image file
        test_data = b"fake image data"
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".png") as f:
            f.write(test_data)
            temp_path = f.name

        try:
            result = encode_image_to_base64(temp_path)

            # Verify it's valid base64
            decoded = base64.b64decode(result)
            assert decoded == test_data

            # Verify it's a string
            assert isinstance(result, str)

        finally:
            os.unlink(temp_path)

    def test_encode_empty_file(self):
        # Create an empty temporary file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".png") as f:
            temp_path = f.name

        try:
            result = encode_image_to_base64(temp_path)

            # Empty file should encode to empty string
            decoded = base64.b64decode(result)
            assert decoded == b""

        finally:
            os.unlink(temp_path)

    def test_encode_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            encode_image_to_base64("/nonexistent/path/to/image.png")
