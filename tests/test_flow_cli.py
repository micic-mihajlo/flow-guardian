"""Tests for the flow.py CLI module."""
from unittest import mock

import pytest
from click.testing import CliRunner

import flow


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


class TestCLIBasics:
    """Tests for basic CLI functionality."""

    def test_help_command(self, cli_runner):
        """CLI should display help message."""
        result = cli_runner.invoke(flow.cli, ['--help'])

        assert result.exit_code == 0
        assert "Flow Guardian" in result.output
        assert "save" in result.output
        assert "resume" in result.output
        assert "learn" in result.output
        assert "recall" in result.output
        assert "team" in result.output
        assert "status" in result.output
        assert "history" in result.output

    def test_version_command(self, cli_runner):
        """CLI should display version."""
        result = cli_runner.invoke(flow.cli, ['--version'])

        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestSaveCommand:
    """Tests for the save command."""

    def test_save_help(self, cli_runner):
        """save command should display help."""
        result = cli_runner.invoke(flow.cli, ['save', '--help'])

        assert result.exit_code == 0
        assert "--message" in result.output or "-m" in result.output
        assert "--tag" in result.output or "-t" in result.output
        assert "--quiet" in result.output or "-q" in result.output

    def test_save_basic(self, cli_runner, tmp_path):
        """save command should save session."""
        with mock.patch('flow.capture') as mock_capture, \
             mock.patch('flow.memory') as mock_memory, \
             mock.patch('flow.backboard_client') as mock_backboard:

            mock_capture.build_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {"summary": "Test session"},
                "git": {"branch": "main"},
                "metadata": {"tags": []}
            }
            mock_memory.save_session.return_value = "session_test"
            mock_backboard.run_async.return_value = None

            result = cli_runner.invoke(flow.cli, ['save'])

            assert result.exit_code == 0
            mock_capture.build_session.assert_called_once()
            mock_memory.save_session.assert_called_once()

    def test_save_with_message(self, cli_runner):
        """save command should accept message."""
        with mock.patch('flow.capture') as mock_capture, \
             mock.patch('flow.memory') as mock_memory, \
             mock.patch('flow.backboard_client'):

            mock_capture.build_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {"summary": "Test"},
                "git": {"branch": "main"},
                "metadata": {"tags": []}
            }
            mock_memory.save_session.return_value = "session_test"

            result = cli_runner.invoke(flow.cli, ['save', '-m', 'Test message'])

            assert result.exit_code == 0
            call_args = mock_capture.build_session.call_args
            assert call_args.kwargs.get('user_message') == 'Test message'

    def test_save_with_tags(self, cli_runner):
        """save command should accept multiple tags."""
        with mock.patch('flow.capture') as mock_capture, \
             mock.patch('flow.memory') as mock_memory, \
             mock.patch('flow.backboard_client'):

            mock_capture.build_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {"summary": "Test"},
                "git": {"branch": "main"},
                "metadata": {"tags": ["auth", "jwt"]}
            }
            mock_memory.save_session.return_value = "session_test"

            result = cli_runner.invoke(flow.cli, ['save', '-t', 'auth', '-t', 'jwt'])

            assert result.exit_code == 0
            call_args = mock_capture.build_session.call_args
            assert 'auth' in call_args.kwargs.get('tags', [])
            assert 'jwt' in call_args.kwargs.get('tags', [])


class TestResumeCommand:
    """Tests for the resume command."""

    def test_resume_help(self, cli_runner):
        """resume command should display help."""
        result = cli_runner.invoke(flow.cli, ['resume', '--help'])

        assert result.exit_code == 0
        assert "--session" in result.output or "-s" in result.output
        assert "--pick" in result.output or "-p" in result.output
        assert "--raw" in result.output
        assert "--copy" in result.output

    def test_resume_no_sessions(self, cli_runner):
        """resume command should handle no sessions gracefully."""
        with mock.patch('flow.memory') as mock_memory:
            mock_memory.get_latest_session.return_value = None

            result = cli_runner.invoke(flow.cli, ['resume'])

            assert result.exit_code == 0
            assert "No saved sessions" in result.output or "no sessions" in result.output.lower()

    def test_resume_with_session(self, cli_runner):
        """resume command should restore session context."""
        with mock.patch('flow.memory') as mock_memory, \
             mock.patch('flow.restore') as mock_restore:

            mock_memory.get_latest_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {
                    "summary": "Working on feature",
                    "hypothesis": "Test approach",
                    "files": ["test.py"],
                    "next_steps": ["Write tests"]
                },
                "git": {"branch": "main"},
                "learnings": []
            }
            mock_restore.get_changes_since.return_value = {
                "elapsed": "2h",
                "commits": [],
                "files_changed": [],
                "is_stale": False
            }
            mock_restore.detect_conflicts.return_value = []
            mock_restore.generate_restoration_message.return_value = "Welcome back!"

            result = cli_runner.invoke(flow.cli, ['resume'])

            assert result.exit_code == 0
            mock_memory.get_latest_session.assert_called_once()


