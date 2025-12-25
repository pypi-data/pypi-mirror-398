"""Tests for the core module."""

import pytest
from pathlib import Path
from prettipy.core import PrettipyConverter
from prettipy.config import PrettipyConfig


class TestPrettipyConverter:
    """Test cases for PrettipyConverter class."""

    def test_converter_initialization(self):
        """Test converter initialization."""
        converter = PrettipyConverter()
        assert converter.config is not None
        assert converter.formatter is not None
        assert converter.highlighter is not None

    def test_converter_with_custom_config(self):
        """Test converter with custom configuration."""
        config = PrettipyConfig(max_line_width=100)
        converter = PrettipyConverter(config)
        assert converter.config.max_line_width == 100
        assert converter.formatter.max_width == 100

    def test_find_python_files(self, tmp_path):
        """Test finding Python files in directory."""
        # Create test structure
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def util(): pass")
        (tmp_path / "README.md").write_text("# Readme")

        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "ignored.py").write_text("# should be ignored")

        converter = PrettipyConverter()
        files = converter.find_python_files(tmp_path)

        # Should find only main.py and utils.py, not the one in venv
        assert len(files) == 2
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "ignored.py" not in file_names

    def test_convert_directory_creates_pdf(self, tmp_path):
        """Test that convert_directory creates a PDF file."""
        # Create a test Python file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('Hello, World!')")

        output_pdf = tmp_path / "output.pdf"

        converter = PrettipyConverter()
        converter.convert_directory(str(tmp_path), str(output_pdf))

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

    def test_convert_nonexistent_directory(self):
        """Test that converting nonexistent directory raises error."""
        converter = PrettipyConverter()

        with pytest.raises(FileNotFoundError):
            converter.convert_directory("/nonexistent/path")

    def test_convert_specific_files(self, tmp_path):
        """Test converting specific files."""
        # Create test files
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("x = 1")
        file2.write_text("y = 2")

        output_pdf = tmp_path / "output.pdf"

        converter = PrettipyConverter()
        converter.convert_files([str(file1), str(file2)], str(output_pdf))

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

    def test_convert_directory_with_tree(self, tmp_path):
        """Test that convert_directory creates a PDF with directory tree."""
        # Create test files
        (tmp_path / "main.py").write_text("print('main')")
        subdir = tmp_path / "utils"
        subdir.mkdir()
        (subdir / "helper.py").write_text("def helper(): pass")

        output_pdf = tmp_path / "output_with_tree.pdf"

        config = PrettipyConfig(show_directory_tree=True)
        converter = PrettipyConverter(config)
        converter.convert_directory(str(tmp_path), str(output_pdf))

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

    def test_convert_directory_tree_depth(self, tmp_path):
        """Test directory tree with custom depth."""
        # Create test files
        (tmp_path / "main.py").write_text("print('main')")

        output_pdf = tmp_path / "output_tree_depth.pdf"

        config = PrettipyConfig(show_directory_tree=True, directory_tree_max_depth=2)
        converter = PrettipyConverter(config)
        converter.convert_directory(str(tmp_path), str(output_pdf))

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
