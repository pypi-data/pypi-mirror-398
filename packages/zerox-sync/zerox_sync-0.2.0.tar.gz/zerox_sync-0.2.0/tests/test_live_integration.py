"""Live integration tests that make real API calls to Gemini.

These tests require GEMINI_API_KEY to be set and will make actual API calls.
They are skipped if the API key is not available.
"""
import os
import pytest
from zerox_sync import zerox


# Skip all tests in this module if GEMINI_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY environment variable not set. Skipping live API tests."
)


class TestLiveGeminiIntegration:
    """Integration tests that make real calls to the Gemini API."""

    def test_basic_pdf_processing(self):
        """Test that zerox can process a real PDF and extract text using Gemini API."""
        # Get the path to our test PDF
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        test_pdf = os.path.join(fixtures_dir, "test_document.pdf")

        # Verify the test PDF exists
        assert os.path.exists(test_pdf), f"Test PDF not found: {test_pdf}"

        # Process the PDF with zerox
        result = zerox(
            file_path=test_pdf,
            model="gemini-2.5-flash",  # Use the correct default model
        )

        # Validate the result structure
        assert result is not None, "Result should not be None"
        assert hasattr(result, 'pages'), "Result should have pages attribute"
        assert hasattr(result, 'completion_time'), "Result should have completion_time"
        assert hasattr(result, 'input_tokens'), "Result should have input_tokens"
        assert hasattr(result, 'output_tokens'), "Result should have output_tokens"

        # Validate we got at least one page
        assert len(result.pages) > 0, "Result should contain at least one page"

        # Validate the first page has content
        first_page = result.pages[0]
        assert hasattr(first_page, 'content'), "Page should have content attribute"
        assert hasattr(first_page, 'page'), "Page should have page number"
        assert first_page.content, "Page content should not be empty"

        # Validate the content contains expected text from our test PDF
        content = first_page.content.lower()

        # The OCR should recognize "test" or "document" from the image
        assert any(word in content for word in ['test', 'document', 'integration']), \
            f"Expected content not found in OCR output. Got: {first_page.content}"

        # Validate token counts are positive (actual API call was made)
        assert result.input_tokens > 0, "Input tokens should be positive"
        assert result.output_tokens > 0, "Output tokens should be positive"

        # Validate completion time is reasonable
        assert result.completion_time > 0, "Completion time should be positive"

        print(f"\n✅ Live API test passed!")
        print(f"   Pages processed: {len(result.pages)}")
        print(f"   Content length: {len(first_page.content)} chars")
        print(f"   Input tokens: {result.input_tokens}")
        print(f"   Output tokens: {result.output_tokens}")
        print(f"   Completion time: {result.completion_time:.2f}ms")
        print(f"   Content preview: {first_page.content[:100]}...")

    def test_model_name_is_valid(self):
        """Test that the default model name is valid and doesn't cause 404 errors."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        test_pdf = os.path.join(fixtures_dir, "test_document.pdf")

        # This should not raise a 404 error
        try:
            result = zerox(
                file_path=test_pdf,
                model="gemini-2.5-flash",
            )
            assert result is not None
            assert len(result.pages) > 0
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                pytest.fail(f"Got 404 error with model 'gemini-2.5-flash'. This indicates an invalid model name: {e}")
            else:
                # Re-raise other exceptions
                raise

    def test_alternate_models(self):
        """Test that alternate Gemini models work correctly."""
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        test_pdf = os.path.join(fixtures_dir, "test_document.pdf")

        # Test with gemini-2.0-flash (should also be valid)
        result = zerox(
            file_path=test_pdf,
            model="gemini-2.0-flash",
        )

        assert result is not None
        assert len(result.pages) > 0
        assert result.pages[0].content, "Content should not be empty"

        print(f"\n✅ Alternate model test passed!")
        print(f"   Model: gemini-2.0-flash")
        print(f"   Pages processed: {len(result.pages)}")
        print(f"   Content length: {len(result.pages[0].content)} chars")
