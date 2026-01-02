"""Tests for utility functions."""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open, MagicMock

from zerox_sync.processor.utils import (
    is_valid_url,
    download_file,
    create_selected_pages_pdf,
)
from zerox_sync.errors import ResourceUnreachableException, PageNumberOutOfBoundError


class TestIsValidUrl:
    """Tests for is_valid_url function."""

    def test_valid_http_url(self):
        assert is_valid_url("http://example.com") is True

    def test_valid_https_url(self):
        assert is_valid_url("https://example.com/path/to/file.pdf") is True

    def test_invalid_url_no_scheme(self):
        assert is_valid_url("example.com") is False

    def test_invalid_url_no_netloc(self):
        assert is_valid_url("http://") is False

    def test_invalid_url_file_path(self):
        assert is_valid_url("/path/to/file.pdf") is False

    def test_invalid_url_ftp(self):
        assert is_valid_url("ftp://example.com") is False


class TestDownloadFile:
    """Tests for download_file function."""

    def test_download_from_local_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_content = b"test content"
            test_file = os.path.join(temp_dir, "test.pdf")
            with open(test_file, "wb") as f:
                f.write(test_content)

            # Download (copy) the file
            result = download_file(test_file, temp_dir)

            assert result is not None
            assert os.path.exists(result)
            with open(result, "rb") as f:
                assert f.read() == test_content

    @patch("zerox_sync.processor.utils.requests.get")
    def test_download_from_url_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"pdf content"
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            result = download_file("https://example.com/test.pdf", temp_dir)

            assert result is not None
            assert os.path.exists(result)
            with open(result, "rb") as f:
                assert f.read() == b"pdf content"

    @patch("zerox_sync.processor.utils.requests.get")
    def test_download_from_url_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ResourceUnreachableException):
                download_file("https://example.com/nonexistent.pdf", temp_dir)


class TestCreateSelectedPagesPdf:
    """Tests for create_selected_pages_pdf function."""

    @patch("zerox_sync.processor.utils.PdfReader")
    @patch("zerox_sync.processor.utils.PdfWriter")
    def test_create_pdf_with_single_page(self, mock_writer_class, mock_reader_class):
        # Mock PDF reader with 10 pages
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock() for _ in range(10)]
        mock_reader_class.return_value = mock_reader

        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer

        with tempfile.TemporaryDirectory() as temp_dir:
            test_pdf = os.path.join(temp_dir, "test.pdf")
            with open(test_pdf, "wb") as f:
                f.write(b"fake pdf")

            result = create_selected_pages_pdf(
                original_pdf_path=test_pdf,
                select_pages=5,
                save_directory=temp_dir,
            )

            assert result.endswith("_selected_pages.pdf")
            assert mock_writer.add_page.call_count == 1

    @patch("zerox_sync.processor.utils.PdfReader")
    @patch("zerox_sync.processor.utils.PdfWriter")
    def test_create_pdf_with_multiple_pages(self, mock_writer_class, mock_reader_class):
        # Mock PDF reader with 10 pages
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock() for _ in range(10)]
        mock_reader_class.return_value = mock_reader

        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer

        with tempfile.TemporaryDirectory() as temp_dir:
            test_pdf = os.path.join(temp_dir, "test.pdf")
            with open(test_pdf, "wb") as f:
                f.write(b"fake pdf")

            result = create_selected_pages_pdf(
                original_pdf_path=test_pdf,
                select_pages=[1, 3, 5, 7],
                save_directory=temp_dir,
            )

            assert result.endswith("_selected_pages.pdf")
            assert mock_writer.add_page.call_count == 4

    @patch("zerox_sync.processor.utils.PdfReader")
    def test_create_pdf_with_invalid_page_numbers(self, mock_reader_class):
        # Mock PDF reader with 5 pages
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock() for _ in range(5)]
        mock_reader_class.return_value = mock_reader

        with tempfile.TemporaryDirectory() as temp_dir:
            test_pdf = os.path.join(temp_dir, "test.pdf")
            with open(test_pdf, "wb") as f:
                f.write(b"fake pdf")

            with pytest.raises(PageNumberOutOfBoundError):
                create_selected_pages_pdf(
                    original_pdf_path=test_pdf,
                    select_pages=[1, 10, 15],  # 10 and 15 are out of bounds
                    save_directory=temp_dir,
                )
