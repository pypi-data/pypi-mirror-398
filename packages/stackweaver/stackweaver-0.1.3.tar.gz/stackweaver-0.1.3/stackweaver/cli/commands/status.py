"""
Status command implementation for StackWeaver CLI.

Displays the status of deployed Docker stacks.
"""

from pathlib import Path
from typing import Any

from rich.panel import Panel

from stackweaver.cli.ui_helpers import (
    EMOJI,
    console,
    create_table,
    show_phase,
    show_step_error,
    show_step_success,
    show_step_warning,
    with_spinner,
)
from stackweaver.deployer.docker_client import DockerClient


def status_command(
    stack_dir: str = "./stackweaver-stack",
    project_name: str | None = None,
) -> None:
    """
    Show status of deployed stack.

    Args:
        stack_dir: Directory containing docker-compose.yml
        project_name: Docker Compose project name (auto-detected if None)
    """
    # Show banner
    console.print("\n")
    console.print(
        Panel(
            f"[bold cyan]{EMOJI['status']} Stack Status[/bold cyan]\n"
            "Checking deployed services...",
            border_style="cyan",
        )
    )

    try:
        # Phase 1: Initialization
        show_phase(1, 2, "Initialization")

        # Initialize Docker client
        with with_spinner("Checking Docker daemon"):
            docker = DockerClient()

            # Check Docker is running
            if not docker.is_running():
                show_step_error("Docker is not running")
                console.print("[dim]Please start Docker Desktop and try again.[/dim]\n")
                return

        # Determine project name
        if not project_name:
            stack_path = Path(stack_dir)
            if not stack_path.exists():
                show_step_warning(f"Stack directory not found: {stack_dir}")
                return
            project_name = stack_path.name

        # Phase 2: Status Check
        show_phase(2, 2, "Status Check")

        # Check if stack is deployed
        with with_spinner(f"Checking stack: {project_name}"):
            if not docker.is_stack_deployed(project_name):
                show_step_warning(f"No stack deployed with project name: {project_name}")
                console.print("[dim]Run [cyan]stackweaver deploy[/cyan] to deploy a stack.[/dim]\n")
                return

            # Get containers
            containers_raw = docker.get_containers(project_name)

        if not containers_raw:
            show_step_warning(f"No containers found for project: {project_name}")
            return

        # Convert Container objects to dicts
        containers = []
        for c in containers_raw:
            containers.append(
                {
                    "name": c.name,
                    "status": c.status,
                    "health": c.attrs.get("State", {}).get("Health", {}).get("Status", "none"),
                    "uptime": c.attrs.get("State", {}).get("StartedAt", "unknown"),
                    "ports": c.ports,
                    "labels": c.labels,
                }
            )

        # Display status
        show_step_success(f"Stack [cyan]{project_name}[/cyan] is deployed")
        console.print(f"[dim]Found {len(containers)} service(s)[/dim]")

        # Create status table
        table = create_status_table(containers)
        console.print("\n")
        console.print(table)

        # Show access URLs
        show_access_urls(containers)

        console.print("\n")

    except Exception as e:
        show_step_error(f"Failed to get status: {e}")


def create_status_table(containers: list[dict]) -> object:
    """
    Create a Rich table displaying container status.

    Args:
        containers: List of container info dicts

    Returns:
        Rich Table object
    """
    columns: list[tuple[str, dict[str, Any]]] = [
        ("Service", {"style": "cyan", "no_wrap": True}),
        ("Status", {"justify": "center"}),
        ("Health", {"justify": "center"}),
        ("Uptime", {"style": "dim"}),
    ]

    table = create_table(f"{EMOJI['container']} Container Status", columns, border_style="cyan")

    for container in containers:
        name = container.get("name", "unknown")
        status = container.get("status", "unknown")
        health = container.get("health", "unknown")
        uptime = container.get("uptime", "unknown")

        # Color code status
        if status == "running":
            status_text = f"[green]{EMOJI['success']}[/green] Running"
        elif status == "exited":
            status_text = f"[red]{EMOJI['error']}[/red] Stopped"
        else:
            status_text = f"[yellow]{EMOJI['warning']}[/yellow] {status}"

        # Color code health
        if health == "healthy":
            health_text = f"[green]{EMOJI['check']}[/green] Healthy"
        elif health == "unhealthy":
            health_text = f"[red]{EMOJI['cross']}[/red] Unhealthy"
        elif health == "starting":
            health_text = f"[yellow]{EMOJI['loading']}[/yellow] Starting"
        else:
            health_text = "[dim]—[/dim]"

        table.add_row(name, status_text, health_text, uptime)

    return table


def show_access_urls(containers: list[dict]) -> None:
    """
    Display access URLs for services.

    Args:
        containers: List of container info dicts
    """
    urls = []
    for container in containers:
        name = container.get("name", "")
        if name and not name.endswith("-db") and not name.endswith("-redis"):
            # Generate Traefik URL
            service_name = name.replace("_", "-").lower()
            urls.append(f"http://{service_name}.localhost")

    if urls:
        console.print(f"\n[bold]{EMOJI['network']} Access URLs:[/bold]")
        for url in urls:
            console.print(f"  • [cyan]{url}[/cyan]")
