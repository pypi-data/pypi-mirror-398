"""
File sorting utilities for Prettipy.

This module provides different methods for sorting Python files:
1. Dependency-based sorting using a DAG and topological sort
2. Lexicographic (alphabetical) sorting
"""

import ast
from pathlib import Path
from typing import List, Dict, Set
import networkx as nx


class FileSorter:
    """Handles sorting of Python files using various strategies."""

    def __init__(self):
        """Initialize the file sorter."""
        self.dependency_graph = nx.DiGraph()

    def sort_by_lexicographic(self, files: List[Path]) -> List[Path]:
        """
        Sort files alphabetically by their full path.

        Args:
            files: List of file paths to sort

        Returns:
            Sorted list of file paths
        """
        return sorted(files, key=lambda p: str(p))

    def sort_by_dependency(self, files: List[Path], reverse: bool = False) -> List[Path]:
        """
        Sort files by dependency order using topological sort.

        Files are treated as nodes in a Directed Acyclic Graph (DAG).
        Dependencies are determined by analyzing function calls between files.
        If multiple files are at the same topological level, they are sorted
        alphabetically.

        Args:
            files: List of file paths to sort
            reverse: If True, files that use functions come first (dependents first).
                    If False, files that define functions come first (dependencies first).

        Returns:
            Sorted list of file paths in dependency order

        Raises:
            ValueError: If circular dependencies are detected
        """
        # Build the dependency graph
        self._build_dependency_graph(files, reverse=reverse)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.dependency_graph):
            cycles = list(nx.simple_cycles(self.dependency_graph))
            raise ValueError(
                f"Circular dependencies detected: {cycles}. " "Cannot perform topological sort."
            )

        # Perform topological sort with lexicographic ordering for ties
        try:
            sorted_files = list(
                nx.lexicographical_topological_sort(
                    self.dependency_graph, key=lambda node: str(node)
                )
            )
            return sorted_files
        except nx.NetworkXError as e:
            # Fallback to regular topological sort if lexicographical fails
            sorted_files = list(nx.topological_sort(self.dependency_graph))
            # Sort nodes at the same level alphabetically
            return sorted(sorted_files, key=lambda p: str(p))

    def _build_dependency_graph(self, files: List[Path], reverse: bool = False) -> None:
        """
        Build a directed graph representing file dependencies.

        A file A depends on file B if file A calls functions defined in file B.

        Args:
            files: List of file paths to analyze
            reverse: If True, reverse the edge direction (dependents come first)
        """
        self.dependency_graph.clear()

        # First pass: collect all function definitions in each file
        file_functions: Dict[Path, Set[str]] = {}
        for file_path in files:
            file_functions[file_path] = self._extract_function_definitions(file_path)
            self.dependency_graph.add_node(file_path)

        # Second pass: find function calls and create edges
        for file_path in files:
            called_functions = self._extract_function_calls(file_path)

            # For each called function, find which file defines it
            for called_func in called_functions:
                for other_file, other_funcs in file_functions.items():
                    if other_file != file_path and called_func in other_funcs:
                        # file_path depends on other_file
                        if reverse:
                            # Add edge from file_path to other_file (dependents come first)
                            self.dependency_graph.add_edge(file_path, other_file)
                        else:
                            # Add edge from other_file to file_path (dependencies come first)
                            self.dependency_graph.add_edge(other_file, file_path)

    def _extract_function_definitions(self, file_path: Path) -> Set[str]:
        """
        Extract all function and class names defined in a file.

        Args:
            file_path: Path to the Python file

        Returns:
            Set of function and class names defined in the file
        """
        definitions = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    definitions.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    definitions.add(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    definitions.add(node.name)

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            # If we can't parse the file, just skip it
            pass

        return definitions

    def _extract_function_calls(self, file_path: Path) -> Set[str]:
        """
        Extract all function and class calls from a file.

        Args:
            file_path: Path to the Python file

        Returns:
            Set of function and class names called in the file
        """
        calls = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        # For method calls like obj.method(), we might want the method name
                        # but this could be noisy, so we'll skip for now
                        pass

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            # If we can't parse the file, just skip it
            pass

        return calls


def sort_files(
    files: List[Path], method: str = "lexicographic", reverse_deps: bool = False
) -> List[Path]:
    """
    Sort files using the specified method.

    Args:
        files: List of file paths to sort
        method: Sorting method - 'dependency', 'dependency-rev', 'lexicographic', or 'none'
        reverse_deps: For dependency sorting, if True, files that use functions
                 come first (dependents first). Ignored for non-dependency methods.

    Returns:
        Sorted list of file paths

    Raises:
        ValueError: If an invalid sorting method is specified or if
                   circular dependencies are detected with dependency sorting
    """
    if method == "none":
        return list(files)  # Return a copy to prevent mutations

    sorter = FileSorter()

    if method == "lexicographic":
        return sorter.sort_by_lexicographic(files)
    elif method == "dependency":
        return sorter.sort_by_dependency(files, reverse=reverse_deps)
    elif method == "dependency-rev":
        return sorter.sort_by_dependency(files, reverse=True)
    else:
        raise ValueError(
            f"Invalid sorting method: {method}. "
            "Must be 'dependency', 'dependency-rev', 'lexicographic', or 'none'."
        )
