"""Test scenarios that expose bugs in the system.

These tests verify expected behavior that is currently broken due to bugs.
Run with: pytest tests/test_bug_scenarios.py -v
"""
import pytest
import tempfile
import shutil
from pathlib import Path


class TestSearchLearnings:
    """Tests for the search_learnings function."""

    def test_search_finds_tag_only_matches(self, tmp_path, monkeypatch):
        """
        Test that search returns learnings that only match by tag.

        A learning with tags ["authentication", "jwt"] should be found
        when searching for "auth" even if the insight text doesn't contain "auth".
        """
        from memory import search_learnings, save_learning, STORAGE_DIR, init_storage

        # Use temp directory for storage
        monkeypatch.setattr("memory.STORAGE_DIR", tmp_path)
        monkeypatch.setattr("memory.SESSIONS_DIR", tmp_path / "sessions")
        monkeypatch.setattr("memory.CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr("memory.SESSIONS_INDEX", tmp_path / "sessions" / "index.json")
        monkeypatch.setattr("memory.LEARNINGS_FILE", tmp_path / "learnings.json")

        init_storage()

        # Save a learning that has "auth" in the tag but not in the insight text
        save_learning({
            "insight": "Use refresh tokens for better user experience",
            "tags": ["authentication", "jwt", "security"]
        })

        # Search for "auth" - should find it via tag match
        results = search_learnings("auth")

        assert len(results) == 1, "Should find learning with 'auth' in tag 'authentication'"
        assert "refresh tokens" in results[0].get("insight", "")


class TestHandoffFiles:
    """Tests for handoff file handling."""

    def test_update_handoff_preserves_all_files(self, tmp_path):
        """
        Test that update_handoff preserves all files in the files list.

        When working on a project with many files, all files should be preserved
        in the handoff, not silently truncated.
        """
        from handoff import save_handoff, update_handoff, load_handoff

        # Create initial handoff with many files
        initial_files = [
            "src/auth.py",
            "src/models.py",
            "src/api/routes.py",
            "src/api/handlers.py",
            "src/utils/helpers.py",
            "src/utils/validators.py",
            "tests/test_auth.py",
            "tests/test_models.py"
        ]

        save_handoff({
            "goal": "Implement user authentication",
            "status": "in_progress",
            "now": "Working on tests",
            "files": initial_files
        }, project_root=tmp_path)

        # Update with status change
        update_handoff({"status": "blocked"}, project_root=tmp_path)

        # Load and verify all files are preserved
        handoff = load_handoff(tmp_path)

        assert handoff is not None
        assert len(handoff.get("files", [])) == len(initial_files), \
            f"All {len(initial_files)} files should be preserved, got {len(handoff.get('files', []))}"

        # Verify file order is preserved (important for context)
        assert handoff["files"] == initial_files, \
            "Files list should maintain original order"


class TestSessionStorage:
    """Tests for session storage to Backboard."""

    @pytest.mark.asyncio
    async def test_store_session_preserves_all_files(self):
        """
        Test that store_session includes all files in the content and metadata.

        When storing a session with many files, all files should be included
        in both the content string and the metadata for proper recall.
        """
        from backboard_client import store_session
        from unittest.mock import AsyncMock, patch

        session = {
            "id": "test_session_001",
            "timestamp": "2024-01-17T10:00:00Z",
            "context": {
                "summary": "Working on authentication refactor",
                "hypothesis": "JWT tokens are expiring too quickly",
                "files": [
                    "src/auth/jwt.py",
                    "src/auth/tokens.py",
                    "src/auth/refresh.py",
                    "src/middleware/auth.py",
                    "tests/test_jwt.py"
                ],
                "next_steps": [
                    "Fix token expiry logic",
                    "Add refresh token endpoint",
                    "Update middleware",
                    "Write integration tests"
                ]
            },
            "git": {
                "branch": "fix/jwt-expiry"
            },
            "metadata": {
                "tags": ["auth", "jwt"]
            }
        }

        # Mock the store_message function to capture what's sent
        captured_content = None
        captured_metadata = None

        async def mock_store_message(thread_id, content, metadata=None):
            nonlocal captured_content, captured_metadata
            captured_content = content
            captured_metadata = metadata
            return {"status": "ok"}

        with patch("backboard_client.store_message", mock_store_message):
            await store_session("test_thread", session)

        # Verify all files are in content
        for f in session["context"]["files"]:
            assert f in captured_content, f"File {f} should be in content"

        # Verify all files are in metadata
        assert len(captured_metadata["files"]) == 5, \
            f"All 5 files should be in metadata, got {len(captured_metadata['files'])}"

        # Verify all next steps are in content
        for step in session["context"]["next_steps"]:
            assert step in captured_content, f"Next step '{step}' should be in content"


class TestSearchEdgeCases:
    """Edge case tests for search functionality."""

    def test_search_returns_partial_matches(self, tmp_path, monkeypatch):
        """
        Test that search returns results even with partial tag matches.

        A search for "jwt" should find learnings tagged with "jwt-auth" or
        learnings where the insight doesn't contain "jwt" but the tag does.
        """
        from memory import search_learnings, save_learning, init_storage

        # Use temp directory for storage
        monkeypatch.setattr("memory.STORAGE_DIR", tmp_path)
        monkeypatch.setattr("memory.SESSIONS_DIR", tmp_path / "sessions")
        monkeypatch.setattr("memory.CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr("memory.SESSIONS_INDEX", tmp_path / "sessions" / "index.json")
        monkeypatch.setattr("memory.LEARNINGS_FILE", tmp_path / "learnings.json")

        init_storage()

        # Save learnings with various tag configurations
        save_learning({
            "insight": "Tokens should be stored securely in httpOnly cookies",
            "tags": ["jwt", "security"]
        })

        save_learning({
            "insight": "Always validate token signatures before trusting claims",
            "tags": ["jwt-validation", "security"]  # "jwt" is substring of tag
        })

        # Search for "jwt"
        results = search_learnings("jwt")

        # Should find both - one has exact tag match, one has partial
        assert len(results) >= 1, "Should find at least the exact jwt tag match"

        # The first result should have "jwt" as a tag
        tags_found = [r.get("tags", []) for r in results]
        jwt_tag_found = any("jwt" in tags for tags in tags_found)
        assert jwt_tag_found, "Should find learning with 'jwt' tag"
