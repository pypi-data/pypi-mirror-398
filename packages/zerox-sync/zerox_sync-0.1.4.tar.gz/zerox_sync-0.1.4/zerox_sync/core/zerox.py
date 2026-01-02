"""Main API for zerox_sync."""

import os
import shutil
import tempfile
import warnings
from typing import List, Optional, Union, Iterable
from datetime import datetime

from ..constants import PDFConversionDefaultOptions, Messages
from ..processor import (
    convert_pdf_to_images,
    download_file,
    process_page,
    process_pages_in_batches,
    create_selected_pages_pdf,
)
from ..errors import FileUnavailable
from ..models import GeminiModel
from .types import Page, ZeroxOutput


def zerox(
    cleanup: bool = True,
    concurrency: int = 10,
    file_path: Optional[str] = "",
    image_density: int = PDFConversionDefaultOptions.DPI,
    image_height: tuple = PDFConversionDefaultOptions.SIZE,
    maintain_format: bool = False,
    model: str = "gemini-3-pro",
    output_dir: Optional[str] = None,
    temp_dir: Optional[str] = None,
    custom_system_prompt: Optional[str] = None,
    select_pages: Optional[Union[int, Iterable[int]]] = None,
    **kwargs
) -> ZeroxOutput:
    """
    API to perform OCR to markdown using Gemini vision models.
    Please set the GOOGLE_API_KEY environment variable before using this API.
    Get your API key from: https://aistudio.google.com/apikey

    Args:
        cleanup: Whether to cleanup the temporary files after processing (default: True)
        concurrency: The number of concurrent processes to run (default: 10)
        file_path: The path or URL to the PDF file to process
        image_density: DPI for image conversion (default: 300)
        image_height: Tuple of (width, height) for image sizing (default: (None, 1056))
        maintain_format: Whether to maintain the format from the previous page (default: False)
        model: The Gemini model to use (default: gemini-3-pro)
        output_dir: The directory to save the markdown output (default: None)
        temp_dir: The directory to store temporary files (default: system temp)
        custom_system_prompt: Override the default system prompt (default: None)
        select_pages: Pages to process, can be a single page number or an iterable (default: None)
        **kwargs: Additional keyword arguments to pass to the Gemini API

    Returns:
        ZeroxOutput object containing the markdown content and metadata

    Raises:
        FileUnavailable: If the file path is invalid or missing
        MissingEnvironmentVariables: If GOOGLE_API_KEY is not set
        ResourceUnreachableException: If a URL cannot be downloaded
        PageNumberOutOfBoundError: If invalid page numbers are provided
    """
    input_token_count = 0
    output_token_count = 0
    prior_page = ""
    aggregated_markdown: List[str] = []
    start_time = datetime.now()

    # File Path Validators
    if not file_path:
        raise FileUnavailable()

    # Create an instance of the Gemini model interface
    vision_model = GeminiModel(model=model, **kwargs)

    # Override the system prompt if a custom prompt is provided
    if custom_system_prompt:
        vision_model.system_prompt = custom_system_prompt
        warnings.warn(Messages.CUSTOM_SYSTEM_PROMPT_WARNING)

    # Check if both maintain_format and select_pages are provided
    if maintain_format and select_pages is not None:
        warnings.warn(Messages.MAINTAIN_FORMAT_SELECTED_PAGES_WARNING)

    # If select_pages is a single integer, convert it to a list for consistency
    if isinstance(select_pages, int):
        select_pages = [select_pages]

    # Sort the pages to maintain consistency
    if select_pages is not None:
        select_pages = sorted(select_pages)

    # Ensure the output directory exists
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Delete temp_dir if exists and then recreate it
    if temp_dir:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

    # Create a temporary directory to store the PDF and images
    with tempfile.TemporaryDirectory() as temp_dir_:
        if temp_dir:
            # Use the user provided temp directory
            temp_directory = temp_dir
        else:
            # Use the system temp directory
            temp_directory = temp_dir_

        # Download the PDF. Get file name.
        local_path = download_file(file_path=file_path, temp_dir=temp_directory)
        if not local_path:
            raise FileUnavailable()

        raw_file_name = os.path.splitext(os.path.basename(local_path))[0]
        file_name = "".join(c.lower() if c.isalnum() else "_" for c in raw_file_name)
        # Truncate file name to 255 characters to prevent ENAMETOOLONG errors
        file_name = file_name[:255]

        # Create a subset pdf in temp dir with only the requested pages if select_pages is provided
        if select_pages is not None:
            local_path = create_selected_pages_pdf(
                original_pdf_path=local_path,
                select_pages=select_pages,
                save_directory=temp_directory,
                suffix="_selected_pages",
            )

        # Convert the file to a series of images
        images = convert_pdf_to_images(
            image_density=image_density,
            image_height=image_height,
            local_path=local_path,
            temp_dir=temp_directory,
        )

        if maintain_format:
            # Process pages sequentially to maintain format consistency
            for image in images:
                result, input_token_count, output_token_count, prior_page = process_page(
                    image,
                    vision_model,
                    temp_directory,
                    input_token_count,
                    output_token_count,
                    prior_page,
                )

                if result:
                    aggregated_markdown.append(result)
        else:
            # Process pages in parallel
            results = process_pages_in_batches(
                images,
                concurrency,
                vision_model,
                temp_directory,
                input_token_count,
                output_token_count,
                prior_page,
            )

            aggregated_markdown = [result[0] for result in results if isinstance(result[0], str)]

            # Add token usage
            input_token_count += sum([result[1] for result in results])
            output_token_count += sum([result[2] for result in results])

        # Write the aggregated markdown to a file
        if output_dir:
            result_file_path = os.path.join(output_dir, f"{file_name}.md")
            with open(result_file_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(aggregated_markdown))

        # Cleanup the downloaded PDF file
        if cleanup and os.path.exists(temp_directory):
            shutil.rmtree(temp_directory)

        # Format JSON response
        end_time = datetime.now()
        completion_time = (end_time - start_time).total_seconds() * 1000

        # Adjusting the formatted_pages logic to account for select_pages
        if select_pages is not None:
            # Map aggregated markdown to the selected pages
            formatted_pages = [
                Page(content=content, page=select_pages[i], content_length=len(content))
                for i, content in enumerate(aggregated_markdown)
            ]
        else:
            # Default behavior when no select_pages is provided
            formatted_pages = [
                Page(content=content, page=i + 1, content_length=len(content))
                for i, content in enumerate(aggregated_markdown)
            ]

        return ZeroxOutput(
            completion_time=completion_time,
            file_name=file_name,
            input_tokens=input_token_count,
            output_tokens=output_token_count,
            pages=formatted_pages,
        )
