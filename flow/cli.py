"""Flow Guardian CLI commands."""
import asyncio
from typing import Optional, List
import typer
from rich.console import Console

from .state import (
    FlowConfig, LastCapture,
    load_config, save_config,
    load_last_capture, save_last_capture
)
from .git_utils import get_repo, get_git_state, get_changes_since
from .cerebras_client import analyze_context, generate_restoration
from .backboard_client import (
    create_assistant, create_thread,
    store_context_snapshot, store_learning, store_team_learning,
    recall_context, recall_personal, query_team_memory
)
from .ui import (
    capture_panel, restore_panel, error_panel,
    status_panel, team_panel, success_message, info_message,
    console
)
from datetime import datetime

app = typer.Typer(
    name="flow",
    help="Flow Guardian - Return to flow state in 30 seconds.",
    add_completion=False
)


@app.command()
def init(
    user: str = typer.Option(..., "--user", "-u", help="Your username"),
    team: Optional[str] = typer.Option(None, "--team", "-t", help="Team name (optional)")
):
    """Initialize Flow Guardian for this project."""
    console.print("[blue]Setting up Flow Guardian...[/blue]")

    async def setup():
        # Create personal assistant
        console.print("  Creating personal memory...")
        personal_assistant_id = await create_assistant(f"flow-guardian-personal-{user}")
        personal_thread_id = await create_thread(personal_assistant_id)

        team_assistant_id = None
        team_thread_id = None

        if team:
            console.print("  Creating team memory...")
            team_assistant_id = await create_assistant(f"flow-guardian-team-{team}")
            team_thread_id = await create_thread(team_assistant_id)

        config = FlowConfig(
            personal_assistant_id=personal_assistant_id,
            personal_thread_id=personal_thread_id,
            team_assistant_id=team_assistant_id,
            team_thread_id=team_thread_id,
            username=user
        )
        save_config(config)

        console.print("[green]Personal memory initialized[/green]")
        if team:
            console.print(f"[green]Team memory initialized for '{team}'[/green]")
        console.print("\n[bold]Ready![/bold] Use 'flow capture' before interruptions.")

    try:
        asyncio.run(setup())
    except Exception as e:
        error_panel(f"Setup failed: {str(e)}", "Check your API keys in .env")
        raise typer.Exit(1)


@app.command()
def capture(
    trigger: str = typer.Option("interruption", "--trigger", "-t", help="Why are you stopping? (meeting, slack, break, etc.)")
):
    """Capture your current context before an interruption."""
    config = load_config()
    if not config:
        error_panel("Flow Guardian not initialized", "Run 'flow init --user yourname' first")
        raise typer.Exit(1)

    repo = get_repo()
    if not repo:
        error_panel("Not in a git repository", "Flow Guardian requires git for context capture")
        raise typer.Exit(1)

    console.print("[blue]Capturing context...[/blue]")

    # Get git state
    git_state = get_git_state(repo)

    # Analyze with Cerebras
    try:
        context = analyze_context(
            branch=git_state["branch"],
            modified_files=git_state["modified_files"],
            recent_commits=git_state["recent_commits"],
            diff_summary=git_state["diff_summary"]
        )
        context_dict = context.model_dump()
    except Exception as e:
        error_panel(f"Analysis failed: {str(e)}", "Check your CEREBRAS_API_KEY")
        raise typer.Exit(1)

    # Add git info to context
    context_dict["branch"] = git_state["branch"]

    # Store to Backboard
    async def store():
        await store_context_snapshot(config.personal_thread_id, context_dict)

    try:
        asyncio.run(store())
    except Exception as e:
        error_panel(f"Storage failed: {str(e)}", "Check your BACKBOARD_API_KEY")
        raise typer.Exit(1)

    # Save local state
    save_last_capture(LastCapture(
        timestamp=datetime.now().isoformat(),
        branch=git_state["branch"],
        files=git_state["modified_files"],
        summary=context_dict["summary"],
        git_head=git_state["head"]
    ))

    # Display panel
    capture_panel(context_dict, trigger)


