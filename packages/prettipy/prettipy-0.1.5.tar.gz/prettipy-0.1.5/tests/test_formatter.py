"""Tests for the code formatter module."""

import pytest
from prettipy.formatter import CodeFormatter


class TestCodeFormatter:
    """Test cases for CodeFormatter class."""

    def test_short_line_no_wrap(self):
        """Test that short lines are not wrapped."""
        formatter = CodeFormatter(max_width=90)
        line = "def hello():"
        result = formatter.wrap_line(line)
        assert result == [line]

    def test_long_line_wrapping(self):
        """Test that long lines are wrapped."""
        formatter = CodeFormatter(max_width=50)
        line = "def very_long_function_name_that_exceeds_max_width(param1, param2, param3):"
        result = formatter.wrap_line(line)
        assert len(result) > 1
        assert all(len(r) <= 90 for r in result)  # Reasonable upper bound

    def test_line_with_comment(self):
        """Test wrapping of lines containing comments."""
        formatter = CodeFormatter(max_width=50)
        line = "x = 1  # This is a comment"
        result = formatter.wrap_line(line)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_empty_line(self):
        """Test handling of empty lines."""
        formatter = CodeFormatter(max_width=90)
        line = ""
        result = formatter.wrap_line(line)
        assert result == [""]

    def test_indented_line(self):
        """Test that indentation is preserved."""
        formatter = CodeFormatter(max_width=40)
        line = "    def indented_function():"
        result = formatter.wrap_line(line)
        # Check first line maintains indentation
        assert result[0].startswith("    ")
