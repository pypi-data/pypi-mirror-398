"""Text formatting utilities."""

import re


def format_markdown(text: str) -> str:
    """
    Format markdown text by removing markdown and code block delimiters.

    Args:
        text: Raw markdown string

    Returns:
        Formatted markdown string
    """
    # Remove markdown code blocks (e.g., ```markdown ... ```)
    formatted_markdown = re.sub(r"^```[a-z]*\n([\s\S]*?)\n```$", r"\1", text)
    # Remove generic code blocks (e.g., ``` ... ```)
    formatted_markdown = re.sub(r"^```\n([\s\S]*?)\n```$", r"\1", formatted_markdown)

    return formatted_markdown.strip()
