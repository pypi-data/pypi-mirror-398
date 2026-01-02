"""Exception classes for zerox_sync."""

from .base import ZeroxError, CustomException
from .exceptions import (
    FileUnavailable,
    ResourceUnreachableException,
    PageNumberOutOfBoundError,
    MissingEnvironmentVariables,
    NotAVisionModel,
    ModelAccessError,
)

__all__ = [
    "ZeroxError",
    "CustomException",
    "FileUnavailable",
    "ResourceUnreachableException",
    "PageNumberOutOfBoundError",
    "MissingEnvironmentVariables",
    "NotAVisionModel",
    "ModelAccessError",
]
