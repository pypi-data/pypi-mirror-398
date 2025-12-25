"""
Syntax highlighting for Python code.

This module handles syntax highlighting using Pygments,
converting tokens to HTML with appropriate colors.
"""

import html
from typing import List, Tuple, Dict, Optional
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token
from .linking import SymbolTracker


class SyntaxHighlighter:
    """Handles syntax highlighting for Python code."""

    # Default color scheme (GitHub-like)
    DEFAULT_COLORS = {
        Token.Keyword: "#007020",
        Token.Name.Builtin: "#007020",
        Token.Name.Function: "#06287e",
        Token.Name.Class: "#0e7c7b",
        Token.Name.Decorator: "#aa22ff",
        Token.String: "#4070a0",
        Token.Number: "#40a070",
        Token.Comment: "#60a0b0",
        Token.Comment.Single: "#60a0b0",
        Token.Comment.Multiline: "#60a0b0",
        Token.Operator: "#666666",
    }

    # Constants for token context analysis
    MAX_LOOKBACK_TOKENS = 5  # How many tokens to look back for def/class keywords
    MAX_LOOKAHEAD_TOKENS = 5  # How many tokens to look ahead for assignment operators

    def __init__(self, color_scheme: Dict = None, enable_linking: bool = True):
        """
        Initialize the syntax highlighter.

        Args:
            color_scheme: Optional custom color scheme dictionary.
                         If None, uses DEFAULT_COLORS.
            enable_linking: Whether to enable auto-linking to definitions.
        """
        self.lexer = PythonLexer()
        self.color_scheme = color_scheme or self.DEFAULT_COLORS
        self.enable_linking = enable_linking
        self.symbol_tracker: Optional[SymbolTracker] = None

    def prepare_for_linking(self, code: str, clear_existing: bool = True) -> None:
        """
        Prepare the highlighter for auto-linking by analyzing the code.

        Args:
            code: The complete code to analyze for symbols
            clear_existing: Whether to clear existing definitions
        """
        if self.enable_linking:
            if self.symbol_tracker is None or clear_existing:
                self.symbol_tracker = SymbolTracker()

            self.symbol_tracker.analyze_code(code)

    def reset_anchors(self) -> None:
        """Reset the anchor tracking to allow creating anchors in a new document."""
        if self.symbol_tracker:
            self.symbol_tracker.clear_anchors()

    def highlight_line(self, line: str) -> str:
        """
        Highlight a single line of Python code.

        Args:
            line: Line of Python code to highlight

        Returns:
            HTML string with syntax highlighting
        """
        if not line.strip():
            return "<br/>"

        tokens = list(lex(line, self.lexer))
        colored_parts = []

        for i, (token_type, token_value) in enumerate(tokens):
            colored_parts.append(self._colorize_token(token_type, token_value, tokens, i))

        return "".join(colored_parts)

    def _colorize_token(
        self, token_type: Token, token_value: str, tokens: List[Tuple] = None, token_idx: int = 0
    ) -> str:
        """
        Apply color to a single token and add linking if applicable.

        Args:
            token_type: Pygments token type
            token_value: The actual text of the token
            tokens: Complete list of tokens (for context)
            token_idx: Index of current token in tokens list

        Returns:
            HTML string with color formatting and optional linking
        """
        # Escape HTML special characters
        escaped = html.escape(token_value)
        # Preserve spaces and tabs
        escaped = escaped.replace(" ", "&nbsp;")
        escaped = escaped.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")

        # Find matching color
        color = self._get_token_color(token_type)

        # Apply linking if enabled and applicable
        if self.enable_linking and self.symbol_tracker and token_type in Token.Name:
            name = token_value.strip()
            if name and self.symbol_tracker.is_definition(name):
                # Check if this is a definition or a reference
                is_def = self._is_definition_site(tokens, token_idx)

                if is_def and self.symbol_tracker.should_create_anchor(name):
                    # This is the definition - add anchor
                    self.symbol_tracker.mark_anchor_placed(name)
                    anchor_name = self.symbol_tracker.get_anchor_name(name)
                    if color and token_value.strip():
                        return f'<a name="{anchor_name}"></a><font color="{color}">{escaped}</font>'
                    return f'<a name="{anchor_name}"></a>{escaped}'
                elif not is_def:
                    # This is a reference - add link
                    anchor_name = self.symbol_tracker.get_anchor_name(name)

                    # Only create link if the anchor has been or will be created
                    # This prevents "format not resolved" errors in ReportLab
                    if (
                        name in self.symbol_tracker.definitions
                        and self.symbol_tracker.is_anchor_created(name)
                    ):
                        if color and token_value.strip():
                            return f'<font color="{color}"><a href="#{anchor_name}">{escaped}</a></font>'
                        return f'<a href="#{anchor_name}">{escaped}</a>'

        # No linking - just apply color
        if color and token_value.strip():
            return f'<font color="{color}">{escaped}</font>'
        return escaped

    def _is_definition_site(self, tokens: List[Tuple], token_idx: int) -> bool:
        """
        Check if a name token is at a definition site.

        Args:
            tokens: List of all tokens
            token_idx: Index of the name token

        Returns:
            True if this is a definition site (def/class/assignment)
        """
        if not tokens or token_idx < 0:
            return False

        # Look backward for 'def' or 'class' keywords (only if not at start)
        if token_idx > 0:
            for i in range(token_idx - 1, max(-1, token_idx - self.MAX_LOOKBACK_TOKENS), -1):
                token_type, token_value = tokens[i]

                # Skip whitespace
                if token_type in Token.Text:
                    continue
                # Check specifically for def or class
                if token_type in Token.Keyword and token_value in ("def", "class"):
                    return True
                # If we hit a non-whitespace token that's not def/class, stop looking
                break

        # Look forward for '=' (assignment)
        for i in range(token_idx + 1, min(len(tokens), token_idx + self.MAX_LOOKAHEAD_TOKENS)):
            token_type, token_value = tokens[i]

            # Skip whitespace
            if token_type in Token.Text:
                continue
            # Check for assignment
            if token_type in Token.Operator and token_value == "=":
                return True
            # If we hit something else first, it's not an assignment
            break

        return False

    def _get_token_color(self, token_type: Token) -> str:
        """
        Get the color for a given token type.

        Args:
            token_type: Pygments token type

        Returns:
            Hex color string or None
        """
        for ttype, color in self.color_scheme.items():
            if token_type in ttype:
                return color
        return None

    def highlight_code(self, code: str, lines: List[str] = None) -> str:
        """
        Highlight an entire code block.

        Args:
            code: Full code string
            lines: Optional pre-split lines (if already processed)

        Returns:
            HTML string with all lines highlighted
        """
        if lines is None:
            lines = code.split("\n")

        highlighted_lines = [self.highlight_line(line) for line in lines]
        return "<br/>".join(highlighted_lines)

    def highlight_code_multiline_aware(self, code: str) -> List[str]:
        """
        Highlight code with proper multiline string support.

        This method processes the entire code block to correctly identify
        multiline strings and other constructs that span multiple lines,
        then returns a list of highlighted HTML strings for each line.

        Args:
            code: Full code string to highlight

        Returns:
            List of HTML strings, one per line
        """
        if not code:
            return []

        # Tokenize the entire code block
        tokens = list(lex(code, self.lexer))

        # Split code into lines to track line boundaries
        lines = code.split("\n")

        # Build highlighted HTML for each line
        highlighted_lines = [""] * len(lines)
        current_line = 0

        for token_idx, (token_type, token_value) in enumerate(tokens):
            # Split token value by newlines to handle multiline tokens
            token_lines = token_value.split("\n")

            for i, line_part in enumerate(token_lines):
                if i > 0:
                    # New line boundary
                    current_line += 1

                if current_line >= len(lines):
                    break

                if line_part:
                    # Colorize the entire line part as one unit
                    # Pass tokens and index for linking support
                    highlighted_part = self._colorize_token(
                        token_type, line_part, tokens, token_idx
                    )
                    highlighted_lines[current_line] += highlighted_part

        # Convert empty lines to <br/>
        return [line if line else "<br/>" for line in highlighted_lines]
