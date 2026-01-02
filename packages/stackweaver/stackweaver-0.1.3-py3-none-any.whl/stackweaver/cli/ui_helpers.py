"""
UI/UX helpers for StackWeaver CLI.

Centralized styles, emojis, and Rich components for consistent CLI experience.
"""

import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
)
from rich.status import Status
from rich.table import Table

# Shared console instance
console = Console()


def _supports_unicode() -> bool:
    """
    Check if terminal supports Unicode emojis.

    Returns:
        True if Unicode is supported, False otherwise
    """
    try:
        # Test if we can encode emojis
        "✅🚀📦".encode(sys.stdout.encoding or "utf-8")
        return True
    except (UnicodeEncodeError, AttributeError):
        return False


# Check Unicode support
_USE_EMOJI = _supports_unicode()

# ASCII-safe spinner for Windows compatibility
ASCII_SPINNER = "dots" if _USE_EMOJI else "line"

# Emojis with ASCII fallbacks
_EMOJI_UNICODE = {
    # Status
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "arrow": "→",
    "check": "✓",
    "cross": "✗",
    # Actions
    "search": "🔍",
    "deploy": "🚀",
    "init": "📦",
    "rollback": "⏮️",
    "status": "📊",
    "logs": "📝",
    "start": "▶️",
    "stop": "⏸️",
    "docker": "🐳",
    "loading": "⏳",
    "sparkles": "✨",
    "security": "🔒",
    # Tools
    "tool": "🔧",
    "database": "🗄️",
    "network": "🌐",
    "volume": "💾",
    "container": "📦",
    "health": "❤️",
    "time": "⏱️",
}

_EMOJI_ASCII = {
    # Status
    "success": "[+]",
    "error": "[X]",
    "warning": "[!]",
    "info": "[i]",
    "arrow": "->",
    "check": "[OK]",
    "cross": "[X]",
    # Actions
    "search": "[?]",
    "deploy": "[*]",
    "init": "[#]",
    "rollback": "[<]",
    "status": "[=]",
    "logs": "[-]",
    "start": "[>]",
    "stop": "[||]",
    "docker": "[D]",
    "loading": "[~]",
    "sparkles": "[*]",
    "security": "[S]",
    # Tools
    "tool": "[T]",
    "database": "[DB]",
    "network": "[N]",
    "volume": "[V]",
    "container": "[C]",
    "health": "[H]",
    "time": "[T]",
}

# Use appropriate icon set
EMOJI = _EMOJI_UNICODE if _USE_EMOJI else _EMOJI_ASCII

# Color schemes
COLORS = {
    "primary": "cyan",
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "info": "blue",
    "accent": "magenta",
    "dim": "dim",
}


# StackWeaver ASCII Banner (pure ASCII for maximum compatibility)
STACKWEAVER_BANNER = """
   ____  _             _    __        __
  / ___|| |_ __ _  ___| | __\\ \\      / /__  __ ___   _____ _ __
  \\___ \\| __/ _` |/ __| |/ / \\ \\ /\\ / / _ \\/ _` \\ \\ / / _ \\ '__|
   ___) | || (_| | (__|   <   \\ V  V /  __/ (_| |\\ V /  __/ |
  |____/ \\__\\__,_|\\___|_|\\_\\   \\_/\\_/ \\___|\\__,_| \\_/ \\___|_|

      Weave production-ready Docker stacks with AI
"""


def show_banner(title: str = "StackWeaver", subtitle: str | None = None) -> None:
    """
    Display StackWeaver banner with optional title/subtitle.

    Args:
        title: Panel title
        subtitle: Optional subtitle text
    """
    content = f"[bold cyan]{STACKWEAVER_BANNER}[/bold cyan]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"

    console.print(Panel(content, title=title, border_style="bright_cyan"))


def show_success(message: str, details: str | None = None) -> None:
    """
    Display success message.

    Args:
        message: Success message
        details: Optional details
    """
    content = f"[bold green]{EMOJI['success']} {message}[/bold green]"
    if details:
        content += f"\n\n[dim]{details}[/dim]"

    console.print(Panel(content, border_style="green"))


