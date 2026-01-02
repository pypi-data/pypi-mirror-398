"""Type definitions for zerox_sync."""

from typing import List, Optional, Dict, Any, Union, Iterable
from dataclasses import dataclass, field


@dataclass
class Page:
    """
    Dataclass to store the page content.
    """

    content: str
    content_length: int
    page: int


@dataclass
class ZeroxOutput:
    """
    Dataclass to store the output of the Zerox class.
    """

    completion_time: float
    file_name: str
    input_tokens: int
    output_tokens: int
    pages: List[Page]