class TestLearnCommand:
    """Tests for the learn command."""

    def test_learn_help(self, cli_runner):
        """learn command should display help."""
        result = cli_runner.invoke(flow.cli, ['learn', '--help'])

        assert result.exit_code == 0
        assert "--tag" in result.output or "-t" in result.output
        assert "--team" in result.output

    def test_learn_basic(self, cli_runner):
        """learn command should store learning."""
        with mock.patch('flow.memory') as mock_memory, \
             mock.patch('flow.backboard_client'):

            mock_memory.save_learning.return_value = "learning_test"
            mock_memory.get_config.return_value = {"user": "testuser"}

            result = cli_runner.invoke(flow.cli, ['learn', 'Test learning'])

            assert result.exit_code == 0
            mock_memory.save_learning.assert_called_once()

    def test_learn_with_tags(self, cli_runner):
        """learn command should accept tags."""
        with mock.patch('flow.memory') as mock_memory, \
             mock.patch('flow.backboard_client'):

            mock_memory.save_learning.return_value = "learning_test"
            mock_memory.get_config.return_value = {"user": "testuser"}

            result = cli_runner.invoke(flow.cli, ['learn', 'Auth insight', '-t', 'auth', '-t', 'security'])

            assert result.exit_code == 0
            call_args = mock_memory.save_learning.call_args
            learning = call_args.args[0] if call_args.args else call_args.kwargs.get('learning')
            if isinstance(learning, dict):
                assert 'auth' in learning.get('tags', [])


class TestRecallCommand:
    """Tests for the recall command."""

    def test_recall_help(self, cli_runner):
        """recall command should display help."""
        result = cli_runner.invoke(flow.cli, ['recall', '--help'])

        assert result.exit_code == 0
        assert "--tag" in result.output or "-t" in result.output
        assert "--limit" in result.output

    def test_recall_basic(self, cli_runner):
        """recall command should search learnings."""
        with mock.patch('flow.memory') as mock_memory, \
             mock.patch('flow.backboard_client') as mock_backboard:

            mock_memory.search_learnings.return_value = [
                {"text": "Auth learning", "tags": ["auth"], "timestamp": "2024-01-01T12:00:00"}
            ]
            mock_memory.get_config.return_value = {}

            result = cli_runner.invoke(flow.cli, ['recall', 'authentication'])

            assert result.exit_code == 0


class TestTeamCommand:
    """Tests for the team command."""

    def test_team_help(self, cli_runner):
        """team command should display help."""
        result = cli_runner.invoke(flow.cli, ['team', '--help'])

        assert result.exit_code == 0
        assert "--tag" in result.output or "-t" in result.output
        assert "--limit" in result.output

    def test_team_no_config(self, cli_runner):
        """team command should handle missing team config."""
        with mock.patch('flow.memory') as mock_memory:
            mock_memory.get_config.return_value = {"backboard": {}}

            result = cli_runner.invoke(flow.cli, ['team', 'query'])

            # Should exit gracefully with info about team setup
            assert result.exit_code == 0 or "team" in result.output.lower()


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_help(self, cli_runner):
        """status command should display help."""
        result = cli_runner.invoke(flow.cli, ['status', '--help'])

        assert result.exit_code == 0

    def test_status_basic(self, cli_runner):
        """status command should show status information."""
        with mock.patch('flow.memory') as mock_memory, \
             mock.patch('flow.capture') as mock_capture, \
             mock.patch('flow.backboard_client') as mock_backboard:

            mock_memory.get_stats.return_value = {
                "sessions_count": 5,
                "personal_learnings": 10,
                "team_learnings": 3,
                "total_learnings": 13
            }
            mock_memory.get_latest_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {"summary": "Working on feature"},
                "git": {"branch": "main"}
            }
            mock_memory.get_config.return_value = {}
            mock_capture.capture_git_state.return_value = {
                "is_git": True,
                "branch": "main",
                "uncommitted_files": []
            }
            mock_backboard.run_async.return_value = True

            result = cli_runner.invoke(flow.cli, ['status'])

            assert result.exit_code == 0


class TestHistoryCommand:
    """Tests for the history command."""

    def test_history_help(self, cli_runner):
        """history command should display help."""
        result = cli_runner.invoke(flow.cli, ['history', '--help'])

        assert result.exit_code == 0
        assert "--limit" in result.output or "-n" in result.output
        assert "--all" in result.output
        assert "--branch" in result.output

    def test_history_basic(self, cli_runner):
        """history command should list sessions."""
        with mock.patch('flow.memory') as mock_memory:
            mock_memory.list_sessions.return_value = [
                {
                    "id": "session_1",
                    "timestamp": "2024-01-01T12:00:00",
                    "branch": "main",
                    "summary": "First session"
                },
                {
                    "id": "session_2",
                    "timestamp": "2024-01-01T13:00:00",
                    "branch": "feature",
                    "summary": "Second session"
                }
            ]

            result = cli_runner.invoke(flow.cli, ['history'])

            assert result.exit_code == 0
            mock_memory.list_sessions.assert_called_once()

    def test_history_with_limit(self, cli_runner):
        """history command should respect limit."""
        with mock.patch('flow.memory') as mock_memory:
            mock_memory.list_sessions.return_value = []

            result = cli_runner.invoke(flow.cli, ['history', '-n', '5'])

            assert result.exit_code == 0
            call_args = mock_memory.list_sessions.call_args
            assert call_args.kwargs.get('limit') == 5

    def test_history_filter_by_branch(self, cli_runner):
        """history command should filter by branch."""
        with mock.patch('flow.memory') as mock_memory:
            mock_memory.list_sessions.return_value = []

            result = cli_runner.invoke(flow.cli, ['history', '--branch', 'main'])

            assert result.exit_code == 0
            call_args = mock_memory.list_sessions.call_args
            assert call_args.kwargs.get('branch') == 'main'

    def test_history_empty(self, cli_runner):
        """history command should handle no sessions."""
        with mock.patch('flow.memory') as mock_memory:
            mock_memory.list_sessions.return_value = []

            result = cli_runner.invoke(flow.cli, ['history'])

            assert result.exit_code == 0
            assert "No sessions" in result.output or "no saved sessions" in result.output.lower()
