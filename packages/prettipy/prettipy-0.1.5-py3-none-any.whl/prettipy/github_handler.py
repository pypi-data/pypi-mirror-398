"""
GitHub repository handling module.

Provides functionality to clone GitHub repositories and process them.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

try:
    from git import Repo, GitCommandError, InvalidGitRepositoryError

    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    Repo = None
    GitCommandError = None
    InvalidGitRepositoryError = None


class GitHubHandlerError(Exception):
    """Base exception for GitHub handler errors."""

    pass


class GitHubHandler:
    """Handler for GitHub repository operations."""

    def __init__(self, verbose: bool = False):
        """
        Initialize GitHub handler.

        Args:
            verbose: Enable verbose output

        Raises:
            GitHubHandlerError: If GitPython is not available
        """
        if not GIT_AVAILABLE:
            raise GitHubHandlerError(
                "GitPython is not installed. Install it with: pip install gitpython"
            )
        self.verbose = verbose
        self.temp_dir: Optional[Path] = None

    def validate_github_url(self, url: str) -> bool:
        """
        Validate if the URL is a valid GitHub repository URL.

        Args:
            url: GitHub repository URL

        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            # Check for github.com domain
            if "github.com" not in parsed.netloc:
                return False
            # Check for valid path structure
            path_parts = [p for p in parsed.path.split("/") if p]
            if len(path_parts) < 2:
                return False
            return True
        except Exception:
            return False

    def clone_repository(self, repo_url: str, branch: Optional[str] = None) -> Tuple[Path, str]:
        """
        Clone a GitHub repository to a temporary directory.

        Args:
            repo_url: GitHub repository URL
            branch: Branch name to checkout (None for default branch)

        Returns:
            Tuple of (cloned directory path, actual branch name)

        Raises:
            GitHubHandlerError: If cloning fails or URL is invalid
        """
        if not self.validate_github_url(repo_url):
            raise GitHubHandlerError(f"Invalid GitHub URL: {repo_url}")

        # Create temporary directory
        try:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="prettipy_github_"))
            if self.verbose:
                print(f"Created temporary directory: {self.temp_dir}")
        except Exception as e:
            raise GitHubHandlerError(f"Failed to create temporary directory: {e}")

        # Clone repository
        try:
            if self.verbose:
                print(f"Cloning repository: {repo_url}")
                if branch:
                    print(f"Checking out branch: {branch}")

            repo = Repo.clone_from(
                repo_url,
                str(self.temp_dir),
                branch=branch,
                depth=1,  # Shallow clone for efficiency
            )

            # Get the actual active branch name
            # Try to get from active_branch, fallback to head reference
            try:
                actual_branch = repo.active_branch.name
            except (TypeError, AttributeError):
                # active_branch might be None or not have a name in some cases
                try:
                    actual_branch = repo.head.reference.name
                except (AttributeError, TypeError):
                    # Last resort fallback for detached HEAD or other edge cases
                    actual_branch = "HEAD"

            if self.verbose:
                print(f"Successfully cloned to {self.temp_dir}")
                print(f"Active branch: {actual_branch}")

            return self.temp_dir, actual_branch

        except GitCommandError as e:
            self.cleanup()
            if branch:
                raise GitHubHandlerError(
                    f"Failed to clone repository or checkout branch '{branch}': {e}"
                )
            else:
                raise GitHubHandlerError(f"Failed to clone repository: {e}")
        except Exception as e:
            self.cleanup()
            raise GitHubHandlerError(f"Unexpected error during cloning: {e}")

    def cleanup(self):
        """
        Clean up temporary directory.

        This method should be called after processing is complete.
        """
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                if self.verbose:
                    print(f"Cleaned up temporary directory: {self.temp_dir}")
                self.temp_dir = None
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Failed to clean up temporary directory: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup()
        return False
