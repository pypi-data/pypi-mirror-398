"""Tests for the linking module."""

import pytest
from prettipy.linking import SymbolTracker


class TestSymbolTracker:
    """Test cases for SymbolTracker class."""

    def test_function_definition_tracking(self):
        """Test tracking of function definitions."""
        tracker = SymbolTracker()
        code = """
def calculate_sum(a, b):
    return a + b

def main():
    result = calculate_sum(5, 10)
"""
        tracker.analyze_code(code)

        assert tracker.is_definition("calculate_sum")
        assert tracker.is_definition("main")

    def test_class_definition_tracking(self):
        """Test tracking of class definitions."""
        tracker = SymbolTracker()
        code = """
class MyClass:
    def __init__(self):
        pass

obj = MyClass()
"""
        tracker.analyze_code(code)

        assert tracker.is_definition("MyClass")

    def test_variable_assignment_tracking(self):
        """Test tracking of variable assignments."""
        tracker = SymbolTracker()
        code = """
my_var = 42
another_var = "hello"
"""
        tracker.analyze_code(code)

        assert tracker.is_definition("my_var")
        assert tracker.is_definition("another_var")

    def test_anchor_creation_once(self):
        """Test that anchors are only created once per symbol."""
        tracker = SymbolTracker()
        code = """
def test_func():
    pass
"""
        tracker.analyze_code(code)

        # First call should return True
        assert tracker.should_create_anchor("test_func")
        tracker.mark_anchor_placed("test_func")
        # Second call should return False
        assert not tracker.should_create_anchor("test_func")

    def test_anchor_name_generation(self):
        """Test anchor name generation."""
        tracker = SymbolTracker()

        anchor_name = tracker.get_anchor_name("my_function")
        assert anchor_name == "def_my_function"

    def test_no_private_variable_tracking(self):
        """Test that private variables (starting with _) are not tracked."""
        tracker = SymbolTracker()
        code = """
_private_var = 42
__very_private = 100
"""
        tracker.analyze_code(code)

        assert not tracker.is_definition("_private_var")
        assert not tracker.is_definition("__very_private")

    def test_complex_code_tracking(self):
        """Test tracking in more complex code."""
        tracker = SymbolTracker()
        code = """
import os

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        return x + y

def main():
    calc = Calculator()
    value = calc.add(5, 10)
    print(value)

if __name__ == '__main__':
    main()
"""
        tracker.analyze_code(code)

        assert tracker.is_definition("Calculator")
        assert tracker.is_definition("main")
        assert tracker.is_definition("calc")
        assert tracker.is_definition("value")
