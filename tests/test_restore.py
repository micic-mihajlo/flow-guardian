"""Tests for the restore.py context restoration module."""
from datetime import datetime, timedelta
from unittest import mock

import pytest

import restore
import cerebras_client


class TestTimeCalculations:
    """Tests for time calculation functions."""

    def test_calculate_time_elapsed_just_now(self):
        """calculate_time_elapsed should return 'just now' for recent times."""
        now = datetime.now()
        timestamp = now.isoformat()

        result = restore.calculate_time_elapsed(timestamp)

        assert result == "just now"

    def test_calculate_time_elapsed_minutes(self):
        """calculate_time_elapsed should format minutes correctly."""
        now = datetime.now()
        past = now - timedelta(minutes=45)
        timestamp = past.isoformat()

        result = restore.calculate_time_elapsed(timestamp)

        assert result == "45m"

    def test_calculate_time_elapsed_hours(self):
        """calculate_time_elapsed should format hours correctly."""
        now = datetime.now()
        past = now - timedelta(hours=2, minutes=30)
        timestamp = past.isoformat()

        result = restore.calculate_time_elapsed(timestamp)

        assert result == "2h 30m"

    def test_calculate_time_elapsed_hours_only(self):
        """calculate_time_elapsed should format hours without minutes."""
        now = datetime.now()
        past = now - timedelta(hours=3)
        timestamp = past.isoformat()

        result = restore.calculate_time_elapsed(timestamp)

        assert result == "3h"

    def test_calculate_time_elapsed_days(self):
        """calculate_time_elapsed should format days correctly."""
        now = datetime.now()
        past = now - timedelta(days=3)
        timestamp = past.isoformat()

        result = restore.calculate_time_elapsed(timestamp)

        assert result == "3 days"

    def test_calculate_time_elapsed_one_day(self):
        """calculate_time_elapsed should format one day correctly."""
        now = datetime.now()
        past = now - timedelta(days=1, hours=5)
        timestamp = past.isoformat()

        result = restore.calculate_time_elapsed(timestamp)

        assert "1 day" in result

    def test_calculate_time_elapsed_invalid(self):
        """calculate_time_elapsed should handle invalid timestamps."""
        result = restore.calculate_time_elapsed("not a timestamp")

        assert result == "unknown time"

    def test_is_session_stale_fresh(self):
        """is_session_stale should return False for recent sessions."""
        now = datetime.now()
        timestamp = now.isoformat()

        result = restore.is_session_stale(timestamp)

        assert result is False

    def test_is_session_stale_old(self):
        """is_session_stale should return True for old sessions."""
        now = datetime.now()
        past = now - timedelta(days=10)
        timestamp = past.isoformat()

        result = restore.is_session_stale(timestamp)

        assert result is True

    def test_is_session_stale_custom_threshold(self):
        """is_session_stale should respect custom threshold."""
        now = datetime.now()
        past = now - timedelta(days=3)
        timestamp = past.isoformat()

        result = restore.is_session_stale(timestamp, threshold_days=2)

        assert result is True


class TestChangeDetection:
    """Tests for change detection functions."""

    def test_get_changes_since_basic(self):
        """get_changes_since should return change information."""
        now = datetime.now()
        past = now - timedelta(hours=1)
        timestamp = past.isoformat()

        result = restore.get_changes_since(timestamp)

        assert "elapsed" in result
        assert "commits" in result
        assert "files_changed" in result
        assert "is_stale" in result

    def test_get_changes_since_not_git_repo(self, tmp_path, monkeypatch):
        """get_changes_since should handle non-git directories."""
        monkeypatch.chdir(tmp_path)
        now = datetime.now()
        timestamp = now.isoformat()

        result = restore.get_changes_since(timestamp)

        assert result["commits"] == []
        assert result["files_changed"] == []

    def test_detect_conflicts_no_conflicts(self):
        """detect_conflicts should return empty list when no conflicts."""
        session = {
            "git": {
                "branch": "main",
                "uncommitted_files": []
            }
        }

        # Mock to return same branch
        with mock.patch.object(restore, '_run_git_command') as mock_git:
            mock_git.return_value = (True, "main")

            result = restore.detect_conflicts(session)

            assert result == []

    def test_detect_conflicts_branch_mismatch(self):
        """detect_conflicts should detect branch changes."""
        session = {
            "git": {
                "branch": "feature",
                "uncommitted_files": []
            }
        }

        with mock.patch.object(restore, '_is_git_repo', return_value=True), \
             mock.patch.object(restore, '_run_git_command') as mock_git:
            mock_git.return_value = (True, "main")

            result = restore.detect_conflicts(session)

            assert len(result) == 1
            assert "Branch changed" in result[0]

    def test_detect_conflicts_uncommitted_files(self):
        """detect_conflicts should detect uncommitted file conflicts."""
        session = {
            "git": {
                "branch": "main",
                "uncommitted_files": ["file.py"]
            }
        }

        with mock.patch.object(restore, '_is_git_repo', return_value=True), \
             mock.patch.object(restore, '_run_git_command') as mock_git:
            # First call for branch check
            # Second call for status
            mock_git.side_effect = [
                (True, "main"),
                (True, " M file.py")
            ]

            result = restore.detect_conflicts(session)

            assert len(result) == 1
            assert "uncommitted" in result[0].lower()

    def test_get_current_branch_in_repo(self):
        """get_current_branch should return branch name in git repo."""
        # This runs in flow-guardian which is a git repo
        result = restore.get_current_branch()

        assert result is not None
        assert isinstance(result, str)

    def test_get_current_branch_not_in_repo(self, tmp_path, monkeypatch):
        """get_current_branch should return None outside git repo."""
        monkeypatch.chdir(tmp_path)

        result = restore.get_current_branch()

        assert result is None