def show_error(message: str, fix: str | None = None, details: str | None = None) -> None:
    """
    Display error message with optional fix suggestion.

    Args:
        message: Error message
        fix: Suggested fix
        details: Technical details
    """
    content = f"[bold red]{EMOJI['error']} {message}[/bold red]"

    if fix:
        content += f"\n\n[bold]💡 How to fix:[/bold]\n[yellow]{fix}[/yellow]"

    if details:
        content += f"\n\n[dim]Details: {details}[/dim]"

    console.print(Panel(content, title="Error", border_style="red"))


def show_warning(message: str, action: str | None = None) -> None:
    """
    Display warning message.

    Args:
        message: Warning message
        action: Suggested action
    """
    content = f"[bold yellow]{EMOJI['warning']} {message}[/bold yellow]"

    if action:
        content += f"\n\n[dim]Action: {action}[/dim]"

    console.print(Panel(content, title="Warning", border_style="yellow"))


def show_info(message: str, details: str | None = None) -> None:
    """
    Display info message.

    Args:
        message: Info message
        details: Additional details
    """
    content = f"[bold blue]{EMOJI['info']} {message}[/bold blue]"

    if details:
        content += f"\n\n[dim]{details}[/dim]"

    console.print(Panel(content, title="Info", border_style="blue"))


def create_progress(description: str = "Working...", show_time: bool = False) -> Progress:
    """
    Create a Rich progress bar with spinner and optional time remaining.

    Args:
        description: Progress description
        show_time: Show time remaining column

    Returns:
        Rich Progress instance
    """
    columns = [
        SpinnerColumn(spinner_name=ASCII_SPINNER),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ]

    if show_time:
        columns.append(TimeRemainingColumn())

    return Progress(*columns, console=console)


def create_table(
    title: str,
    columns: list[tuple[str, dict[str, Any]]],
    border_style: str = "cyan",
) -> Table:
    """
    Create a Rich table with consistent styling.

    Args:
        title: Table title
        columns: List of (name, kwargs) tuples for columns
        border_style: Border color

    Returns:
        Rich Table instance
    """
    table = Table(
        title=f"[bold {COLORS['primary']}]{title}[/bold {COLORS['primary']}]",
        show_header=True,
        header_style=f"bold {COLORS['accent']}",
        border_style=border_style,
    )

    for col_name, col_kwargs in columns:
        table.add_column(col_name, **col_kwargs)

    return table


def format_status(status: str, health: str | None = None) -> str:
    """
    Format container status with colors and emojis.

    Args:
        status: Container status (running, exited, etc.)
        health: Health status (healthy, unhealthy, etc.)

    Returns:
        Formatted status string
    """
    if status == "running":
        if health == "healthy":
            return f"[green]{EMOJI['success']}[/green] Healthy"
        elif health == "unhealthy":
            return f"[red]{EMOJI['error']}[/red] Unhealthy"
        elif health == "starting":
            return f"[yellow]{EMOJI['loading']}[/yellow] Starting"
        else:
            return f"[green]{EMOJI['check']}[/green] Running"
    elif status == "exited":
        return f"[red]{EMOJI['cross']}[/red] Stopped"
    elif status == "created":
        return f"[dim]{EMOJI['loading']}[/dim] Created"
    elif status == "restarting":
        return f"[yellow]{EMOJI['loading']}[/yellow] Restarting"
    else:
        return f"[dim]{status}[/dim]"


