"""Tests for the GitHub handler module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from prettipy.github_handler import GitHubHandler, GitHubHandlerError


class TestGitHubHandler:
    """Test cases for GitHubHandler class."""

    def test_handler_initialization(self):
        """Test handler initialization."""
        handler = GitHubHandler()
        assert handler.verbose is False
        assert handler.temp_dir is None

    def test_handler_initialization_verbose(self):
        """Test handler initialization with verbose."""
        handler = GitHubHandler(verbose=True)
        assert handler.verbose is True

    def test_validate_github_url_valid(self):
        """Test validation of valid GitHub URLs."""
        handler = GitHubHandler()

        valid_urls = [
            "https://github.com/user/repo",
            "https://github.com/user/repo.git",
            "https://github.com/organization/project",
            "http://github.com/user/repo",
        ]

        for url in valid_urls:
            assert handler.validate_github_url(url) is True, f"Should validate: {url}"

    def test_validate_github_url_invalid(self):
        """Test validation of invalid GitHub URLs."""
        handler = GitHubHandler()

        invalid_urls = [
            "https://gitlab.com/user/repo",
            "https://bitbucket.org/user/repo",
            "https://github.com",
            "https://github.com/",
            "https://github.com/user",
            "not-a-url",
            "",
        ]

        for url in invalid_urls:
            assert handler.validate_github_url(url) is False, f"Should not validate: {url}"

    @patch("prettipy.github_handler.Repo")
    @patch("prettipy.github_handler.tempfile.mkdtemp")
    def test_clone_repository_success(self, mock_mkdtemp, mock_repo_class):
        """Test successful repository cloning."""
        handler = GitHubHandler()

        # Mock temporary directory
        temp_path = "/tmp/prettipy_test"
        mock_mkdtemp.return_value = temp_path

        # Mock repository
        mock_repo = MagicMock()
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_repo.active_branch = mock_branch
        mock_repo_class.clone_from.return_value = mock_repo

        # Clone repository
        repo_url = "https://github.com/user/repo"
        cloned_path, branch = handler.clone_repository(repo_url)

        # Verify
        assert cloned_path == Path(temp_path)
        assert branch == "main"
        mock_repo_class.clone_from.assert_called_once_with(
            repo_url, temp_path, branch=None, depth=1
        )

    @patch("prettipy.github_handler.Repo")
    @patch("prettipy.github_handler.tempfile.mkdtemp")
    def test_clone_repository_with_branch(self, mock_mkdtemp, mock_repo_class):
        """Test cloning repository with specific branch."""
        handler = GitHubHandler()

        # Mock temporary directory
        temp_path = "/tmp/prettipy_test"
        mock_mkdtemp.return_value = temp_path

        # Mock repository
        mock_repo = MagicMock()
        mock_branch = MagicMock()
        mock_branch.name = "develop"
        mock_repo.active_branch = mock_branch
        mock_repo_class.clone_from.return_value = mock_repo

        # Clone repository with branch
        repo_url = "https://github.com/user/repo"
        cloned_path, branch = handler.clone_repository(repo_url, branch="develop")

        # Verify
        assert cloned_path == Path(temp_path)
        assert branch == "develop"
        mock_repo_class.clone_from.assert_called_once_with(
            repo_url, temp_path, branch="develop", depth=1
        )

    def test_clone_repository_invalid_url(self):
        """Test cloning with invalid URL."""
        handler = GitHubHandler()

        with pytest.raises(GitHubHandlerError, match="Invalid GitHub URL"):
            handler.clone_repository("https://gitlab.com/user/repo")

    @patch("prettipy.github_handler.Repo")
    @patch("prettipy.github_handler.tempfile.mkdtemp")
    def test_clone_repository_git_error(self, mock_mkdtemp, mock_repo_class):
        """Test handling of git command errors."""
        handler = GitHubHandler()

        # Mock temporary directory
        temp_path = "/tmp/prettipy_test"
        mock_mkdtemp.return_value = temp_path

        # Mock git error
        from git import GitCommandError

        mock_repo_class.clone_from.side_effect = GitCommandError("clone", "error")

        # Try to clone
        with pytest.raises(GitHubHandlerError, match="Failed to clone repository"):
            handler.clone_repository("https://github.com/user/repo")

    @patch("prettipy.github_handler.shutil.rmtree")
    def test_cleanup(self, mock_rmtree):
        """Test cleanup of temporary directory."""
        handler = GitHubHandler()
        handler.temp_dir = Path("/tmp/test")

        # Mock exists
        with patch.object(Path, "exists", return_value=True):
            handler.cleanup()

        mock_rmtree.assert_called_once_with(Path("/tmp/test"))
        assert handler.temp_dir is None

    def test_cleanup_no_temp_dir(self):
        """Test cleanup when no temp directory exists."""
        handler = GitHubHandler()
        handler.temp_dir = None

        # Should not raise any error
        handler.cleanup()
        assert handler.temp_dir is None

    @patch("prettipy.github_handler.Repo")
    @patch("prettipy.github_handler.tempfile.mkdtemp")
    @patch("prettipy.github_handler.shutil.rmtree")
    def test_context_manager(self, mock_rmtree, mock_mkdtemp, mock_repo_class):
        """Test using handler as context manager."""
        temp_path = "/tmp/prettipy_test"
        mock_mkdtemp.return_value = temp_path

        mock_repo = MagicMock()
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_repo.active_branch = mock_branch
        mock_repo_class.clone_from.return_value = mock_repo

        with patch.object(Path, "exists", return_value=True):
            with GitHubHandler() as handler:
                repo_url = "https://github.com/user/repo"
                cloned_path, branch = handler.clone_repository(repo_url)
                assert cloned_path == Path(temp_path)

        # Verify cleanup was called
        mock_rmtree.assert_called_once()

    @patch("prettipy.github_handler.Repo")
    @patch("prettipy.github_handler.tempfile.mkdtemp")
    def test_clone_repository_with_nonexistent_branch(self, mock_mkdtemp, mock_repo_class):
        """Test cloning with a branch that doesn't exist."""
        handler = GitHubHandler()

        temp_path = "/tmp/prettipy_test"
        mock_mkdtemp.return_value = temp_path

        from git import GitCommandError

        mock_repo_class.clone_from.side_effect = GitCommandError("clone", "branch not found")

        with pytest.raises(
            GitHubHandlerError, match="Failed to clone repository or checkout branch"
        ):
            handler.clone_repository("https://github.com/user/repo", branch="nonexistent")
