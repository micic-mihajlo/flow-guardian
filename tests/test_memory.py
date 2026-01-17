"""Tests for the memory.py local storage module."""
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

import memory


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Use a temporary directory for storage during tests."""
    # Patch the storage directory constants
    with mock.patch.object(memory, 'STORAGE_DIR', tmp_path), \
         mock.patch.object(memory, 'SESSIONS_DIR', tmp_path / "sessions"), \
         mock.patch.object(memory, 'CONFIG_FILE', tmp_path / "config.json"), \
         mock.patch.object(memory, 'SESSIONS_INDEX', tmp_path / "sessions" / "index.json"), \
         mock.patch.object(memory, 'LEARNINGS_FILE', tmp_path / "learnings.json"):
        yield tmp_path


class TestInitStorage:
    """Tests for init_storage function."""

    def test_creates_directories(self, temp_storage_dir):
        """init_storage should create all required directories."""
        memory.init_storage()

        assert temp_storage_dir.exists()
        assert (temp_storage_dir / "sessions").exists()

    def test_creates_config_file(self, temp_storage_dir):
        """init_storage should create config.json with defaults."""
        memory.init_storage()

        config_file = temp_storage_dir / "config.json"
        assert config_file.exists()

        config = json.loads(config_file.read_text())
        assert "user" in config
        assert "backboard" in config
        assert "settings" in config

    def test_creates_sessions_index(self, temp_storage_dir):
        """init_storage should create empty sessions index."""
        memory.init_storage()

        index_file = temp_storage_dir / "sessions" / "index.json"
        assert index_file.exists()

        index = json.loads(index_file.read_text())
        assert index == []

    def test_creates_learnings_file(self, temp_storage_dir):
        """init_storage should create empty learnings file."""
        memory.init_storage()

        learnings_file = temp_storage_dir / "learnings.json"
        assert learnings_file.exists()

        learnings = json.loads(learnings_file.read_text())
        assert learnings == []

    def test_idempotent(self, temp_storage_dir):
        """init_storage should be safe to call multiple times."""
        memory.init_storage()
        memory.init_storage()

        assert temp_storage_dir.exists()


class TestSessionManagement:
    """Tests for session save/load/list functions."""

    def test_save_session_generates_id(self, temp_storage_dir):
        """save_session should generate ID if not provided."""
        session = {"context": {"summary": "Test session"}}

        session_id = memory.save_session(session)

        assert session_id.startswith("session_")

    def test_save_session_uses_provided_id(self, temp_storage_dir):
        """save_session should use provided ID."""
        session = {
            "id": "session_2024-01-01_12-00-00",
            "context": {"summary": "Test session"}
        }

        session_id = memory.save_session(session)

        assert session_id == "session_2024-01-01_12-00-00"

    def test_save_and_load_session(self, temp_storage_dir):
        """save_session and load_session should work together."""
        session = {
            "context": {"summary": "Test session"},
            "git": {"branch": "main"},
            "metadata": {"tags": ["test"]}
        }

        session_id = memory.save_session(session)
        loaded = memory.load_session(session_id)

        assert loaded is not None
        assert loaded["context"]["summary"] == "Test session"
        assert loaded["git"]["branch"] == "main"

    def test_load_nonexistent_session(self, temp_storage_dir):
        """load_session should return None for nonexistent session."""
        memory.init_storage()

        result = memory.load_session("session_nonexistent")

        assert result is None

    def test_get_latest_session(self, temp_storage_dir):
        """get_latest_session should return most recent session."""
        # Save multiple sessions
        session1 = {"context": {"summary": "First session"}}
        session2 = {"context": {"summary": "Second session"}}

        memory.save_session(session1)
        memory.save_session(session2)

        latest = memory.get_latest_session()

        assert latest is not None
        assert latest["context"]["summary"] == "Second session"

    def test_get_latest_session_empty(self, temp_storage_dir):
        """get_latest_session should return None when no sessions exist."""
        memory.init_storage()

        result = memory.get_latest_session()

        assert result is None

    def test_list_sessions(self, temp_storage_dir):
        """list_sessions should return session summaries."""
        # Use explicit IDs to avoid timestamp collisions
        session1 = {
            "id": "session_2024-01-01_12-00-00",
            "context": {"summary": "First session"},
            "git": {"branch": "main"}
        }
        session2 = {
            "id": "session_2024-01-01_12-00-01",
            "context": {"summary": "Second session"},
            "git": {"branch": "feature"}
        }

        memory.save_session(session1)
        memory.save_session(session2)

        sessions = memory.list_sessions()

        assert len(sessions) == 2

    def test_list_sessions_with_limit(self, temp_storage_dir):
        """list_sessions should respect limit parameter."""
        # Use explicit IDs to avoid timestamp collisions
        for i in range(5):
            memory.save_session({
                "id": f"session_2024-01-01_12-00-0{i}",
                "context": {"summary": f"Session {i}"}
            })

        sessions = memory.list_sessions(limit=3)

        assert len(sessions) == 3

    def test_list_sessions_filter_by_branch(self, temp_storage_dir):
        """list_sessions should filter by branch."""
        # Use explicit IDs to avoid timestamp collisions
        memory.save_session({
            "id": "session_2024-01-01_12-00-00",
            "context": {"summary": "Main session"},
            "git": {"branch": "main"}
        })
        memory.save_session({
            "id": "session_2024-01-01_12-00-01",
            "context": {"summary": "Feature session"},
            "git": {"branch": "feature"}
        })

        main_sessions = memory.list_sessions(branch="main")
        feature_sessions = memory.list_sessions(branch="feature")

        assert len(main_sessions) == 1
        assert len(feature_sessions) == 1


class TestLearningsManagement:
    """Tests for learnings save/search functions."""

    def test_save_learning_generates_id(self, temp_storage_dir):
        """save_learning should generate ID if not provided."""
        learning = {"text": "Test learning", "tags": ["test"]}

        learning_id = memory.save_learning(learning)

        assert learning_id.startswith("learning_")

    def test_save_and_search_learnings(self, temp_storage_dir):
        """save_learning and search_learnings should work together."""
        memory.save_learning({
            "text": "Authentication requires JWT tokens",
            "tags": ["auth", "jwt"]
        })
        memory.save_learning({
            "text": "Database connection pooling is important",
            "tags": ["database"]
        })

        results = memory.search_learnings("authentication")

        assert len(results) == 1
        assert "JWT" in results[0]["text"]

    def test_search_learnings_by_tag(self, temp_storage_dir):
        """search_learnings should filter by tags."""
        memory.save_learning({
            "text": "Learning about auth",
            "tags": ["auth"]
        })
        memory.save_learning({
            "text": "Learning about database",
            "tags": ["database"]
        })

        results = memory.search_learnings("learning", tags=["auth"])

        assert len(results) == 1
        assert "auth" in results[0]["tags"]

    def test_get_all_learnings(self, temp_storage_dir):
        """get_all_learnings should return all learnings."""
        memory.save_learning({"text": "Learning 1", "tags": []})
        memory.save_learning({"text": "Learning 2", "tags": []})

        all_learnings = memory.get_all_learnings()

        assert len(all_learnings) == 2

    def test_get_all_learnings_filter_by_team(self, temp_storage_dir):
        """get_all_learnings should filter by team flag."""
        memory.save_learning({"text": "Personal learning", "team": False})
        memory.save_learning({"text": "Team learning", "team": True})

        personal = memory.get_all_learnings(team=False)
        team = memory.get_all_learnings(team=True)

        assert len(personal) == 1
        assert len(team) == 1


class TestConfigManagement:
    """Tests for configuration functions."""

    def test_get_config(self, temp_storage_dir):
        """get_config should return configuration dictionary."""
        memory.init_storage()

        config = memory.get_config()

        assert isinstance(config, dict)
        assert "user" in config

    def test_set_config_simple_key(self, temp_storage_dir):
        """set_config should update simple keys."""
        memory.init_storage()

        memory.set_config("user", "testuser")
        config = memory.get_config()

        assert config["user"] == "testuser"

    def test_set_config_nested_key(self, temp_storage_dir):
        """set_config should support dot notation for nested keys."""
        memory.init_storage()

        memory.set_config("backboard.personal_thread_id", "thread_123")
        config = memory.get_config()

        assert config["backboard"]["personal_thread_id"] == "thread_123"


class TestStats:
    """Tests for statistics functions."""

    def test_get_stats(self, temp_storage_dir):
        """get_stats should return correct counts."""
        # Use explicit IDs to avoid timestamp collisions
        memory.save_session({"id": "session_2024-01-01_12-00-00", "context": {"summary": "Session 1"}})
        memory.save_session({"id": "session_2024-01-01_12-00-01", "context": {"summary": "Session 2"}})
        memory.save_learning({"id": "learning_2024-01-01_12-00-00", "text": "Personal learning", "team": False})
        memory.save_learning({"id": "learning_2024-01-01_12-00-01", "text": "Team learning", "team": True})

        stats = memory.get_stats()

        assert stats["sessions_count"] == 2
        assert stats["personal_learnings"] == 1
        assert stats["team_learnings"] == 1
        assert stats["total_learnings"] == 2


class TestAtomicWrites:
    """Tests for atomic file write behavior."""

    def test_atomic_write_creates_file(self, temp_storage_dir):
        """_atomic_write should create file with correct content."""
        filepath = temp_storage_dir / "test.json"
        data = {"key": "value"}

        memory._atomic_write(filepath, data)

        assert filepath.exists()
        assert json.loads(filepath.read_text()) == data

    def test_safe_read_handles_missing_file(self, temp_storage_dir):
        """_safe_read should return default for missing file."""
        filepath = temp_storage_dir / "nonexistent.json"

        result = memory._safe_read(filepath, {"default": True})

        assert result == {"default": True}

    def test_safe_read_handles_corrupted_file(self, temp_storage_dir):
        """_safe_read should return default for corrupted JSON."""
        filepath = temp_storage_dir / "corrupted.json"
        filepath.write_text("not valid json {{{")

        result = memory._safe_read(filepath, {"default": True})

        assert result == {"default": True}
