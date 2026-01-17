"""Tests for the capture.py context capture module."""
from datetime import datetime
from unittest import mock

import pytest

import capture
import cerebras_client


class TestGitState:
    """Tests for git state extraction functions."""

    def test_is_git_repo_true(self):
        """is_git_repo should return True in a git repository."""
        # This test runs in the flow-guardian repo which is a git repo
        result = capture.is_git_repo()
        assert result is True

    def test_is_git_repo_false(self, tmp_path, monkeypatch):
        """is_git_repo should return False outside a git repository."""
        monkeypatch.chdir(tmp_path)
        result = capture.is_git_repo()
        assert result is False

    def test_capture_git_state_in_repo(self):
        """capture_git_state should return git info in a repository."""
        result = capture.capture_git_state()

        assert result["is_git"] is True
        assert "branch" in result
        assert "uncommitted_files" in result
        assert isinstance(result["uncommitted_files"], list)
        assert "recent_commits" in result
        assert isinstance(result["recent_commits"], list)

    def test_capture_git_state_not_in_repo(self, tmp_path, monkeypatch):
        """capture_git_state should handle non-git directories."""
        monkeypatch.chdir(tmp_path)

        result = capture.capture_git_state()

        assert result["is_git"] is False
        assert result["branch"] is None
        assert result["uncommitted_files"] == []
        assert result["recent_commits"] == []
        assert result["last_commit"] is None

    def test_get_diff_summary_in_repo(self):
        """get_diff_summary should return diff stats in a repository."""
        result = capture.get_diff_summary()

        # Result should be a string
        assert isinstance(result, str)

    def test_get_diff_summary_not_in_repo(self, tmp_path, monkeypatch):
        """get_diff_summary should return empty string outside git repo."""
        monkeypatch.chdir(tmp_path)

        result = capture.get_diff_summary()

        assert result == ""

    def test_get_detailed_diff(self):
        """get_detailed_diff should return detailed diff output."""
        result = capture.get_detailed_diff()

        # Result should be a string
        assert isinstance(result, str)

    def test_get_detailed_diff_truncates(self):
        """get_detailed_diff should truncate long output."""
        result = capture.get_detailed_diff(max_lines=5)

        lines = result.split("\n") if result else []
        # Even truncated, should be reasonable length
        assert len(lines) <= 10  # Allow some buffer


class TestContextAnalysis:
    """Tests for context analysis functions."""

    def test_analyze_context_with_cerebras(self):
        """analyze_context should use Cerebras when available."""
        git_state = {
            "branch": "feature/test",
            "uncommitted_files": ["test.py"],
            "is_git": True
        }

        mock_result = {
            "summary": "Working on test feature",
            "hypothesis": "Testing approach",
            "next_steps": ["Write tests"],
            "decisions": ["Use pytest"],
            "learnings": ["TDD is useful"]
        }

        with mock.patch.object(
            cerebras_client, 'analyze_session_context',
            return_value=mock_result
        ):
            result = capture.analyze_context(git_state, "Test message")

            assert result["summary"] == "Working on test feature"
            assert result["hypothesis"] == "Testing approach"
            assert result["files"] == ["test.py"]

    def test_analyze_context_fallback(self):
        """analyze_context should fallback gracefully on Cerebras error."""
        git_state = {
            "branch": "main",
            "uncommitted_files": [],
            "is_git": True
        }

        with mock.patch.object(
            cerebras_client, 'analyze_session_context',
            side_effect=cerebras_client.CerebrasError("API unavailable")
        ):
            result = capture.analyze_context(git_state, "Working on feature")

            assert result["summary"] == "Working on feature"
            assert result["hypothesis"] is None
            assert result["files"] == []


class TestBuildSession:
    """Tests for build_session function."""

    def test_build_session_structure(self):
        """build_session should return complete session structure."""
        with mock.patch.object(capture, 'capture_git_state') as mock_git, \
             mock.patch.object(capture, 'analyze_context') as mock_analyze:

            mock_git.return_value = {
                "is_git": True,
                "branch": "main",
                "uncommitted_files": ["file.py"],
                "recent_commits": ["abc123 Initial commit"],
                "last_commit": {"hash": "abc123", "message": "Initial commit"}
            }
            mock_analyze.return_value = {
                "summary": "Test session",
                "hypothesis": "Test hypothesis",
                "files": ["file.py"],
                "next_steps": ["Step 1"],
                "decisions": ["Decision 1"],
                "learnings": ["Learning 1"]
            }

            session = capture.build_session(
                user_message="Test message",
                tags=["test", "example"]
            )

            # Check session structure
            assert "id" in session
            assert session["id"].startswith("session_")
            assert "timestamp" in session
            assert "version" in session
            assert session["version"] == 1

            # Check context
            assert "context" in session
            assert session["context"]["summary"] == "Test session"
            assert session["context"]["hypothesis"] == "Test hypothesis"

            # Check git info
            assert "git" in session
            assert session["git"]["branch"] == "main"
            assert session["git"]["uncommitted_files"] == ["file.py"]

            # Check metadata
            assert "metadata" in session
            assert session["metadata"]["message"] == "Test message"
            assert session["metadata"]["tags"] == ["test", "example"]
            assert session["metadata"]["trigger"] == "manual"

    def test_build_session_without_message(self):
        """build_session should work without user message."""
        with mock.patch.object(capture, 'capture_git_state') as mock_git, \
             mock.patch.object(capture, 'analyze_context') as mock_analyze:

            mock_git.return_value = {
                "is_git": True,
                "branch": "main",
                "uncommitted_files": [],
                "recent_commits": [],
                "last_commit": None
            }
            mock_analyze.return_value = {
                "summary": "Working on code",
                "hypothesis": None,
                "files": [],
                "next_steps": [],
                "decisions": [],
                "learnings": []
            }

            session = capture.build_session()

            assert session["metadata"]["message"] is None
            assert session["metadata"]["tags"] == []

    def test_build_session_id_format(self):
        """build_session should generate correctly formatted session ID."""
        with mock.patch.object(capture, 'capture_git_state') as mock_git, \
             mock.patch.object(capture, 'analyze_context') as mock_analyze:

            mock_git.return_value = {
                "is_git": False,
                "branch": None,
                "uncommitted_files": [],
                "recent_commits": [],
                "last_commit": None
            }
            mock_analyze.return_value = {
                "summary": "Test",
                "hypothesis": None,
                "files": [],
                "next_steps": [],
                "decisions": [],
                "learnings": []
            }

            session = capture.build_session()

            # ID should be in format session_YYYY-MM-DD_HH-MM-SS
            assert session["id"].startswith("session_")
            parts = session["id"].replace("session_", "").split("_")
            assert len(parts) == 2
            # Date part should have dashes
            assert len(parts[0].split("-")) == 3
            # Time part should have dashes
            assert len(parts[1].split("-")) == 3
