"""
Start command implementation for StackWeaver CLI.

Starts stopped Docker containers.
"""

from pathlib import Path

from rich.panel import Panel

from stackweaver.cli.ui_helpers import EMOJI, console
from stackweaver.deployer.docker_client import DockerClient


def start_command(
    stack_dir: str = "./stackweaver-stack",
    project_name: str | None = None,
) -> None:
    """
    Start a stopped stack.

    Args:
        stack_dir: Directory containing docker-compose.yml
        project_name: Docker Compose project name (auto-detected if None)
    """
    # Show banner
    console.print("\n")
    console.print(
        Panel(
            "[bold green]Start Stack[/bold green]\n" "Starting containers...",
            border_style="green",
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

        # Start stack
        console.print(f"\n[cyan]{EMOJI['arrow']}[/cyan] Starting stack '{project_name}'...")

        compose_file = Path(stack_dir) / "docker-compose.yml"
        if not compose_file.exists():
            console.print(f"\n[red][/red] docker-compose.yml not found in {stack_dir}\n")
            return

        result = docker.compose_start(
            compose_file=compose_file,
            project_name=project_name,
        )

        if result.get("success", False):
            console.print(f"\n[green]{EMOJI['check']}[/green] Stack '{project_name}' started")
            console.print(
                "\n[dim]Run [cyan]stackweaver status[/cyan] to check service health.[/dim]\n"
            )
        else:
            console.print(
                f"\n[red][/red] Failed to start stack: {result.get('error', 'Unknown error')}\n"
            )

    except Exception as e:
        console.print(f"\n[red]{EMOJI['cross']}[/red] Failed to start stack: {e}\n")
