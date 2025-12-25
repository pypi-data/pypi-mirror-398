"""
Symbol tracking and linking for auto-navigation in PDFs.

This module handles tracking of function, class, and variable definitions
and creates links from references to their declarations.
"""

from typing import Dict, Set, List, Tuple
from pygments.token import Token
from pygments import lex
from pygments.lexers import PythonLexer


class SymbolTracker:
    """Tracks symbols (functions, classes, variables) for auto-linking."""

    def __init__(self):
        """Initialize the symbol tracker."""
        self.lexer = PythonLexer()
        # Maps symbol names to their types ('function', 'class', 'variable')
        self.definitions: Dict[str, str] = {}
        # Track which symbols have been marked as having anchors (for link creation)
        self.anchors_created: Set[str] = set()
        # Track which symbols have actually had anchors placed in the HTML output
        self.anchors_placed: Set[str] = set()

    def clear_anchors(self) -> None:
        """Clear the set of created anchors. Use this before processing a new document."""
        self.anchors_created.clear()
        self.anchors_placed.clear()

    def analyze_code(self, code: str) -> None:
        """
        Analyze code to find all function, class, and variable definitions.

        Args:
            code: The complete code to analyze
        """
        tokens = list(lex(code, self.lexer))

        for i, (token_type, token_value) in enumerate(tokens):
            # Look for function definitions
            if token_type in Token.Keyword and token_value == "def":
                # Next non-whitespace token should be the function name
                func_name = self._get_next_name_token(tokens, i)
                if func_name:
                    self.definitions[func_name] = "function"

            # Look for class definitions
            elif token_type in Token.Keyword and token_value == "class":
                # Next non-whitespace token should be the class name
                class_name = self._get_next_name_token(tokens, i)
                if class_name:
                    self.definitions[class_name] = "class"

            # Look for variable assignments (simple heuristic)
            elif token_type in Token.Name and i + 1 < len(tokens):
                # Skip if this is part of an import statement
                # Look backward for 'import' or 'from' keywords on the same logical line
                is_import = False
                for j in range(i - 1, max(-1, i - 10), -1):
                    # Stop at newlines (end of logical line)
                    if tokens[j][0] in Token.Text.Whitespace and "\n" in tokens[j][1]:
                        break
                    if tokens[j][0] in Token.Keyword:
                        if tokens[j][1] in ("import", "from"):
                            is_import = True
                            break
                        # If we hit another keyword, it's not an import
                        break

                if is_import:
                    continue

                # Check if next non-whitespace token is '='
                next_idx = i + 1
                while next_idx < len(tokens) and tokens[next_idx][0] in Token.Text:
                    next_idx += 1

                if next_idx < len(tokens) and tokens[next_idx][1] == "=":
                    # Don't track very common names or private names
                    if not token_value.startswith("_") and len(token_value) > 1:
                        # Only track if it's at module level or clear assignment
                        # This is a simple heuristic to avoid false positives
                        if token_value not in self.definitions:
                            self.definitions[token_value] = "variable"

    def _get_next_name_token(self, tokens: List[Tuple], start_idx: int) -> str:
        """
        Get the next name token after start_idx, skipping whitespace.

        Args:
            tokens: List of (token_type, token_value) tuples
            start_idx: Starting index

        Returns:
            The name token value, or empty string if not found
        """
        for i in range(start_idx + 1, len(tokens)):
            token_type, token_value = tokens[i]
            # Skip whitespace
            if token_type in Token.Text:
                continue
            # Return if it's a name token
            if token_type in Token.Name:
                return token_value
            # If we hit something else, stop looking
            break
        return ""

    def is_definition(self, name: str) -> bool:
        """
        Check if a name is a known definition.

        Args:
            name: Symbol name to check

        Returns:
            True if the name is a known definition
        """
        return name in self.definitions

    def should_create_anchor(self, name: str) -> bool:
        """
        Check if an anchor should be created for this symbol.

        This ensures we only create one anchor per symbol (at its first definition).

        Args:
            name: Symbol name

        Returns:
            True if anchor should be created
        """
        return name in self.definitions and name not in self.anchors_placed

    def mark_anchor_created(self, name: str) -> None:
        """
        Mark an anchor as will-be-created (for link creation).

        Args:
            name: Symbol name
        """
        self.anchors_created.add(name)

    def mark_anchor_placed(self, name: str) -> None:
        """
        Mark an anchor as actually placed in HTML output.

        Args:
            name: Symbol name
        """
        self.anchors_placed.add(name)

    def is_anchor_created(self, name: str) -> bool:
        """
        Check if an anchor has been created for this symbol.

        Args:
            name: Symbol name

        Returns:
            True if anchor has been created
        """
        return name in self.anchors_created

    def get_anchor_name(self, name: str) -> str:
        """
        Get the anchor name for a symbol, sanitizing it for use in HTML.

        Args:
            name: Symbol name

        Returns:
            Sanitized anchor name for use in HTML links
        """
        # Sanitize the name to be safe for HTML attributes
        # Replace any non-alphanumeric characters (except underscore) with underscore
        import re

        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        return f"def_{sanitized}"
