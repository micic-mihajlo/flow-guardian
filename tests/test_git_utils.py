"""Tests for the git_utils.py shared git utilities module."""
import subprocess
from unittest import mock

import pytest

import git_utils


class TestRunGitCommand:
    """Tests for run_git_command helper."""

    def test_successful_command(self):
        """run_git_command should return success for valid commands."""
        success, output = git_utils.run_git_command(["--version"])

        assert success is True
        assert "git version" in output.lower()

    def test_failed_command(self):
        """run_git_command should return failure for invalid commands."""
        success, output = git_utils.run_git_command(["invalid-command-xyz"])

        assert success is False

    def test_handles_timeout(self):
        """run_git_command should handle timeouts gracefully."""
        with mock.patch('git_utils.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 10)

            success, output = git_utils.run_git_command(["status"])

            assert success is False
            assert output == ""

    def test_handles_file_not_found(self):
        """run_git_command should handle missing git binary gracefully."""
        with mock.patch('git_utils.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            success, output = git_utils.run_git_command(["status"])

            assert success is False
            assert output == ""

    def test_custom_timeout(self):
        """run_git_command should support custom timeout values."""
        with mock.patch('git_utils.subprocess.run') as mock_run:
            mock_result = mock.Mock()
            mock_result.returncode = 0
            mock_result.stdout = "test output"
            mock_run.return_value = mock_result

            success, output = git_utils.run_git_command(["status"], timeout=30)

            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["timeout"] == 30


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_is_git_repo_true(self):
        """is_git_repo should return True in a git repository."""
        # This test runs in the flow-guardian repo which is a git repo
        result = git_utils.is_git_repo()
        assert result is True

    def test_is_git_repo_false(self, tmp_path, monkeypatch):
        """is_git_repo should return False outside a git repository."""
        monkeypatch.chdir(tmp_path)
        result = git_utils.is_git_repo()
        assert result is False


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    def test_get_current_branch_in_repo(self):
        """get_current_branch should return branch name in git repo."""
        result = git_utils.get_current_branch()

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_current_branch_not_in_repo(self, tmp_path, monkeypatch):
        """get_current_branch should return None outside git repo."""
        monkeypatch.chdir(tmp_path)

        result = git_utils.get_current_branch()

        assert result is None

    def test_get_current_branch_returns_expected_branch(self):
        """get_current_branch should return the actual branch name."""
        # Run git command directly to compare
        import subprocess
        direct_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True
        )
        expected_branch = direct_result.stdout.strip()

        result = git_utils.get_current_branch()

        assert result == expected_branch
