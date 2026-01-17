"""Rich terminal UI for Flow Guardian."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

FLOW_GREEN = "#50C878"
FLOW_BLUE = "#4A90D9"
FLOW_RED = "#FF6B6B"


def capture_panel(context: dict, trigger: str):
    """Display capture confirmation."""
    content = Table.grid(padding=(0, 2))
    content.add_column(style="bold cyan", justify="right")
    content.add_column()

    content.add_row("Working on", context.get("summary", "Unknown"))
    if context.get("hypothesis"):
        content.add_row("Hypothesis", context["hypothesis"])
    content.add_row("Key files", ", ".join(context.get("key_files", [])[:3]))
    content.add_row("Complexity", context.get("complexity", "unknown"))
    content.add_row("Trigger", trigger)

    panel = Panel(
        content,
        title="[bold green]Context Captured[/bold green]",
        subtitle="[dim]Use 'flow resume' when you return[/dim]",
        border_style=FLOW_GREEN,
        box=box.ROUNDED
    )
    console.print(panel)


def restore_panel(restoration: dict, capture_time: str):
    """Display restoration panel."""
    content = Table.grid(padding=(0, 2))
    content.add_column(style="bold cyan", justify="right", width=15)
    content.add_column()

    content.add_row("You were", restoration.get("context_summary", "Unknown"))

    if restoration.get("hypothesis"):
        content.add_row("Your theory", restoration["hypothesis"])

    changes = restoration.get("changes_impact", "No relevant changes")
    if changes and changes != "No relevant changes":
        content.add_row(
            Text("Changes", style="bold yellow"),
            Text(changes, style="yellow")
        )
    else:
        content.add_row("Changes", Text("No relevant changes", style="dim"))

    content.add_row(
        Text("Next step", style="bold green"),
        Text(restoration.get("suggested_action", "Continue"), style="green")
    )

    panel = Panel(
        content,
        title=f"[bold blue]Flow Restored[/bold blue]",
        subtitle=f"[dim]Away since {capture_time}[/dim]",
        border_style=FLOW_BLUE,
        box=box.ROUNDED
    )
    console.print()
    console.print(panel)


def error_panel(message: str, hint: str = None):
    """Display error."""
    content = Text(message, style="red")
    if hint:
        content.append(f"\n\n{hint}", style="dim")

    panel = Panel(content, title="[bold red]Error[/bold red]", border_style=FLOW_RED, box=box.ROUNDED)
    console.print(panel)


def status_panel(config: dict, last_capture: dict = None):
    """Display status."""
    content = Table.grid(padding=(0, 2))
    content.add_column(style="bold", justify="right")
    content.add_column()

    content.add_row("User", config.get("username", "Unknown"))
    content.add_row("Personal memory", "Connected" if config.get("personal_assistant_id") else "Not set")
    content.add_row("Team memory", "Connected" if config.get("team_assistant_id") else "Optional")

    if last_capture:
        content.add_row("", "")
        content.add_row("Last capture", last_capture.get("timestamp", "Unknown")[:19])
        content.add_row("Branch", last_capture.get("branch", "Unknown"))
        content.add_row("Summary", last_capture.get("summary", "Unknown")[:50])

    panel = Panel(content, title="[bold]Flow Guardian Status[/bold]", border_style="blue", box=box.ROUNDED)
    console.print(panel)


def team_panel(result: str, query: str):
    """Display team search result."""
    panel = Panel(
        f"[cyan]{result}[/cyan]",
        title=f"[bold magenta]Team Knowledge: '{query}'[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED
    )
    console.print(panel)


def success_message(message: str):
    """Display success message."""
    console.print(f"[green]{message}[/green]")


def info_message(message: str):
    """Display info message."""
    console.print(f"[blue]{message}[/blue]")
