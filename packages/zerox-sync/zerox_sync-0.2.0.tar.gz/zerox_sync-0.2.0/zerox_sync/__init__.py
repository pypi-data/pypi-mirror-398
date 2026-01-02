"""
Zerox Sync - Synchronous OCR using Gemini Vision API

A synchronous rewrite of pyzerox that uses Google's Gemini API directly
instead of litellm, without async wrappers.
"""

from .core import zerox
from .constants.prompts import Prompts

DEFAULT_SYSTEM_PROMPT = Prompts.DEFAULT_SYSTEM_PROMPT

__version__ = "0.1.0"

__all__ = [
    "zerox",
    "Prompts",
    "DEFAULT_SYSTEM_PROMPT",
]
