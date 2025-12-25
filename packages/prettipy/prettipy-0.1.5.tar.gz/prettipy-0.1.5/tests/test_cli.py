"""Tests for CLI argument validation."""

import pytest
from prettipy.cli import CLI


class TestCLIArgumentValidation:
    """Test cases for CLI argument validation."""

    def test_github_and_files_conflict(self):
        """Test that using --github with --files raises an error."""
        cli = CLI()

        # Test that using both --github and --files returns error code
        result = cli.run(
            ["--gh", "https://github.com/user/repo", "--files", "test.py", "-o", "test.pdf"]
        )

        assert result == 1, "Should return error code when --github and --files are both used"
