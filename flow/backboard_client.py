"""Backboard.io client for persistent memory."""
import os
import httpx
from datetime import datetime
from typing import Optional

BASE_URL = os.environ.get("BACKBOARD_BASE_URL", "https://app.backboard.io/api")
API_KEY = os.environ.get("BACKBOARD_API_KEY")


def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }


async def create_assistant(name: str) -> str:
    """Create a Backboard assistant."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/assistants",
            headers=_headers(),
            json={
                "name": name,
                "llm_provider": "cerebras",
                "llm_model_name": "llama-3.3-70b",
                "tools": []
            }
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def create_thread(assistant_id: str) -> str:
    """Create a thread within an assistant."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/assistants/{assistant_id}/threads",
            headers=_headers()
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def store_context_snapshot(thread_id: str, context: dict):
    """Store context snapshot without LLM call."""
    content = f"""## Context Snapshot
**Working on:** {context.get('summary', 'unknown')}
**Hypothesis:** {context.get('hypothesis', 'none')}
**Files:** {', '.join(context.get('key_files', []))}
**Branch:** {context.get('branch', 'unknown')}
**Next steps:** {', '.join(context.get('next_steps', []))}"""

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": content,
                "metadata": {
                    "type": "context_snapshot",
                    "timestamp": datetime.now().isoformat(),
                    **context
                },
                "send_to_llm": False
            }
        )
        resp.raise_for_status()
        return resp.json()


async def store_learning(thread_id: str, learning: str, tags: list = None):
    """Store a learning for future recall."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": f"**Learning:** {learning}",
                "metadata": {
                    "type": "learning",
                    "timestamp": datetime.now().isoformat(),
                    "tags": tags or []
                },
                "send_to_llm": False
            }
        )
        resp.raise_for_status()
        return resp.json()


async def recall_context(thread_id: str, query: str) -> str:
    """Query memory with semantic recall."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": query,
                "memory": "auto",
                "send_to_llm": True
            }
        )
        resp.raise_for_status()
        return resp.json().get("content", "")


async def store_team_learning(thread_id: str, learning: str, author: str, tags: list = None):
    """Store learning to team memory."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": f"**Team Learning** (from {author}): {learning}",
                "metadata": {
                    "type": "team_learning",
                    "author": author,
                    "timestamp": datetime.now().isoformat(),
                    "tags": tags or []
                },
                "send_to_llm": False
            }
        )
        resp.raise_for_status()
        return resp.json()


async def query_team_memory(thread_id: str, query: str) -> str:
    """Search team's shared learnings."""
    return await recall_context(
        thread_id,
        f"Search team learnings for: {query}\n\nSummarize relevant learnings with authors."
    )


async def recall_personal(thread_id: str, query: str) -> str:
    """Search personal learnings."""
    return await recall_context(thread_id, f"Search my learnings for: {query}")
