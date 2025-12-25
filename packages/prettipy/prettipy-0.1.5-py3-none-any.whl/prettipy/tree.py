"""
Directory tree generation for PDF documents.

This module handles generating visual directory trees using the directory-tree
package and creating clickable links from tree nodes to file pages in the PDF.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys
from io import StringIO
from directory_tree import DisplayTree
import html


class DirectoryTreeGenerator:
    """Generates directory tree representations with file-to-page mappings."""

    def __init__(self, max_depth: int = 5):
        """
        Initialize the directory tree generator.

        Args:
            max_depth: Maximum depth to display in the tree
        """
        self.max_depth = max_depth
        self.file_to_anchor: Dict[str, str] = {}

    def generate_tree_text(
        self, root_path: Path, files: List[Path], exclude_dirs: set = None
    ) -> str:
        """
        Generate the directory tree text representation.

        Args:
            root_path: Root directory path
            files: List of files to include in the PDF (for context)
            exclude_dirs: Set of directory names to exclude from tree

        Returns:
            String representation of the directory tree
        """
        if exclude_dirs is None:
            exclude_dirs = set()

        # Convert exclude_dirs to list for directory_tree
        ignore_list = list(exclude_dirs) if exclude_dirs else None

        # Capture the tree output
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            # Generate the tree
            DisplayTree(
                str(root_path), maxDepth=self.max_depth, showHidden=False, ignoreList=ignore_list
            )

            # Get the output
            sys.stdout = old_stdout
            tree_str = buffer.getvalue()

            return tree_str
        except Exception as e:
            sys.stdout = old_stdout
            # Return a simple fallback tree if directory_tree fails
            return f"Directory: {root_path.name}/\n(Tree generation failed: {str(e)})"

    def create_file_anchors(self, files: List[Path], root: Path) -> Dict[str, str]:
        """
        Create anchor names for each file.

        Args:
            files: List of file paths
            root: Root directory for relative path calculation

        Returns:
            Dictionary mapping relative file paths to anchor names
        """
        file_to_anchor = {}
        for idx, file_path in enumerate(files):
            try:
                rel_path = file_path.relative_to(root)
            except ValueError:
                rel_path = file_path

            # Create a unique anchor name for this file
            anchor_name = f"file_{idx}_{rel_path.name.replace('.', '_')}"
            file_to_anchor[str(rel_path)] = anchor_name

        return file_to_anchor

    def generate_linked_tree_html(
        self, root_path: Path, files: List[Path], exclude_dirs: set = None
    ) -> Tuple[str, Dict[str, str]]:
        """
        Generate HTML representation of the tree with clickable links.

        Args:
            root_path: Root directory path
            files: List of files included in the PDF
            exclude_dirs: Set of directory names to exclude

        Returns:
            Tuple of (HTML string, file_to_anchor mapping)
        """
        # Get the tree text
        tree_text = self.generate_tree_text(root_path, files, exclude_dirs)

        # Create anchor mappings for all files
        file_to_anchor = self.create_file_anchors(files, root_path)

        # Convert tree text to HTML with links
        html_lines = []
        for line in tree_text.split("\n"):
            if not line.strip():
                html_lines.append("")
                continue

            # Check if this line contains a file that's in our PDF
            linked = False
            for file_path in files:
                try:
                    rel_path = file_path.relative_to(root_path)
                    filename = rel_path.name

                    # If the filename appears in this line
                    if filename in line and not line.strip().endswith("/"):
                        # Get the anchor for this file
                        anchor = file_to_anchor.get(str(rel_path))
                        if anchor:
                            # Replace the filename with a linked version
                            # Use blue color for links
                            escaped_line = html.escape(line)
                            escaped_filename = html.escape(filename)
                            linked_line = escaped_line.replace(
                                escaped_filename,
                                f'<a href="#{anchor}" color="blue"><u>{escaped_filename}</u></a>',
                            )
                            html_lines.append(linked_line)
                            linked = True
                            break
                except ValueError:
                    continue

            if not linked:
                # No link needed, just escape and add
                html_lines.append(html.escape(line))

        return "<br/>".join(html_lines), file_to_anchor
