"""
Logs command implementation for StackWeaver CLI.

Displays Docker container logs for deployed stacks.
"""

from pathlib import Path

from rich.panel import Panel

from stackweaver.cli.ui_helpers import EMOJI, console
from stackweaver.deployer.docker_client import DockerClient


def logs_command(
    stack_dir: str = "./stackweaver-stack",
    project_name: str | None = None,
    service: str | None = None,
    follow: bool = False,
    tail: int = 100,
) -> None:
    """
    Show logs for deployed stack.

    Args:
        stack_dir: Directory containing docker-compose.yml
        project_name: Docker Compose project name (auto-detected if None)
        service: Specific service name (shows all if None)
        follow: Follow log output (tail -f)
        tail: Number of lines to show from end
    """
    # Show banner
    console.print("\n")
    if follow:
        console.print(
            Panel(
                "[bold cyan]Live Logs[/bold cyan]\n" "Press Ctrl+C to stop...",
                border_style="cyan",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold cyan]Container Logs[/bold cyan]\n" f"Showing last {tail} lines...",
                border_style="cyan",
            )
        )

    try:
        # Initialize Docker client
        docker = DockerClient()

        # Check Docker is running
        if not docker.is_running():
            console.print(
                "\n[red][/red] Docker is not running. "
                "Please start Docker Desktop and try again.\n"
            )
            return

        # Determine project name
        if not project_name:
            stack_path = Path(stack_dir)
            if not stack_path.exists():
                console.print(f"\n[yellow]⚠[/yellow] Stack directory not found: {stack_dir}\n")
                return
            project_name = stack_path.name

        # Check if stack is deployed
        if not docker.is_stack_deployed(project_name):
            console.print(
                f"\n[yellow]⚠[/yellow] No stack deployed with project name: {project_name}\n"
            )
            console.print("[dim]Run [cyan]stackweaver deploy[/cyan] to deploy a stack.[/dim]\n")
            return

        # Get logs
        console.print("\n[cyan][/cyan] Fetching logs...\n")

        compose_file = Path(stack_dir) / "docker-compose.yml"
        if not compose_file.exists():
            console.print(f"\n[red][/red] docker-compose.yml not found in {stack_dir}\n")
            return

        logs = docker.get_logs(
            compose_file=compose_file,
            project_name=project_name,
            service=service,
            follow=follow,
            tail=tail,
        )

        # Display logs
        if logs:
            console.print(logs)
        else:
            console.print("[dim]No logs available.[/dim]\n")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Stopped following logs.[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]{EMOJI['cross']}[/red] Failed to get logs: {e}\n")