@app.command()
def resume():
    """Restore your context after returning from an interruption."""
    config = load_config()
    if not config:
        error_panel("Flow Guardian not initialized", "Run 'flow init --user yourname' first")
        raise typer.Exit(1)

    last_capture = load_last_capture()
    if not last_capture:
        error_panel("No previous capture found", "Run 'flow capture' before interruptions")
        raise typer.Exit(1)

    console.print("[blue]Restoring flow...[/blue]")

    repo = get_repo()
    changes = ""
    if repo:
        changes = get_changes_since(repo, last_capture.git_head)

    # Recall from Backboard
    async def recall():
        return await recall_context(
            config.personal_thread_id,
            "What was I working on in my last context snapshot? Summarize briefly."
        )

    try:
        recalled = asyncio.run(recall())
    except Exception as e:
        recalled = last_capture.summary

    # Generate restoration with Cerebras
    context = {
        "summary": last_capture.summary,
        "branch": last_capture.branch,
        "files": last_capture.files,
        "recalled": recalled
    }

    try:
        restoration = generate_restoration(context, changes)
    except Exception as e:
        # Fallback if Cerebras fails
        restoration = {
            "context_summary": last_capture.summary,
            "hypothesis": None,
            "changes_impact": changes if changes else "No changes detected",
            "suggested_action": "Continue where you left off"
        }

    # Display panel
    restore_panel(restoration, last_capture.timestamp[:19])


@app.command()
def learn(
    insight: str = typer.Argument(..., help="The insight or learning to save"),
    team: bool = typer.Option(False, "--team", help="Share with team"),
    tags: Optional[List[str]] = typer.Option(None, "--tags", "-t", help="Tags for categorization")
):
    """Save a learning or insight for future reference."""
    config = load_config()
    if not config:
        error_panel("Flow Guardian not initialized", "Run 'flow init --user yourname' first")
        raise typer.Exit(1)

    async def store():
        if team:
            if not config.team_thread_id:
                error_panel("Team memory not configured", "Re-run 'flow init' with --team option")
                raise typer.Exit(1)
            await store_team_learning(config.team_thread_id, insight, config.username, tags)
        else:
            await store_learning(config.personal_thread_id, insight, tags)

    try:
        asyncio.run(store())
        if team:
            success_message(f"Shared with team: {insight[:50]}...")
        else:
            success_message(f"Saved: {insight[:50]}...")
    except Exception as e:
        error_panel(f"Failed to save: {str(e)}")
        raise typer.Exit(1)


@app.command(name="recall")
def recall_cmd(
    query: str = typer.Argument(..., help="What to search for")
):
    """Search your personal learnings."""
    config = load_config()
    if not config:
        error_panel("Flow Guardian not initialized")
        raise typer.Exit(1)

    async def search():
        return await recall_personal(config.personal_thread_id, query)

    try:
        result = asyncio.run(search())
        console.print(f"\n[cyan]{result}[/cyan]\n")
    except Exception as e:
        error_panel(f"Search failed: {str(e)}")
        raise typer.Exit(1)


@app.command(name="team")
def team_cmd(
    query: str = typer.Argument(..., help="What to search for in team knowledge")
):
    """Search team's shared knowledge base."""
    config = load_config()
    if not config:
        error_panel("Flow Guardian not initialized")
        raise typer.Exit(1)

    if not config.team_thread_id:
        error_panel("Team memory not configured", "Re-run 'flow init' with --team option")
        raise typer.Exit(1)

    async def search():
        return await query_team_memory(config.team_thread_id, query)

    try:
        result = asyncio.run(search())
        team_panel(result, query)
    except Exception as e:
        error_panel(f"Search failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def status():
    """Show Flow Guardian status and last capture."""
    config = load_config()
    if not config:
        error_panel("Flow Guardian not initialized", "Run 'flow init --user yourname' first")
        raise typer.Exit(1)

    last_capture = load_last_capture()

    config_dict = config.model_dump()
    capture_dict = last_capture.model_dump() if last_capture else None

    status_panel(config_dict, capture_dict)


if __name__ == "__main__":
    app()
