"""User-facing messages."""


class Messages:
    """User-facing messages"""

    MISSING_ENVIRONMENT_VARIABLES = """
    Required environment variable GEMINI_API_KEY is missing. Please set the GEMINI_API_KEY environment variable.
    Get your API key from: https://aistudio.google.com/apikey
    """

    NON_VISION_MODEL = """
    The provided model is not a vision model. Please provide a vision model.
    """

    MODEL_ACCESS_ERROR = """
    Your provided model can't be accessed. Please make sure you have access to the model and the GEMINI_API_KEY environment variable is set correctly.
    Get your API key from: https://aistudio.google.com/apikey
    """

    CUSTOM_SYSTEM_PROMPT_WARNING = """
    Custom system prompt was provided which overrides the default system prompt. We assume that you know what you are doing.
    """

    MAINTAIN_FORMAT_SELECTED_PAGES_WARNING = """
    The maintain_format flag is set to True in conjunction with select_pages input given. This may result in unexpected behavior.
    """

    PAGE_NUMBER_OUT_OF_BOUND_ERROR = """
    The page number(s) provided is out of bound. Please provide a valid page number(s).
    """

    COMPLETION_ERROR = """
    Error in Completion Response. Error: {0}
    Please check the status of your Gemini API.
    """

    PDF_CONVERSION_FAILED = """
    Error during PDF conversion: {0}
    Please check the PDF file and try again. For more information: https://github.com/Belval/pdf2image
    """

    FILE_UNREACHABLE = """
    File not found or unreachable. Status Code: {0}
    """

    FILE_PATH_MISSING = """
    File path is invalid or missing.
    """

    FAILED_TO_SAVE_FILE = """Failed to save file to local drive"""

    FAILED_TO_PROCESS_IMAGE = """Failed to process image"""
