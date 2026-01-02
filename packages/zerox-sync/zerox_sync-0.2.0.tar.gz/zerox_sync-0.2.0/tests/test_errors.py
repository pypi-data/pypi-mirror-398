"""Tests for error classes."""

import pytest

from zerox_sync.errors import (
    ZeroxError,
    FileUnavailable,
    ResourceUnreachableException,
    PageNumberOutOfBoundError,
    MissingEnvironmentVariables,
    NotAVisionModel,
    ModelAccessError,
)


class TestZeroxError:
    """Tests for base ZeroxError class."""

    def test_error_with_message(self):
        error = ZeroxError("Test error message")
        assert str(error) == "Test error message"

    def test_error_with_extra_info(self):
        error = ZeroxError("Test error", extra_info={"key": "value"})
        assert "Test error" in str(error)
        assert "key" in str(error)

    def test_error_without_message(self):
        error = ZeroxError()
        assert str(error) == ""


class TestCustomExceptions:
    """Tests for custom exception classes."""

    def test_file_unavailable(self):
        error = FileUnavailable()
        assert "File path" in str(error) or "missing" in str(error).lower()

    def test_resource_unreachable(self):
        error = ResourceUnreachableException(extra_info={"status_code": 404})
        assert "404" in str(error) or "unreachable" in str(error).lower()

    def test_page_number_out_of_bound(self):
        error = PageNumberOutOfBoundError(
            extra_info={
                "input_pdf_num_pages": 10,
                "select_pages": [1, 15],
                "invalid_page_numbers": [15],
            }
        )
        assert "page" in str(error).lower()

    def test_missing_environment_variables(self):
        error = MissingEnvironmentVariables()
        assert "GEMINI_API_KEY" in str(error) or "environment" in str(error).lower()

    def test_not_a_vision_model(self):
        error = NotAVisionModel(extra_info={"model": "text-model"})
        assert "vision" in str(error).lower()

    def test_model_access_error(self):
        error = ModelAccessError(extra_info={"model": "gemini-3-pro"})
        assert "access" in str(error).lower() or "API" in str(error)
