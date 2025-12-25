"""
Command-line interface for Prettipy.

Provides a beautiful, user-friendly CLI with progress bars and rich formatting.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

from . import __version__
from .config import PrettipyConfig
from .core import PrettipyConverter
from .github_handler import GitHubHandler, GitHubHandlerError


class CLI:
    """Command-line interface handler."""

    def __init__(self):
        """Initialize CLI."""
        self.console = Console() if RICH_AVAILABLE else None
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Create and configure argument parser.

        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            prog="prettipy",
            description="Convert Python code to beautifully formatted PDFs",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  prettipy                             # Convert current directory
  prettipy /path/to/project            # Convert specific directory
  prettipy -o output.pdf               # Specify output file
  prettipy -f file1.py file2.py        # Convert specific files
  prettipy -w 100                      # Set max line width to 100
  prettipy --config my-config.json     # Use custom configuration
  prettipy --sort dependency           # Sort files by dependencies
  prettipy --sort lexicographic        # Sort files alphabetically
  prettipy --sort none                 # No sorting (discovery order)
  prettipy --gh https://github.com/user/repo  # Clone and convert GitHub repo
  prettipy --github https://github.com/user/repo -b dev  # Clone specific branch

For more information, visit: https://github.com/yourusername/prettipy
            """,
        )

        parser.add_argument(
            "directory",
            nargs="?",
            default=".",
            help="Directory to scan for Python files (default: current directory)",
        )

        parser.add_argument(
            "-o",
            "--output",
            default="output.pdf",
            help="Output PDF file path (default: output.pdf)",
        )

        parser.add_argument("-f", "--files", nargs="+", help="Specific Python files to convert")

        parser.add_argument(
            "-w",
            "--width",
            type=int,
            default=90,
            help="Maximum line width before wrapping (default: 90)",
        )

        parser.add_argument("--config", type=Path, help="Path to configuration JSON file")

        parser.add_argument("-t", "--title", help="Custom title for the PDF document")

        parser.add_argument(
            "--theme",
            choices=["default"],
            default="default",
            help="Color theme to use (default: default)",
        )

        parser.add_argument(
            "--page-size",
            choices=["letter", "a4"],
            default="letter",
            help="PDF page size (default: letter)",
        )

        parser.add_argument(
            "--no-linking",
            action="store_true",
            help="Disable auto-linking to function/variable definitions",
        )

        parser.add_argument(
            "--show-tree",
            action="store_true",
            help="Show directory tree structure on the first page with clickable links to files",
        )

        parser.add_argument(
            "--no-tree", action="store_true", help="Hide the directory tree on the first page"
        )

        parser.add_argument(
            "--tree-depth",
            type=int,
            default=5,
            help="Maximum depth for directory tree display (default: 5)",
        )

        parser.add_argument(
            "--sort",
            choices=["dependency", "dependency-rev", "lexicographic", "none"],
            default="dependency",
            help="File sorting method: dependency (providers first), dependency-rev "
            "(dependents first), lexicographic (alphabetical), or none "
            "(default: dependency)",
        )

        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

        parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

        parser.add_argument(
            "--init-config", action="store_true", help="Generate a sample configuration file"
        )

        parser.add_argument(
            "--github",
            "--gh",
            dest="github_url",
            help="Clone and convert a GitHub repository (e.g., https://github.com/user/repo)",
        )

        parser.add_argument(
            "--branch",
            "-b",
            dest="github_branch",
            help="Branch to checkout when cloning GitHub repository (default: repository's default branch)",
        )

        return parser

    def _print_header(self):
        """Print application header."""
        if RICH_AVAILABLE and self.console:
            self.console.print(
                Panel.fit(
                    "[bold cyan]Prettipy[/bold cyan] - Python Code to PDF Converter",
                    subtitle=f"v{__version__}",
                )
            )
        else:
            print(f"\n{'='*60}")
            print(f"Prettipy v{__version__} - Python Code to PDF Converter")
            print(f"{'='*60}\n")

    def _print_success(self, message: str):
        """Print success message."""
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[bold green]✓[/bold green] {message}")
        else:
            print(f"✓ {message}")

    def _print_error(self, message: str):
        """Print error message."""
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[bold red]✗[/bold red] {message}")
        else:
            print(f"✗ {message}", file=sys.stderr)

    def _print_info(self, message: str):
        """Print info message."""
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[cyan]ℹ[/cyan] {message}")
        else:
            print(f"ℹ {message}")

    def _init_config(self, output_path: str = "prettipy-config.json"):
        """
        Generate a sample configuration file.

        Args:
            output_path: Where to save the config file
        """
        config = PrettipyConfig()
        config.to_file(Path(output_path))
        self._print_success(f"Created sample configuration file: {output_path}")
        self._print_info("Edit this file and use with: prettipy --config {output_path}")

    def run(self, argv: Optional[list] = None):
        """
        Run the CLI application.

        Args:
            argv: Command-line arguments (default: sys.argv[1:])

        Returns:
            Exit code (0 for success, 1 for error)
        """
        args = self.parser.parse_args(argv)

        # Handle --init-config
        if args.init_config:
            self._init_config()
            return 0

        # Validate conflicting arguments
        if args.github_url and args.files:
            self._print_error(
                "Cannot use --github with --files. "
                "GitHub mode converts the entire cloned repository."
            )
            return 1

        self._print_header()

        # Load configuration
        try:
            if args.config:
                config = PrettipyConfig.from_file(args.config)
                self._print_info(f"Loaded configuration from {args.config}")
            else:
                config = PrettipyConfig()

            # Override with command-line arguments
            config.output_file = args.output
            config.max_line_width = args.width
            config.verbose = args.verbose
            config.theme = args.theme
            config.page_size = args.page_size
            config.sort_method = args.sort
            # Preserve reverse_deps for compatibility; dependency-rev implies reverse
            config.reverse_deps = (
                getattr(args, "reverse_deps", False) or args.sort == "dependency-rev"
            )

            if args.no_linking:
                config.enable_linking = False

            if args.show_tree:
                config.show_directory_tree = True

            if getattr(args, "no_tree", False):
                config.show_directory_tree = False

            if hasattr(args, "tree_depth"):
                config.directory_tree_max_depth = args.tree_depth

            if args.title:
                config.title = args.title

        except Exception as e:
            self._print_error(f"Configuration error: {e}")
            return 1

        # Create converter
        converter = PrettipyConverter(config)

        # Handle GitHub repository cloning
        github_handler = None
        target_directory = args.directory

        if args.github_url:
            try:
                github_handler = GitHubHandler(verbose=config.verbose)
                self._print_info(f"Cloning GitHub repository: {args.github_url}")

                if args.github_branch:
                    self._print_info(f"Checking out branch: {args.github_branch}")

                cloned_path, branch = github_handler.clone_repository(
                    args.github_url, args.github_branch
                )
                target_directory = str(cloned_path)

                self._print_success(f"Successfully cloned repository (branch: {branch})")

            except GitHubHandlerError as e:
                self._print_error(str(e))
                return 1
            except Exception as e:
                self._print_error(f"Unexpected error while cloning repository: {e}")
                return 1

        # Convert files
        try:
            if RICH_AVAILABLE and self.console:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task("Converting Python files...", total=None)

                    if args.files:
                        converter.convert_files(args.files, args.output)
                    else:
                        converter.convert_directory(target_directory, args.output)

                    progress.update(task, completed=True)
            else:
                # Fallback without rich
                if args.files:
                    converter.convert_files(args.files, args.output)
                else:
                    converter.convert_directory(target_directory, args.output)

            return 0

        except FileNotFoundError as e:
            self._print_error(str(e))
            return 1
        except PermissionError as e:
            self._print_error(f"Permission denied: {e}")
            return 1
        except Exception as e:
            self._print_error(f"An error occurred: {e}")
            if config.verbose:
                import traceback

                traceback.print_exc()
            return 1
        finally:
            # Always clean up GitHub temporary directory
            if github_handler:
                github_handler.cleanup()


def main():
    """Main entry point for the CLI."""
    cli = CLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
