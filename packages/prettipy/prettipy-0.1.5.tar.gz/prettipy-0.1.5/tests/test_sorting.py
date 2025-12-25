"""Tests for the sorting module."""

import pytest
from pathlib import Path
from prettipy.sorting import FileSorter, sort_files


class TestFileSorter:
    """Test cases for FileSorter class."""

    def test_sort_by_lexicographic(self, tmp_path):
        """Test lexicographic (alphabetical) sorting."""
        # Create test files with names out of order
        file_c = tmp_path / "c_file.py"
        file_a = tmp_path / "a_file.py"
        file_b = tmp_path / "b_file.py"

        for f in [file_c, file_a, file_b]:
            f.write_text("print('hello')")

        files = [file_c, file_a, file_b]
        sorter = FileSorter()
        sorted_files = sorter.sort_by_lexicographic(files)

        # Should be sorted alphabetically
        assert sorted_files == [file_a, file_b, file_c]

    def test_sort_by_dependency_no_dependencies(self, tmp_path):
        """Test dependency sorting with files that have no dependencies."""
        file_a = tmp_path / "a_file.py"
        file_b = tmp_path / "b_file.py"

        file_a.write_text("def func_a(): pass")
        file_b.write_text("def func_b(): pass")

        files = [file_b, file_a]
        sorter = FileSorter()
        sorted_files = sorter.sort_by_dependency(files)

        # Should be sorted alphabetically when no dependencies
        assert sorted_files == [file_a, file_b]

    def test_sort_by_dependency_simple_chain(self, tmp_path):
        """Test dependency sorting with a simple dependency chain."""
        file_a = tmp_path / "a_module.py"
        file_b = tmp_path / "b_module.py"

        # file_a defines a function
        file_a.write_text(
            """
def helper_function():
    return 42
"""
        )

        # file_b calls the function from file_a
        file_b.write_text(
            """
def main():
    result = helper_function()
    return result
"""
        )

        files = [file_b, file_a]
        sorter = FileSorter()
        sorted_files = sorter.sort_by_dependency(files)

        # file_a should come before file_b (b depends on a)
        assert sorted_files[0] == file_a
        assert sorted_files[1] == file_b

    def test_sort_by_dependency_multiple_files(self, tmp_path):
        """Test dependency sorting with multiple files and dependencies."""
        file_utils = tmp_path / "utils.py"
        file_models = tmp_path / "models.py"
        file_main = tmp_path / "main.py"

        # utils defines helper functions
        file_utils.write_text(
            """
def format_string(s):
    return s.upper()
"""
        )

        # models uses utils
        file_models.write_text(
            """
class User:
    def __init__(self, name):
        self.name = format_string(name)
"""
        )

        # main uses both
        file_main.write_text(
            """
def run():
    user = User("alice")
    return format_string(user.name)
"""
        )

        files = [file_main, file_models, file_utils]
        sorter = FileSorter()
        sorted_files = sorter.sort_by_dependency(files)

        # utils should come first, then models, then main
        assert sorted_files.index(file_utils) < sorted_files.index(file_models)
        assert sorted_files.index(file_models) < sorted_files.index(file_main)

    def test_sort_by_dependency_circular_dependency(self, tmp_path):
        """Test that circular dependencies raise an error."""
        file_a = tmp_path / "a_module.py"
        file_b = tmp_path / "b_module.py"

        # file_a calls function from file_b
        file_a.write_text(
            """
def func_a():
    return func_b()
"""
        )

        # file_b calls function from file_a (circular dependency)
        file_b.write_text(
            """
def func_b():
    return func_a()
"""
        )

        files = [file_a, file_b]
        sorter = FileSorter()

        with pytest.raises(ValueError, match="Circular dependencies detected"):
            sorter.sort_by_dependency(files)

    def test_extract_function_definitions(self, tmp_path):
        """Test extraction of function and class definitions."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """
def function_one():
    pass

class MyClass:
    def method(self):
        pass

async def async_function():
    pass
"""
        )

        sorter = FileSorter()
        definitions = sorter._extract_function_definitions(test_file)

        assert "function_one" in definitions
        assert "MyClass" in definitions
        assert "async_function" in definitions
        # Note: methods are also extracted as they might be called externally
        assert "method" in definitions

    def test_extract_function_calls(self, tmp_path):
        """Test extraction of function calls."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """
def main():
    result = helper_function()
    obj = MyClass()
    return result
"""
        )

        sorter = FileSorter()
        calls = sorter._extract_function_calls(test_file)

        assert "helper_function" in calls
        assert "MyClass" in calls

    def test_extract_handles_syntax_errors(self, tmp_path):
        """Test that extraction handles files with syntax errors gracefully."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text(
            """
def incomplete_function(
    # Missing closing parenthesis and body
"""
        )

        sorter = FileSorter()

        # Should not raise an error, just return empty set
        definitions = sorter._extract_function_definitions(bad_file)
        assert definitions == set()

        calls = sorter._extract_function_calls(bad_file)
        assert calls == set()


class TestSortFilesFunction:
    """Test cases for the sort_files convenience function."""

    def test_sort_files_lexicographic(self, tmp_path):
        """Test sort_files with lexicographic method."""
        file_c = tmp_path / "c.py"
        file_a = tmp_path / "a.py"
        file_b = tmp_path / "b.py"

        for f in [file_c, file_a, file_b]:
            f.write_text("pass")

        files = [file_c, file_a, file_b]
        sorted_files = sort_files(files, method="lexicographic")

        assert sorted_files == [file_a, file_b, file_c]

    def test_sort_files_none(self, tmp_path):
        """Test sort_files with none method (no sorting)."""
        file_c = tmp_path / "c.py"
        file_a = tmp_path / "a.py"
        file_b = tmp_path / "b.py"

        for f in [file_c, file_a, file_b]:
            f.write_text("pass")

        files = [file_c, file_a, file_b]
        sorted_files = sort_files(files, method="none")

        # Should maintain original order
        assert sorted_files == files

    def test_sort_files_dependency(self, tmp_path):
        """Test sort_files with dependency method."""
        file_a = tmp_path / "a.py"
        file_b = tmp_path / "b.py"

        file_a.write_text("def func_a(): pass")
        file_b.write_text("def func_b():\n    func_a()")

        files = [file_b, file_a]
        sorted_files = sort_files(files, method="dependency")

        assert sorted_files[0] == file_a
        assert sorted_files[1] == file_b

    def test_sort_files_invalid_method(self, tmp_path):
        """Test sort_files with an invalid method."""
        file_a = tmp_path / "a.py"
        file_a.write_text("pass")

        files = [file_a]

        with pytest.raises(ValueError, match="Invalid sorting method"):
            sort_files(files, method="invalid")