def format_time(seconds: float) -> str:
    """
    Format time duration in human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def show_step(step: str, emoji: str | None = None) -> None:
    """
    Display a step in the process.

    Args:
        step: Step description
        emoji: Optional emoji (defaults to arrow)
    """
    icon = emoji if emoji else EMOJI["arrow"]
    console.print(f"\n[cyan]{icon}[/cyan] {step}...")


def show_step_success(message: str) -> None:
    """Display successful step completion."""
    console.print(f"[green]{EMOJI['success']}[/green] {message}")


def show_step_warning(message: str) -> None:
    """Display step warning."""
    console.print(f"[yellow]{EMOJI['warning']}[/yellow] {message}")


def show_step_error(message: str) -> None:
    """Display step error."""
    console.print(f"[red]{EMOJI['error']}[/red] {message}")


def show_step_info(message: str) -> None:
    """Display step info."""
    console.print(f"[blue]{EMOJI['info']}[/blue] {message}")


def show_tip(message: str) -> None:
    """
    Display a helpful tip.

    Args:
        message: Tip message
    """
    console.print(f"\n[dim]Tip: {message}[/dim]\n")


@contextmanager
def with_spinner(message: str, success_message: str | None = None) -> Generator[Status, None, None]:
    """
    Context manager for displaying a spinner during an operation.

    Args:
        message: Operation description
        success_message: Message to show on success (optional)

    Yields:
        Rich Status object

    Example:
        with with_spinner("Loading data", "Data loaded!"):
            time.sleep(2)
    """
    status = Status(f"[cyan]{EMOJI['loading']} {message}...", console=console)
    status.start()

    try:
        yield status
        status.stop()
        if success_message:
            show_step_success(success_message)
    except Exception:
        status.stop()
        raise


def create_live_progress(
    title: str = "Progress",
    show_percentage: bool = True,
    show_time: bool = True,
) -> Progress:
    """
    Create an enhanced progress bar with more info.

    Args:
        title: Progress title
        show_percentage: Show percentage complete
        show_time: Show time remaining

    Returns:
        Rich Progress instance
    """
    columns = [
        SpinnerColumn(
            spinner_name=ASCII_SPINNER, finished_text=f"[green]{EMOJI['success']}[/green]"
        ),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40),
    ]

    if show_percentage:
        columns.append(TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))

    if show_time:
        columns.append(TimeRemainingColumn())

    return Progress(*columns, console=console, expand=True)


def show_phase(phase_number: int, total_phases: int, title: str) -> None:
    """
    Display a phase header with progress.

    Args:
        phase_number: Current phase number (1-indexed)
        total_phases: Total number of phases
        title: Phase title

    Example:
        show_phase(2, 5, "Deploying Services")
    """
    percentage = int((phase_number / total_phases) * 100)
    progress_bar = "=" * int(percentage / 10) + ">" + " " * (10 - int(percentage / 10))

    console.print()
    console.print(
        Panel(
            f"[bold cyan]{EMOJI['arrow']} Phase {phase_number}/{total_phases}: {title}[/bold cyan]\n"
            f"[dim]Progress: [{progress_bar}] {percentage}%[/dim]",
            border_style="cyan",
            padding=(0, 1),
        )
    )


def show_task_list(tasks: list[tuple[str, str]]) -> None:
    """
    Display a list of tasks with status.

    Args:
        tasks: List of (task_name, status) tuples
            Status can be: "pending", "running", "done", "failed"

    Example:
        show_task_list([
            ("Pull images", "done"),
            ("Create containers", "running"),
            ("Start services", "pending"),
        ])
    """
    status_icons = {
        "pending": f"[dim]{EMOJI['loading']}[/dim]",
        "running": f"[yellow]{EMOJI['loading']}[/yellow]",
        "done": f"[green]{EMOJI['check']}[/green]",
        "failed": f"[red]{EMOJI['cross']}[/red]",
    }

    console.print()
    for task_name, status in tasks:
        icon = status_icons.get(status, EMOJI["info"])
        color = {
            "pending": "dim",
            "running": "yellow",
            "done": "green",
            "failed": "red",
        }.get(status, "white")

        console.print(f"  {icon} [{color}]{task_name}[/{color}]")


def create_multi_task_progress() -> tuple[Progress, dict[str, TaskID]]:
    """
    Create a progress tracker for multiple parallel tasks.

    Returns:
        Tuple of (Progress instance, task_ids dict)

    Example:
        progress, tasks = create_multi_task_progress()
        with progress:
            tasks["download"] = progress.add_task("Downloading...", total=100)
            tasks["process"] = progress.add_task("Processing...", total=50)

            # Update tasks
            progress.update(tasks["download"], advance=10)
    """
    progress = Progress(
        SpinnerColumn(spinner_name=ASCII_SPINNER),
        TextColumn("[bold]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )

    return progress, {}
