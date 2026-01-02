"""Utility functions for file operations."""

import os
from typing import Optional, Union, Iterable
from urllib.parse import urlparse
import requests
from pypdf import PdfReader, PdfWriter

from ..constants.messages import Messages
from ..errors.exceptions import ResourceUnreachableException, PageNumberOutOfBoundError


def download_file(file_path: str, temp_dir: str) -> Optional[str]:
    """
    Downloads a file from a URL or copies from local path to a temporary directory.

    Args:
        file_path: URL or local path to the file
        temp_dir: Temporary directory to save the file

    Returns:
        Path to the downloaded/copied file

    Raises:
        ResourceUnreachableException: If the file cannot be downloaded
    """
    local_pdf_path = os.path.join(temp_dir, os.path.basename(file_path))

    if is_valid_url(file_path):
        response = requests.get(file_path, timeout=30)
        if response.status_code != 200:
            raise ResourceUnreachableException(
                extra_info={"url": file_path, "status_code": response.status_code}
            )
        with open(local_pdf_path, "wb") as f:
            f.write(response.content)
    else:
        # If source and destination are the same, just return the path
        if os.path.abspath(file_path) == os.path.abspath(local_pdf_path):
            return local_pdf_path

        # Read first, then write to avoid truncation issues
        with open(file_path, "rb") as src:
            content = src.read()
        with open(local_pdf_path, "wb") as dst:
            dst.write(content)

    return local_pdf_path


def is_valid_url(string: str) -> bool:
    """
    Checks if a string is a valid URL.

    Args:
        string: String to check

    Returns:
        True if the string is a valid URL, False otherwise
    """
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc]) and result.scheme in [
            "http",
            "https",
        ]
    except ValueError:
        return False


def create_selected_pages_pdf(
    original_pdf_path: str,
    select_pages: Union[int, Iterable[int]],
    save_directory: str,
    suffix: str = "_selected_pages",
    sorted_pages: bool = True,
) -> str:
    """
    Creates a new PDF with only the selected pages.

    Args:
        original_pdf_path: Path to the original PDF file
        select_pages: A single page number or an iterable of page numbers (1-indexed)
        save_directory: The directory to store the new PDF
        suffix: The suffix to add to the new PDF file name
        sorted_pages: Whether to sort the selected pages

    Returns:
        Path to the new PDF file

    Raises:
        PageNumberOutOfBoundError: If invalid page numbers are provided
    """
    file_name = os.path.splitext(os.path.basename(original_pdf_path))[0]
    selected_pages_pdf_path = os.path.join(save_directory, f"{file_name}{suffix}.pdf")

    # Ensure select_pages is iterable, if not, convert to list
    if isinstance(select_pages, int):
        select_pages = [select_pages]

    if sorted_pages:
        # Sort the pages for consistency
        select_pages = sorted(list(select_pages))

    with open(original_pdf_path, "rb") as orig_pdf, open(
        selected_pages_pdf_path, "wb"
    ) as new_pdf:
        # Read the original PDF
        reader = PdfReader(stream=orig_pdf)
        total_pages = len(reader.pages)

        # Validate page numbers
        invalid_page_numbers = []
        for page in select_pages:
            if page < 1 or page > total_pages:
                invalid_page_numbers.append(page)

        # Raise error if invalid page numbers
        if invalid_page_numbers:
            raise PageNumberOutOfBoundError(
                extra_info={
                    "input_pdf_num_pages": total_pages,
                    "select_pages": select_pages,
                    "invalid_page_numbers": invalid_page_numbers,
                }
            )

        # Create a new PDF writer
        writer = PdfWriter(fileobj=new_pdf)

        # Add only the selected pages
        for page_number in select_pages:
            writer.add_page(reader.pages[page_number - 1])

        writer.write(stream=new_pdf)

    return selected_pages_pdf_path
