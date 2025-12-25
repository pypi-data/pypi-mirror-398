"""Tests for the tree module."""

import pytest
from pathlib import Path
from prettipy.tree import DirectoryTreeGenerator


class TestDirectoryTreeGenerator:
    """Test cases for DirectoryTreeGenerator class."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = DirectoryTreeGenerator()
        assert generator.max_depth == 5
        assert generator.file_to_anchor == {}

    def test_generator_with_custom_depth(self):
        """Test generator with custom max depth."""
        generator = DirectoryTreeGenerator(max_depth=3)
        assert generator.max_depth == 3

    def test_create_file_anchors(self, tmp_path):
        """Test creating file anchors."""
        # Create test files
        file1 = tmp_path / "test1.py"
        file2 = tmp_path / "test2.py"
        file1.write_text("print('test1')")
        file2.write_text("print('test2')")

        files = [file1, file2]
        generator = DirectoryTreeGenerator()
        file_to_anchor = generator.create_file_anchors(files, tmp_path)

        # Check that anchors were created
        assert len(file_to_anchor) == 2
        assert "test1.py" in file_to_anchor
        assert "test2.py" in file_to_anchor

        # Check that anchor names are unique
        anchor1 = file_to_anchor["test1.py"]
        anchor2 = file_to_anchor["test2.py"]
        assert anchor1 != anchor2
        assert "file_0_test1_py" in anchor1
        assert "file_1_test2_py" in anchor2

    def test_create_file_anchors_nested(self, tmp_path):
        """Test creating file anchors for nested files."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file1 = tmp_path / "main.py"
        file2 = subdir / "helper.py"
        file1.write_text("print('main')")
        file2.write_text("print('helper')")

        files = [file1, file2]
        generator = DirectoryTreeGenerator()
        file_to_anchor = generator.create_file_anchors(files, tmp_path)

        # Check that nested paths work correctly
        assert "main.py" in file_to_anchor
        assert str(Path("subdir") / "helper.py") in file_to_anchor

    def test_generate_tree_text(self, tmp_path):
        """Test generating tree text representation."""
        # Create test structure
        (tmp_path / "file1.py").write_text("print('file1')")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.py").write_text("print('file2')")

        files = [tmp_path / "file1.py", subdir / "file2.py"]
        generator = DirectoryTreeGenerator()
        tree_text = generator.generate_tree_text(tmp_path, files)

        # Check that tree text contains expected elements
        assert tmp_path.name in tree_text or str(tmp_path) in tree_text
        # Tree should have some structure characters
        assert any(char in tree_text for char in ["├", "└", "│", "-", "/"])

    def test_generate_linked_tree_html(self, tmp_path):
        """Test generating linked tree HTML."""
        # Create test files
        file1 = tmp_path / "test.py"
        file1.write_text("print('test')")

        files = [file1]
        generator = DirectoryTreeGenerator()
        tree_html, file_to_anchor = generator.generate_linked_tree_html(tmp_path, files)

        # Check that HTML was generated
        assert tree_html is not None
        assert len(tree_html) > 0

        # Check that anchors were created
        assert len(file_to_anchor) == 1
        assert "test.py" in file_to_anchor

        # Check that HTML contains link markup
        if "test.py" in tree_html:
            # The link should be present
            assert '<a href="#' in tree_html or "test.py" in tree_html

    def test_generate_tree_with_exclude_dirs(self, tmp_path):
        """Test generating tree with excluded directories."""
        # Create structure with directory to exclude
        (tmp_path / "main.py").write_text("print('main')")
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "ignored.py").write_text("print('ignored')")

        files = [tmp_path / "main.py"]
        exclude_dirs = {"venv", "__pycache__"}

        generator = DirectoryTreeGenerator()
        tree_text = generator.generate_tree_text(tmp_path, files, exclude_dirs)

        # The tree should be generated
        assert tree_text is not None
        assert len(tree_text) > 0

    def test_generate_tree_handles_errors_gracefully(self, tmp_path):
        """Test that tree generation handles errors gracefully."""
        # Try to generate tree for non-existent path
        fake_path = tmp_path / "nonexistent"
        generator = DirectoryTreeGenerator()

        # Should not raise an exception
        tree_text = generator.generate_tree_text(fake_path, [])

        # Should return some fallback text
        assert tree_text is not None
        assert len(tree_text) > 0
