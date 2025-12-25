"""Tests for syntax highlighting with linking."""

import pytest
from prettipy.syntax import SyntaxHighlighter


class TestSyntaxHighlighterLinking:
    """Test cases for SyntaxHighlighter with auto-linking."""

    def test_function_definition_gets_anchor(self):
        """Test that function definitions get anchor tags."""
        highlighter = SyntaxHighlighter(enable_linking=True)
        code = """def calculate_sum(a, b):
    return a + b"""

        # Prepare for linking
        highlighter.prepare_for_linking(code)

        # Highlight the definition line
        result = highlighter.highlight_line("def calculate_sum(a, b):")

        # Should contain an anchor tag
        assert '<a name="def_calculate_sum"></a>' in result
        assert "calculate_sum" in result

    def test_function_call_gets_link(self):
        """Test that function calls get link tags."""
        highlighter = SyntaxHighlighter(enable_linking=True)
        code = """def calculate_sum(a, b):
    return a + b

result = calculate_sum(5, 10)"""

        # Prepare for linking
        highlighter.prepare_for_linking(code)

        # Mark that the anchor will be created (simulate pre-marking phase)
        highlighter.symbol_tracker.mark_anchor_created("calculate_sum")

        # Highlight the definition line first (to create anchor)
        highlighter.highlight_line("def calculate_sum(a, b):")

        # Highlight the call line
        result = highlighter.highlight_line("result = calculate_sum(5, 10)")

        # Should contain a link tag
        assert '<a href="#def_calculate_sum">' in result

    def test_class_definition_gets_anchor(self):
        """Test that class definitions get anchor tags."""
        highlighter = SyntaxHighlighter(enable_linking=True)
        code = """class MyClass:
    pass

obj = MyClass()"""

        # Prepare for linking
        highlighter.prepare_for_linking(code)

        # Highlight the definition line
        result = highlighter.highlight_line("class MyClass:")

        # Should contain an anchor tag
        assert '<a name="def_MyClass"></a>' in result

    def test_variable_assignment_gets_anchor(self):
        """Test that variable assignments get anchor tags."""
        highlighter = SyntaxHighlighter(enable_linking=True)
        code = """my_var = 42
print(my_var)"""

        # Prepare for linking
        highlighter.prepare_for_linking(code)

        # Highlight the assignment line
        result = highlighter.highlight_line("my_var = 42")

        # Should contain an anchor tag
        assert '<a name="def_my_var"></a>' in result

    def test_linking_disabled(self):
        """Test that linking can be disabled."""
        highlighter = SyntaxHighlighter(enable_linking=False)
        code = """def test_func():
    pass"""

        # Don't prepare for linking
        result = highlighter.highlight_line("def test_func():")

        # Should not contain anchor or link tags
        assert "<a name=" not in result
        assert "<a href=" not in result

    def test_preserves_syntax_highlighting(self):
        """Test that linking preserves syntax highlighting."""
        highlighter = SyntaxHighlighter(enable_linking=True)
        code = """def my_function():
    return 42"""

        highlighter.prepare_for_linking(code)
        result = highlighter.highlight_line("def my_function():")

        # Should still have color tags
        assert "<font color=" in result
        # And should have anchor
        assert '<a name="def_my_function"></a>' in result

    def test_no_false_positives_in_strings(self):
        """Test that function names in strings are not linked."""
        highlighter = SyntaxHighlighter(enable_linking=True)
        code = """def hello():
    pass

msg = "hello world" """

        highlighter.prepare_for_linking(code)

        # Highlight the definition
        highlighter.highlight_line("def hello():")

        # Highlight the string line - "hello" in string should not be linked
        result = highlighter.highlight_line('msg = "hello world"')

        # The word "hello" in the string should not have a link
        # (Pygments will tokenize it as String, not Name)
        # So there should be no href to hello in this line
        assert result.count('<a href="#def_hello">') == 0
