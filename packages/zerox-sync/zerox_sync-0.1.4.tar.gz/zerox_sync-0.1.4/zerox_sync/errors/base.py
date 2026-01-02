"""Base exception class for zerox_sync."""

from typing import Dict, Optional


class ZeroxError(Exception):
    """Base exception class for zerox_sync errors."""

    def __init__(self, message: str = "", extra_info: Optional[Dict] = None):
        self.message = message
        self.extra_info = extra_info or {}
        super().__init__(self.message)

    def __str__(self):
        if self.extra_info:
            return f"{self.message}\nAdditional Info: {self.extra_info}"
        return self.message


class CustomException(ZeroxError):
    """Custom exception class with additional info support."""

    pass
