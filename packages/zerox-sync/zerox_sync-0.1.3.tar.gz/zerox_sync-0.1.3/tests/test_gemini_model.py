"""Tests for Gemini model interface."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from zerox_sync.models.gemini import GeminiModel
from zerox_sync.errors import MissingEnvironmentVariables


class TestGeminiModel:
    """Tests for GeminiModel class."""

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("zerox_sync.models.gemini.genai.Client")
    def test_initialization_with_api_key(self, mock_client):
        model = GeminiModel(model="gemini-3-pro")

        assert model.model == "gemini-3-pro"
        assert model.system_prompt is not None
        mock_client.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_initialization_without_api_key(self):
        with pytest.raises(MissingEnvironmentVariables):
            GeminiModel(model="gemini-3-pro")

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("zerox_sync.models.gemini.genai.Client")
    def test_custom_system_prompt(self, mock_client):
        model = GeminiModel(model="gemini-3-pro")
        custom_prompt = "Custom prompt for testing"

        model.system_prompt = custom_prompt

        assert model.system_prompt == custom_prompt

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("zerox_sync.models.gemini.genai.Client")
    def test_prepare_messages_basic(self, mock_client):
        model = GeminiModel(model="gemini-3-pro")

        # Create a temporary test image
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".png") as f:
            f.write(b"fake image data")
            temp_path = f.name

        try:
            messages = model._prepare_messages(
                image_path=temp_path,
                maintain_format=False,
                prior_page="",
            )

            # Should have system prompt and image
            assert len(messages) >= 2
            assert isinstance(messages[0], str)  # System prompt

        finally:
            os.unlink(temp_path)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("zerox_sync.models.gemini.genai.Client")
    def test_prepare_messages_with_prior_page(self, mock_client):
        model = GeminiModel(model="gemini-3-pro")

        # Create a temporary test image
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".png") as f:
            f.write(b"fake image data")
            temp_path = f.name

        try:
            messages = model._prepare_messages(
                image_path=temp_path,
                maintain_format=True,
                prior_page="# Previous Page\n\nContent here",
            )

            # Should have system prompt, format instruction, and image
            assert len(messages) >= 3

        finally:
            os.unlink(temp_path)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("zerox_sync.models.gemini.genai.Client")
    def test_completion_success(self, mock_client):
        # Mock the client and response
        mock_response = MagicMock()
        mock_response.text = "# Extracted Content\n\nTest content"
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50

        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client.return_value = mock_client_instance

        model = GeminiModel(model="gemini-3-pro")

        # Create a temporary test image
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".png") as f:
            f.write(b"fake image data")
            temp_path = f.name

        try:
            result = model.completion(
                image_path=temp_path,
                maintain_format=False,
                prior_page="",
            )

            assert result["content"] == "# Extracted Content\n\nTest content"
            assert result["input_tokens"] == 100
            assert result["output_tokens"] == 50

        finally:
            os.unlink(temp_path)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("zerox_sync.models.gemini.genai.Client")
    def test_completion_error(self, mock_client):
        # Mock the client to raise an exception
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.side_effect = Exception("API Error")
        mock_client.return_value = mock_client_instance

        model = GeminiModel(model="gemini-3-pro")

        # Create a temporary test image
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".png") as f:
            f.write(b"fake image data")
            temp_path = f.name

        try:
            with pytest.raises(Exception) as exc_info:
                model.completion(
                    image_path=temp_path,
                    maintain_format=False,
                    prior_page="",
                )

            assert "API Error" in str(exc_info.value)

        finally:
            os.unlink(temp_path)
