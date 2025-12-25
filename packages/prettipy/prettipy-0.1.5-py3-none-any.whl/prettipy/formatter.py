"""
Code formatting and line wrapping utilities.

This module handles intelligent line wrapping for Python code,
preserving comment structure and breaking at natural points.
"""

import re
from typing import List


class CodeFormatter:
    """Handles formatting and wrapping of Python code lines."""

    def __init__(self, max_width: int = 90):
        """
        Initialize the code formatter.

        Args:
            max_width: Maximum character width before wrapping (default: 90)
        """
        self.max_width = max_width
        self.break_chars = [
            ", ",
            " + ",
            " - ",
            " * ",
            " / ",
            " = ",
            " and ",
            " or ",
            " if ",
            " else ",
            " (",
            " [",
        ]

    def wrap_line(self, line: str) -> List[str]:
        """
        Wrap a long line at natural break points, preserving comment structure.

        Args:
            line: The line of code to wrap

        Returns:
            List of wrapped lines
        """
        if len(line) <= self.max_width:
            return [line]

        # Check if line has a comment
        comment_match = re.search(r"#.*", line)
        if comment_match:
            return self._wrap_line_with_comment(line, comment_match)

        # No comment - wrap at natural break points
        return self._wrap_plain_line(line)

    def _wrap_line_with_comment(self, line: str, comment_match: re.Match) -> List[str]:
        """
        Wrap a line that contains a comment.

        Args:
            line: The full line of code
            comment_match: Regex match object for the comment

        Returns:
            List of wrapped lines
        """
        code_part = line[: comment_match.start()].rstrip()
        comment_part = line[comment_match.start() :]

        # If code part fits, just wrap the comment
        if len(code_part) <= self.max_width:
            lines = [code_part]
            # Wrap comment if needed
            if len(code_part + " " + comment_part) > self.max_width:
                lines[0] = code_part + " " + comment_part[: self.max_width - len(code_part)]
                remaining = comment_part[self.max_width - len(code_part) :].lstrip()
                if remaining:
                    indent = len(line) - len(line.lstrip())
                    lines.append(" " * (indent + 4) + remaining)
            else:
                lines[0] = code_part + " " + comment_part
            return lines

        # Code part is too long, wrap it first
        return self._wrap_plain_line(line)

    def _wrap_plain_line(self, line: str) -> List[str]:
        """
        Wrap a line without comments at natural break points.

        Args:
            line: The line of code to wrap

        Returns:
            List of wrapped lines
        """
        lines = []
        current = line
        indent = len(line) - len(line.lstrip())
        continuation_indent = indent + 4

        while len(current) > self.max_width:
            # Find the best break point
            best_break = self._find_break_point(current, indent)

            if best_break == -1 or best_break <= indent:
                # No good break point found, break at max_width
                best_break = self.max_width

            lines.append(current[:best_break].rstrip())
            current = " " * continuation_indent + current[best_break:].lstrip()

        if current.strip():
            lines.append(current)

        return lines if lines else [line]

    def _find_break_point(self, line: str, min_pos: int) -> int:
        """
        Find the best position to break a line.

        Args:
            line: The line to analyze
            min_pos: Minimum position for the break (usually the indentation)

        Returns:
            Position to break at, or -1 if no good break point found
        """
        best_break = -1
        for char in self.break_chars:
            pos = line.rfind(char, 0, self.max_width)
            if pos > best_break and pos > min_pos:
                best_break = pos + len(char)
        return best_break
