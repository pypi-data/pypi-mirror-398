"""Tests for package metadata and configuration."""

import os
import sys
from pathlib import Path

import pytest


class TestPackageMetadata:
    """Tests for package metadata and imports."""

    def test_package_imports(self):
        """Test that main package imports correctly."""
        import zerox_sync

        assert hasattr(zerox_sync, "zerox")
        assert hasattr(zerox_sync, "Prompts")
        assert hasattr(zerox_sync, "DEFAULT_SYSTEM_PROMPT")

    def test_package_version(self):
        """Test that package has a version."""
        import zerox_sync

        assert hasattr(zerox_sync, "__version__")
        assert isinstance(zerox_sync.__version__, str)
        assert len(zerox_sync.__version__) > 0

    def test_package_exports(self):
        """Test that __all__ is correctly defined."""
        import zerox_sync

        assert hasattr(zerox_sync, "__all__")
        assert "zerox" in zerox_sync.__all__
        assert "Prompts" in zerox_sync.__all__
        assert "DEFAULT_SYSTEM_PROMPT" in zerox_sync.__all__

    def test_zerox_function_callable(self):
        """Test that zerox function is callable."""
        from zerox_sync import zerox

        assert callable(zerox)

    def test_prompts_class_available(self):
        """Test that Prompts class is available."""
        from zerox_sync import Prompts

        assert hasattr(Prompts, "DEFAULT_SYSTEM_PROMPT")
        assert isinstance(Prompts.DEFAULT_SYSTEM_PROMPT, str)

    def test_default_system_prompt_available(self):
        """Test that DEFAULT_SYSTEM_PROMPT is available."""
        from zerox_sync import DEFAULT_SYSTEM_PROMPT

        assert isinstance(DEFAULT_SYSTEM_PROMPT, str)
        assert len(DEFAULT_SYSTEM_PROMPT) > 0


class TestPythonVersionCompatibility:
    """Tests for Python version compatibility."""

    def test_python_version_minimum(self):
        """Test that Python version meets minimum requirement."""
        # Package requires Python 3.9+
        assert sys.version_info >= (3, 9), f"Python 3.9+ required, got {sys.version}"

    def test_python_version_file_exists(self):
        """Test that .python-version file exists."""
        repo_root = Path(__file__).parent.parent
        python_version_file = repo_root / ".python-version"

        assert python_version_file.exists(), ".python-version file should exist for uv"

    def test_python_version_file_content(self):
        """Test that .python-version file has valid content."""
        repo_root = Path(__file__).parent.parent
        python_version_file = repo_root / ".python-version"

        if python_version_file.exists():
            content = python_version_file.read_text().strip()
            assert content, ".python-version should not be empty"
            # Should be a version number like "3.9" or "3.11"
            assert content[0].isdigit(), ".python-version should start with a digit"


class TestProjectStructure:
    """Tests for project structure and configuration files."""

    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists."""
        repo_root = Path(__file__).parent.parent
        pyproject = repo_root / "pyproject.toml"

        assert pyproject.exists(), "pyproject.toml should exist"

    def test_readme_exists(self):
        """Test that README.md exists."""
        repo_root = Path(__file__).parent.parent
        readme = repo_root / "README.md"

        assert readme.exists(), "README.md should exist"

    def test_license_exists(self):
        """Test that LICENSE file exists."""
        repo_root = Path(__file__).parent.parent
        license_file = repo_root / "LICENSE"

        assert license_file.exists(), "LICENSE file should exist"

    def test_gitignore_exists(self):
        """Test that .gitignore exists."""
        repo_root = Path(__file__).parent.parent
        gitignore = repo_root / ".gitignore"

        assert gitignore.exists(), ".gitignore should exist"

    def test_example_file_exists(self):
        """Test that example.py exists."""
        repo_root = Path(__file__).parent.parent
        example = repo_root / "example.py"

        assert example.exists(), "example.py should exist"

    def test_uv_documentation_exists(self):
        """Test that UV.md documentation exists."""
        repo_root = Path(__file__).parent.parent
        uv_doc = repo_root / "UV.md"

        assert uv_doc.exists(), "UV.md should exist for uv users"

    def test_claude_documentation_exists(self):
        """Test that CLAUDE.md documentation exists."""
        repo_root = Path(__file__).parent.parent
        claude_doc = repo_root / "CLAUDE.md"

        assert claude_doc.exists(), "CLAUDE.md should exist for AI-assisted development"


class TestModuleImports:
    """Tests for all module imports."""

    def test_core_module_imports(self):
        """Test that core modules import correctly."""
        from zerox_sync.core import zerox, Page, ZeroxOutput

        assert callable(zerox)
        assert Page is not None
        assert ZeroxOutput is not None

    def test_models_module_imports(self):
        """Test that models module imports correctly."""
        from zerox_sync.models import GeminiModel

        assert GeminiModel is not None

    def test_processor_module_imports(self):
        """Test that processor modules import correctly."""
        from zerox_sync.processor import (
            convert_pdf_to_images,
            process_page,
            process_pages_in_batches,
            download_file,
            is_valid_url,
            create_selected_pages_pdf,
            encode_image_to_base64,
            format_markdown,
        )

        assert callable(convert_pdf_to_images)
        assert callable(process_page)
        assert callable(process_pages_in_batches)
        assert callable(download_file)
        assert callable(is_valid_url)
        assert callable(create_selected_pages_pdf)
        assert callable(encode_image_to_base64)
        assert callable(format_markdown)

    def test_constants_module_imports(self):
        """Test that constants modules import correctly."""
        from zerox_sync.constants import Prompts, PDFConversionDefaultOptions, Messages

        assert Prompts is not None
        assert PDFConversionDefaultOptions is not None
        assert Messages is not None

    def test_errors_module_imports(self):
        """Test that error modules import correctly."""
        from zerox_sync.errors import (
            ZeroxError,
            FileUnavailable,
            ResourceUnreachableException,
            PageNumberOutOfBoundError,
            MissingEnvironmentVariables,
            NotAVisionModel,
            ModelAccessError,
        )

        assert ZeroxError is not None
        assert FileUnavailable is not None
        assert ResourceUnreachableException is not None
        assert PageNumberOutOfBoundError is not None
        assert MissingEnvironmentVariables is not None
        assert NotAVisionModel is not None
        assert ModelAccessError is not None
