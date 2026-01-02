"""PDF processing utilities."""

import logging
import os
from typing import List, Optional, Tuple
from pdf2image import convert_from_path
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..constants import PDFConversionDefaultOptions, Messages
from ..models import GeminiModel
from .text import format_markdown


def convert_pdf_to_images(
    image_density: int,
    image_height: tuple,
    local_path: str,
    temp_dir: str,
) -> List[str]:
    """
    Converts a PDF file to a series of images in the temp_dir.
    Returns a list of image paths in page order.

    Args:
        image_density: DPI for image conversion
        image_height: Tuple of (width, height) for image sizing
        local_path: Path to the PDF file
        temp_dir: Directory to save images

    Returns:
        List of image paths in page order
    """
    options = {
        "pdf_path": local_path,
        "output_folder": temp_dir,
        "dpi": image_density,
        "fmt": PDFConversionDefaultOptions.FORMAT,
        "size": image_height,
        "thread_count": PDFConversionDefaultOptions.THREAD_COUNT,
        "use_pdftocairo": PDFConversionDefaultOptions.USE_PDFTOCAIRO,
        "paths_only": True,
    }

    try:
        image_paths = convert_from_path(**options)
        return image_paths
    except Exception as err:
        logging.error(f"Error converting PDF to images: {err}")
        raise Exception(Messages.PDF_CONVERSION_FAILED.format(err))


def process_page(
    image: str,
    model: GeminiModel,
    temp_directory: str = "",
    input_token_count: int = 0,
    output_token_count: int = 0,
    prior_page: str = "",
) -> Tuple[str, int, int, str]:
    """
    Process a single page of a PDF.

    Args:
        image: Image filename
        model: Gemini model instance
        temp_directory: Directory containing the image
        input_token_count: Current input token count
        output_token_count: Current output token count
        prior_page: Content of the previous page (for format consistency)

    Returns:
        Tuple of (formatted_markdown, input_tokens, output_tokens, prior_page)
    """
    image_path = os.path.join(temp_directory, image)

    try:
        completion = model.completion(
            image_path=image_path,
            maintain_format=True,
            prior_page=prior_page,
        )

        formatted_markdown = format_markdown(completion["content"])
        input_token_count += completion["input_tokens"]
        output_token_count += completion["output_tokens"]
        prior_page = formatted_markdown

        return formatted_markdown, input_token_count, output_token_count, prior_page

    except Exception as error:
        logging.error(f"{Messages.FAILED_TO_PROCESS_IMAGE} Error:{error}")
        return "", input_token_count, output_token_count, ""


def process_pages_in_batches(
    images: List[str],
    concurrency: int,
    model: GeminiModel,
    temp_directory: str = "",
    input_token_count: int = 0,
    output_token_count: int = 0,
    prior_page: str = "",
) -> List[Tuple[str, int, int, str]]:
    """
    Process multiple pages in parallel using ThreadPoolExecutor.

    Args:
        images: List of image filenames
        concurrency: Number of concurrent threads
        model: Gemini model instance
        temp_directory: Directory containing the images
        input_token_count: Current input token count
        output_token_count: Current output token count
        prior_page: Content of the previous page (for format consistency)

    Returns:
        List of tuples (formatted_markdown, input_tokens, output_tokens, prior_page)
    """
    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Submit all tasks
        future_to_image = {
            executor.submit(
                process_page,
                image,
                model,
                temp_directory,
                input_token_count,
                output_token_count,
                prior_page,
            ): image
            for image in images
        }

        # Collect results in submission order
        for future in as_completed(future_to_image):
            try:
                result = future.result()
                results.append(result)
            except Exception as error:
                logging.error(f"Error processing page: {error}")
                results.append(("", 0, 0, ""))

    return results
