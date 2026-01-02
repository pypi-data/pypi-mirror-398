"""Integration tests for zerox_sync."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from zerox_sync import zerox
from zerox_sync.errors import FileUnavailable, MissingEnvironmentVariables


class TestZeroxIntegration:
    """Integration tests for the main zerox function."""

    def test_zerox_requires_file_path(self):
        with pytest.raises(FileUnavailable):
            zerox(file_path="")

    @patch.dict(os.environ, {}, clear=True)
    def test_zerox_requires_api_key(self):
        with pytest.raises(MissingEnvironmentVariables):
            zerox(file_path="test.pdf")

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("zerox_sync.core.zerox.GeminiModel")
    @patch("zerox_sync.core.zerox.download_file")
    @patch("zerox_sync.core.zerox.convert_pdf_to_images")
    @patch("zerox_sync.core.zerox.process_pages_in_batches")
    def test_zerox_basic_flow(
        self,
        mock_process_pages,
        mock_convert_pdf,
        mock_download,
        mock_gemini,
    ):
        # Mock download_file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pdf") as f:
            f.write(b"fake pdf")
            temp_pdf = f.name

        mock_download.return_value = temp_pdf

        # Mock convert_pdf_to_images
        mock_convert_pdf.return_value = ["page1.png", "page2.png"]

        # Mock process_pages_in_batches
        mock_process_pages.return_value = [
            ("# Page 1\n\nContent 1", 100, 50, ""),
            ("# Page 2\n\nContent 2", 100, 50, ""),
        ]

        # Mock Gemini model
        mock_model_instance = MagicMock()
        mock_gemini.return_value = mock_model_instance

        try:
            result = zerox(file_path="test.pdf", model="gemini-3-pro")

            # File name is derived from the temp file, so just check it's not empty
            assert result.file_name != ""
            assert len(result.pages) == 2
            assert result.pages[0].content == "# Page 1\n\nContent 1"
            assert result.pages[1].content == "# Page 2\n\nContent 2"
            assert result.input_tokens == 200
            assert result.output_tokens == 100

        finally:
            if os.path.exists(temp_pdf):
                os.unlink(temp_pdf)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("zerox_sync.core.zerox.GeminiModel")
    @patch("zerox_sync.core.zerox.download_file")
    @patch("zerox_sync.core.zerox.convert_pdf_to_images")
    @patch("zerox_sync.core.zerox.process_page")
    def test_zerox_maintain_format(
        self,
        mock_process_page,
        mock_convert_pdf,
        mock_download,
        mock_gemini,
    ):
        # Mock download_file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pdf") as f:
            f.write(b"fake pdf")
            temp_pdf = f.name

        mock_download.return_value = temp_pdf

        # Mock convert_pdf_to_images
        mock_convert_pdf.return_value = ["page1.png", "page2.png"]

        # Mock process_page (called sequentially with maintain_format=True)
        mock_process_page.side_effect = [
            ("# Page 1\n\nContent 1", 100, 50, "# Page 1\n\nContent 1"),
            ("# Page 2\n\nContent 2", 200, 100, "# Page 2\n\nContent 2"),
        ]

        # Mock Gemini model
        mock_model_instance = MagicMock()
        mock_gemini.return_value = mock_model_instance

        try:
            result = zerox(
                file_path="test.pdf",
                model="gemini-3-pro",
                maintain_format=True,
            )

            assert len(result.pages) == 2
            # process_page should be called twice (once per page)
            assert mock_process_page.call_count == 2

        finally:
            if os.path.exists(temp_pdf):
                os.unlink(temp_pdf)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("zerox_sync.core.zerox.GeminiModel")
    @patch("zerox_sync.core.zerox.download_file")
    @patch("zerox_sync.core.zerox.convert_pdf_to_images")
    @patch("zerox_sync.core.zerox.process_pages_in_batches")
    @patch("zerox_sync.core.zerox.create_selected_pages_pdf")
    def test_zerox_select_pages(
        self,
        mock_create_selected,
        mock_process_pages,
        mock_convert_pdf,
        mock_download,
        mock_gemini,
    ):
        # Mock download_file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pdf") as f:
            f.write(b"fake pdf")
            temp_pdf = f.name

        mock_download.return_value = temp_pdf

        # Mock create_selected_pages_pdf
        mock_create_selected.return_value = temp_pdf

        # Mock convert_pdf_to_images
        mock_convert_pdf.return_value = ["page1.png", "page3.png"]

        # Mock process_pages_in_batches
        mock_process_pages.return_value = [
            ("# Page 1\n\nContent 1", 100, 50, ""),
            ("# Page 3\n\nContent 3", 100, 50, ""),
        ]

        # Mock Gemini model
        mock_model_instance = MagicMock()
        mock_gemini.return_value = mock_model_instance

        try:
            result = zerox(
                file_path="test.pdf",
                model="gemini-3-pro",
                select_pages=[1, 3],
            )

            assert len(result.pages) == 2
            assert result.pages[0].page == 1
            assert result.pages[1].page == 3
            # create_selected_pages_pdf should be called
            mock_create_selected.assert_called_once()

        finally:
            if os.path.exists(temp_pdf):
                os.unlink(temp_pdf)
