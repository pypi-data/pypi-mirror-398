"""Gemini API model interface."""

import os
from typing import Dict, Any, List

from google import genai
from google.genai import types

from ..constants.prompts import Prompts
from ..constants.messages import Messages
from ..errors.exceptions import (
    MissingEnvironmentVariables,
    ModelAccessError,
)
from ..processor.image import encode_image_to_base64

DEFAULT_SYSTEM_PROMPT = Prompts.DEFAULT_SYSTEM_PROMPT


class GeminiModel:
    """Interface for Google Gemini vision models."""

    def __init__(self, model: str = "gemini-3-pro", **kwargs):
        """
        Initialize the Gemini model interface.

        Args:
            model: The Gemini model to use (default: gemini-3-pro)
            **kwargs: Additional arguments to pass to the model
        """
        self.model = model
        self.kwargs = kwargs
        self._system_prompt = DEFAULT_SYSTEM_PROMPT

        # Validate environment and initialize client
        self.validate_environment()
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    @property
    def system_prompt(self) -> str:
        """Returns the system prompt for the model."""
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, prompt: str) -> None:
        """Sets/overrides the system prompt for the model."""
        self._system_prompt = prompt

    def validate_environment(self) -> None:
        """Validates that the GOOGLE_API_KEY environment variable is set."""
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise MissingEnvironmentVariables()

    def completion(
        self,
        image_path: str,
        maintain_format: bool,
        prior_page: str,
    ) -> Dict[str, Any]:
        """
        Gemini completion for image to markdown conversion.

        Args:
            image_path: Path to the image file
            maintain_format: Whether to maintain the format from the previous page
            prior_page: The markdown content of the previous page

        Returns:
            Dictionary with keys: content, input_tokens, output_tokens
        """
        messages = self._prepare_messages(
            image_path=image_path,
            maintain_format=maintain_format,
            prior_page=prior_page,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=messages,
                config=types.GenerateContentConfig(**self.kwargs) if self.kwargs else None,
            )

            # Extract token usage
            input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
            output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0

            return {
                "content": response.text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

        except Exception as err:
            raise Exception(Messages.COMPLETION_ERROR.format(err))

    def _prepare_messages(
        self,
        image_path: str,
        maintain_format: bool,
        prior_page: str,
    ) -> List[Any]:
        """
        Prepares the messages to send to the Gemini API.

        Args:
            image_path: Path to the image file
            maintain_format: Whether to maintain the format from the previous page
            prior_page: The markdown content of the previous page

        Returns:
            List of content parts for the Gemini API
        """
        messages = []

        # Add system prompt
        messages.append(self._system_prompt)

        # If content has already been generated, add it to context
        # This helps maintain the same format across pages
        if maintain_format and prior_page:
            messages.append(
                f'Markdown must maintain consistent formatting with the following page: \n\n """{prior_page}"""'
            )

        # Add image to request
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # Determine mime type from file extension
        ext = os.path.splitext(image_path)[1].lower()
        mime_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".heic": "image/heic",
            ".heif": "image/heif",
        }
        mime_type = mime_type_map.get(ext, "image/png")

        messages.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )
        )

        return messages
