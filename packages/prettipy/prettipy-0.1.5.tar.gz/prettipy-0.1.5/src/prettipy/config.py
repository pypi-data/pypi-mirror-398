"""
Configuration management for Prettipy.

This module handles user configuration, including file filtering,
styling options, and output preferences.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Optional
import json


@dataclass
class PrettipyConfig:
    """Configuration for PDF generation."""

    # File filtering
    exclude_dirs: Set[str] = field(
        default_factory=lambda: {
            ".git",
            ".svn",
            ".hg",
            "venv",
            "env",
            ".venv",
            ".env",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "node_modules",
            "dist",
            "build",
            ".tox",
            ".idea",
            ".vscode",
            ".DS_Store",
        }
    )
    exclude_patterns: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=lambda: ["*.py"])

    # Formatting options
    max_line_width: int = 90
    font_size: int = 9
    line_spacing: int = 14

    # PDF options
    page_size: str = "letter"  # or 'a4'
    title: Optional[str] = None
    show_line_numbers: bool = False

    # Theme
    theme: str = "default"

    # Linking
    enable_linking: bool = True

    # Directory tree
    show_directory_tree: bool = True
    directory_tree_max_depth: int = 5

    sort_method: str = "dependency"  # 'dependency', 'dependency-rev', 'lexicographic', or 'none'
    reverse_deps: bool = False  # For dependency sorting, reverse the order

    # Output
    output_file: str = "output.pdf"
    verbose: bool = False

    @classmethod
    def from_file(cls, config_path: Path) -> "PrettipyConfig":
        """
        Load configuration from a JSON file.

        Args:
            config_path: Path to the configuration file

        Returns:
            PrettipyConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        with open(config_path, "r") as f:
            data = json.load(f)

        # Convert exclude_dirs list to set if present
        if "exclude_dirs" in data:
            data["exclude_dirs"] = set(data["exclude_dirs"])

        return cls(**data)

    def to_file(self, config_path: Path):
        """
        Save configuration to a JSON file.

        Args:
            config_path: Path where to save the configuration
        """
        data = {
            "exclude_dirs": list(self.exclude_dirs),
            "exclude_patterns": self.exclude_patterns,
            "include_patterns": self.include_patterns,
            "max_line_width": self.max_line_width,
            "font_size": self.font_size,
            "line_spacing": self.line_spacing,
            "page_size": self.page_size,
            "title": self.title,
            "show_line_numbers": self.show_line_numbers,
            "theme": self.theme,
            "enable_linking": self.enable_linking,
            "show_directory_tree": self.show_directory_tree,
            "directory_tree_max_depth": self.directory_tree_max_depth,
            "sort_method": self.sort_method,
            "reverse_deps": self.reverse_deps,
            "output_file": self.output_file,
            "verbose": self.verbose,
        }

        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

    def should_exclude_path(self, path: Path) -> bool:
        """
        Check if a path should be excluded from processing.

        Args:
            path: Path to check

        Returns:
            True if path should be excluded, False otherwise
        """
        # Check if any part of the path is in excluded directories
        for part in path.parts:
            if part in self.exclude_dirs or part.startswith("."):
                return True

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if path.match(pattern):
                return True

        return False
