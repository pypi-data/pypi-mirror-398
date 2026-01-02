"""Tests to verify pypdf migration from PyPDF2."""

import pytest


class TestPyPDFMigration:
    """Tests to ensure pypdf is used instead of deprecated PyPDF2."""

    def test_pypdf_is_importable(self):
        """Test that pypdf can be imported."""
        try:
            import pypdf
            assert pypdf is not None
        except ImportError:
            pytest.fail("pypdf is not installed")

    def test_pypdf2_not_imported_in_utils(self):
        """Test that utils.py uses pypdf, not PyPDF2."""
        import zerox_sync.processor.utils as utils
        import inspect

        source = inspect.getsource(utils)
        assert "from pypdf import" in source, "utils.py should import from pypdf"
        assert "from PyPDF2 import" not in source, "utils.py should not import from PyPDF2"

    def test_pypdf_classes_available(self):
        """Test that pypdf classes are available in utils."""
        from zerox_sync.processor.utils import PdfReader, PdfWriter

        assert PdfReader is not None
        assert PdfWriter is not None

    def test_pypdf_reader_functionality(self):
        """Test that PdfReader works correctly."""
        from pypdf import PdfReader
        import tempfile
        import os

        # Create a minimal PDF
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
190
%%EOF"""

        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pdf") as f:
            f.write(pdf_content)
            temp_path = f.name

        try:
            reader = PdfReader(temp_path)
            assert len(reader.pages) == 1, "Should have 1 page"
        finally:
            os.unlink(temp_path)

    def test_no_pypdf2_deprecation_warning(self):
        """Test that importing the module doesn't raise PyPDF2 warnings."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Import the module that uses PDF library
            import zerox_sync.processor.utils

            # Check no PyPDF2 deprecation warnings
            pypdf2_warnings = [warning for warning in w if "PyPDF2" in str(warning.message)]
            assert len(pypdf2_warnings) == 0, "Should not have PyPDF2 deprecation warnings"

    def test_create_selected_pages_pdf_works_with_pypdf(self):
        """Test that create_selected_pages_pdf works with pypdf."""
        from zerox_sync.processor.utils import create_selected_pages_pdf
        from pypdf import PdfReader, PdfWriter
        import tempfile
        import os

        # Create a simple 2-page PDF
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R 4 0 R]
/Count 2
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
4 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000123 00000 n
0000000196 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
269
%%EOF"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source PDF
            source_pdf = os.path.join(temp_dir, "source.pdf")
            with open(source_pdf, "wb") as f:
                f.write(pdf_content)

            # This should work with pypdf
            result = create_selected_pages_pdf(
                original_pdf_path=source_pdf,
                select_pages=[1],
                save_directory=temp_dir,
            )

            assert os.path.exists(result), "Selected pages PDF should be created"

            # Verify it has 1 page
            reader = PdfReader(result)
            assert len(reader.pages) == 1, "Should have 1 page"