class TestRestorationMessage:
    """Tests for restoration message generation."""

    def test_generate_restoration_message_with_cerebras(self):
        """generate_restoration_message should use Cerebras when available."""
        session = {
            "context": {
                "summary": "Working on feature",
                "hypothesis": "Test approach",
                "files": ["test.py"],
                "next_steps": ["Write tests"]
            },
            "git": {"branch": "main"},
            "learnings": ["Learned something"]
        }
        changes = {
            "elapsed": "2h",
            "commits": ["abc123 New commit"],
            "files_changed": ["other.py"]
        }

        with mock.patch.object(
            cerebras_client, 'generate_restoration_message',
            return_value="Welcome back! You were working on a feature."
        ):
            result = restore.generate_restoration_message(session, changes)

            assert "Welcome back" in result

    def test_generate_restoration_message_fallback(self):
        """generate_restoration_message should fallback on Cerebras error."""
        session = {
            "context": {
                "summary": "Working on feature",
                "hypothesis": "Test approach",
                "files": ["test.py"],
                "next_steps": ["Write tests"]
            },
            "git": {"branch": "main"},
            "learnings": []
        }
        changes = {
            "elapsed": "2h",
            "commits": [],
            "files_changed": []
        }

        with mock.patch.object(
            cerebras_client, 'generate_restoration_message',
            side_effect=cerebras_client.CerebrasError("API unavailable")
        ):
            result = restore.generate_restoration_message(session, changes)

            # Should still produce a message
            assert "Welcome back" in result
            assert "Working on feature" in result

    def test_build_fallback_message(self):
        """_build_fallback_message should create structured message."""
        session = {
            "context": {
                "summary": "Implementing auth",
                "hypothesis": "JWT is best",
                "files": ["auth.py", "tokens.py"],
                "next_steps": ["Add refresh tokens", "Write tests"]
            },
            "git": {"branch": "feature/auth"},
            "learnings": []
        }
        changes = {
            "elapsed": "3h",
            "commits": ["123 Added base auth"],
            "files_changed": ["README.md"]
        }

        result = restore._build_fallback_message(session, changes)

        assert "Welcome back" in result
        assert "Implementing auth" in result
        assert "JWT is best" in result
        assert "feature/auth" in result
        assert "3h" in result


class TestBuildRawContext:
    """Tests for build_raw_context function."""

    def test_build_raw_context_full(self):
        """build_raw_context should create complete markdown context."""
        session = {
            "context": {
                "summary": "Working on feature",
                "hypothesis": "Test approach",
                "files": ["test.py", "main.py"],
                "next_steps": ["Step 1", "Step 2"]
            },
            "git": {"branch": "main"},
            "learnings": [
                {"text": "Learning 1", "tags": ["tag1"]},
                "Learning 2 (plain string)"
            ]
        }
        changes = {
            "elapsed": "2h",
            "commits": ["abc123 New commit"],
            "files_changed": ["other.py"]
        }

        result = restore.build_raw_context(session, changes)

        assert "## Session Context" in result
        assert "Working on feature" in result
        assert "Test approach" in result
        assert "test.py" in result
        assert "## Previous Learnings" in result
        assert "Learning 1" in result
        assert "## Changes Since Last Session" in result
        assert "2h" in result
        assert "## Suggested Next Steps" in result
        assert "Step 1" in result

    def test_build_raw_context_minimal(self):
        """build_raw_context should handle minimal session data."""
        session = {
            "context": {
                "summary": "Working",
            },
            "git": {},
            "learnings": []
        }
        changes = {
            "elapsed": "1h",
            "commits": [],
            "files_changed": []
        }

        result = restore.build_raw_context(session, changes)

        assert "## Session Context" in result
        assert "Working" in result
        # Should not have learnings section
        assert "## Previous Learnings" not in result
