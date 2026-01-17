#!/usr/bin/env python3
"""
Flow Guardian MCP Server
Provides persistent memory for Claude Code sessions.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Flow Guardian imports (reuse from CLI)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow.state import load_config, load_last_capture, save_last_capture, LastCapture, FlowConfig
from flow.git_utils import get_repo, get_git_state, get_changes_since
from flow.backboard_client import (
    store_context_snapshot,
    recall_context,
    store_learning,
    store_team_learning,
    query_team_memory
)

# Initialize MCP server
server = Server("flow-guardian")

# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOLS = [
    Tool(
        name="flow_recall",
        description="""Recall previous coding context from Flow Guardian's memory.

USE THIS WHEN:
- User says "continue from yesterday/last time"
- User references previous work without full context
- Starting a new session on an existing project
- User asks "what were we working on?"

The tool searches semantic memory and returns relevant past context including:
- What was being worked on
- Key decisions made
- Suggested next steps""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for (e.g., 'auth refactoring', 'database migration', 'recent work')"
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="flow_capture",
        description="""Capture current coding context to Flow Guardian's memory.

USE THIS WHEN:
- User says they need to stop/leave/take a break
- Session is ending
- Switching to a different task
- User asks to "save progress" or "remember this"

Captures:
- Summary of current work
- Key decisions made
- Next steps to continue
- Git state (branch, files)""",
        inputSchema={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief description of what we were working on"
                },
                "decisions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key decisions made during this session"
                },
                "next_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What should be done next when returning"
                },
                "blockers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Any blockers or issues to remember"
                }
            },
            "required": ["summary"]
        }
    ),
    Tool(
        name="flow_learn",
        description="""Store a learning or insight for future reference.

USE THIS WHEN:
- We discover something important (bug cause, best practice, gotcha)
- User says "remember this" or "note this down"
- Finding a solution that others might need
- Debugging reveals root cause

Set share_with_team=true for insights that would help teammates.""",
        inputSchema={
            "type": "object",
            "properties": {
                "insight": {
                    "type": "string",
                    "description": "The learning or insight to store"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to categorize (e.g., ['auth', 'jwt', 'bug'])"
                },
                "share_with_team": {
                    "type": "boolean",
                    "description": "Whether to share with team (default: false)",
                    "default": False
                }
            },
            "required": ["insight"]
        }
    ),
    Tool(
        name="flow_team",
        description="""Search team's shared knowledge base.

USE THIS WHEN:
- Looking for solutions others may have found
- User asks "has anyone dealt with..."
- Debugging common issues
- Looking for team conventions or patterns""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in team knowledge"
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="flow_status",
        description="""Get current Flow Guardian status and last captured context.

USE THIS WHEN:
- User asks about Flow Guardian status
- Checking if memory is connected
- Seeing what was last captured""",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
]

# ============================================================
# TOOL HANDLERS
# ============================================================

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return list of available tools."""
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from Claude Code."""

    try:
        if name == "flow_recall":
            return await tool_flow_recall(arguments)
        elif name == "flow_capture":
            return await tool_flow_capture(arguments)
        elif name == "flow_learn":
            return await tool_flow_learn(arguments)
        elif name == "flow_team":
            return await tool_flow_team(arguments)
        elif name == "flow_status":
            return await tool_flow_status(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

async def tool_flow_recall(arguments: dict) -> list[TextContent]:
    """Recall previous coding context."""

    config = load_config()
    if not config:
        return [TextContent(
            type="text",
            text="Flow Guardian not initialized.\n\nRun `flow init --user yourname` in terminal first."
        )]

    query = arguments.get("query", "recent work")

    # Get semantic recall from Backboard
    recall_query = f"""Recall coding context about: {query}

Please provide:
1. What was being worked on
2. Key decisions made
3. Important files involved
4. Suggested next steps

Be specific and actionable."""

    try:
        result = await recall_context(config.personal_thread_id, recall_query)
    except Exception as e:
        result = f"Could not reach memory service: {str(e)}"

    # Also include last local capture for immediate context
    last_capture = load_last_capture()

    response = "## Retrieved Context\n\n"
    response += result if result else "No matching context found in memory."

    if last_capture:
        response += "\n\n---\n\n## Last Captured Session\n\n"
        response += f"**When:** {last_capture.timestamp[:19].replace('T', ' ')}\n"
        response += f"**Branch:** `{last_capture.branch}`\n"
        response += f"**Summary:** {last_capture.summary}\n"
        if last_capture.files:
            response += f"**Files:** `{', '.join(last_capture.files[:5])}`"
            if len(last_capture.files) > 5:
                response += f" (+{len(last_capture.files) - 5} more)"

    return [TextContent(type="text", text=response)]


async def tool_flow_capture(arguments: dict) -> list[TextContent]:
    """Capture current coding context."""

    config = load_config()
    if not config:
        return [TextContent(
            type="text",
            text="Flow Guardian not initialized.\n\nRun `flow init --user yourname` in terminal first."
        )]

    # Extract arguments
    summary = arguments.get("summary", "Coding session")
    decisions = arguments.get("decisions", [])
    next_steps = arguments.get("next_steps", [])
    blockers = arguments.get("blockers", [])

    # Get git state
    repo = get_repo()
    if repo:
        git_state = get_git_state(repo)
        branch = git_state.get("branch", "unknown")
        head = git_state.get("head", "unknown")
        files = git_state.get("modified_files", [])
    else:
        branch = "unknown"
        head = "unknown"
        files = []

    # Build context object
    context = {
        "summary": summary,
        "decisions": decisions,
        "next_steps": next_steps,
        "blockers": blockers,
        "branch": branch,
        "key_files": files[:10],
        "hypothesis": None,
        "complexity": "medium",
        "source": "claude_code_mcp"
    }

    # Store to Backboard
    try:
        await store_context_snapshot(config.personal_thread_id, context)
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Could not save to cloud memory: {str(e)}\n\nLocal state will still be saved."
        )]

    # Save local state
    timestamp = datetime.now().isoformat()
    save_last_capture(LastCapture(
        timestamp=timestamp,
        branch=branch,
        files=files,
        summary=summary,
        git_head=head
    ))

    # Build response
    response = "## Context Captured\n\n"
    response += f"**Summary:** {summary}\n\n"

    if decisions:
        response += "**Decisions Made:**\n"
        for d in decisions:
            response += f"  - {d}\n"
        response += "\n"

    if next_steps:
        response += "**Next Steps (for next session):**\n"
        for s in next_steps:
            response += f"  - {s}\n"
        response += "\n"

    if blockers:
        response += "**Blockers to Remember:**\n"
        for b in blockers:
            response += f"  - {b}\n"
        response += "\n"

    response += f"**Branch:** `{branch}`\n"
    if files:
        response += f"**Files:** `{', '.join(files[:5])}`\n"

    response += "\n---\n*You can pick up where you left off by saying \"continue from last session\"*"

    return [TextContent(type="text", text=response)]


async def tool_flow_learn(arguments: dict) -> list[TextContent]:
    """Store a learning or insight."""

    config = load_config()
    if not config:
        return [TextContent(
            type="text",
            text="Flow Guardian not initialized."
        )]

    insight = arguments.get("insight")
    tags = arguments.get("tags", [])
    share = arguments.get("share_with_team", False)

    if not insight:
        return [TextContent(type="text", text="No insight provided.")]

    try:
        if share and config.team_thread_id:
            await store_team_learning(
                config.team_thread_id,
                insight,
                config.username,
                tags
            )
            response = f"## Shared with Team\n\n"
            response += f"**Insight:** {insight}\n"
            response += f"**Author:** {config.username}\n"
            if tags:
                response += f"**Tags:** {', '.join(tags)}\n"
            response += "\n*Your teammates can find this with `flow team` search.*"
        else:
            await store_learning(config.personal_thread_id, insight, tags)
            response = f"## Learning Saved\n\n"
            response += f"**Insight:** {insight}\n"
            if tags:
                response += f"**Tags:** {', '.join(tags)}\n"
            response += "\n*You can recall this later with `flow recall`.*"

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"Could not save learning: {str(e)}")]


async def tool_flow_team(arguments: dict) -> list[TextContent]:
    """Search team's shared knowledge."""

    config = load_config()
    if not config:
        return [TextContent(type="text", text="Flow Guardian not initialized.")]

    if not config.team_thread_id:
        return [TextContent(
            type="text",
            text="Team memory not configured.\n\nRun `flow init --user yourname --team teamname` to set up team memory."
        )]

    query = arguments.get("query", "")
    if not query:
        return [TextContent(type="text", text="No search query provided.")]

    try:
        result = await query_team_memory(config.team_thread_id, query)

        response = f"## Team Knowledge: \"{query}\"\n\n"
        response += result if result else "No matching team knowledge found."

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return [TextContent(type="text", text=f"Could not search team memory: {str(e)}")]


async def tool_flow_status(arguments: dict) -> list[TextContent]:
    """Get Flow Guardian status."""

    config = load_config()
    last_capture = load_last_capture()

    response = "## Flow Guardian Status\n\n"

    if config:
        response += f"**User:** {config.username}\n"
        response += f"**Personal Memory:** Connected\n"
        response += f"**Team Memory:** {'Connected' if config.team_thread_id else 'Not configured'}\n"
    else:
        response += "**Status:** Not initialized\n"
        response += "\n*Run `flow init --user yourname` in terminal to set up.*\n"
        return [TextContent(type="text", text=response)]

    response += "\n---\n\n"

    if last_capture:
        response += "## Last Capture\n\n"
        response += f"**When:** {last_capture.timestamp[:19].replace('T', ' ')}\n"
        response += f"**Branch:** `{last_capture.branch}`\n"
        response += f"**Summary:** {last_capture.summary}\n"
        if last_capture.files:
            response += f"**Files:** `{', '.join(last_capture.files[:5])}`\n"
    else:
        response += "*No context captured yet. Use `flow_capture` to save your first session.*"

    return [TextContent(type="text", text=response)]

# ============================================================
# MAIN ENTRY POINT
# ============================================================

async def main():
    """Run the MCP server."""

    # Verify environment
    if not os.environ.get("BACKBOARD_API_KEY"):
        print("Warning: BACKBOARD_API_KEY not set", file=sys.stderr)

    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
