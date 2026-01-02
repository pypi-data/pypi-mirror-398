"""
Rollback command implementation for StackWeaver CLI.

Handles rolling back failed deployments by stopping containers
while preserving volumes by default.
"""

import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from stackweaver.deployer.docker_client import DockerClient, DockerClientError

console = Console()


def rollback_command(
    stack_dir: str = "./stackweaver-stack", project_name: str | None = None, clean: bool = False
) -> None:
    """
    Rollback a StackWeaver deployment.

    Args:
        stack_dir: Directory containing the stack (used to infer project name)
        project_name: Optional project name (defaults to directory name)
        clean: If True, also remove volumes (requires confirmation)
    """
    start_time = time.time()

    # Show banner
    console.print("\n")
    console.print(
        Panel(
            "[bold yellow]StackWeaver Rollback[/bold yellow]\n" "Rolling back your deployment...",
            border_style="yellow",
        )
    )

    # Resolve paths and project name
    stack_path = Path(stack_dir).resolve()

    if not project_name:
        project_name = stack_path.name

    # Step 1: Check Docker is running
    console.print("\n[cyan]→[/cyan] Checking Docker daemon...")

    client = DockerClient()
    if not client.is_running():
        console.print("\n[red]✗[/red] Docker is not running")
        console.print("[dim]Please start Docker Desktop (or Docker daemon) and try again.[/dim]")
        return

    console.print("[green]✓[/green] Docker is running")

    # Step 2: Check if stack exists
    console.print(f"\n[cyan]→[/cyan] Checking for project '{project_name}'...")

    if not client.is_stack_deployed(project_name):
        console.print(f"\n[yellow]⚠[/yellow] No deployment found for project '{project_name}'")
        console.print("[dim]Nothing to roll back.[/dim]")
        client.close()
        return

    console.print(f"[green]✓[/green] Found deployment for '{project_name}'")

    # Step 3: Confirm volume deletion if --clean flag is used
    remove_volumes = False

    if clean:
        console.print(
            "\n[yellow]⚠ WARNING:[/yellow] The --clean flag will [bold red]DELETE ALL DATA[/bold red] (volumes)!"
        )
        console.print("[dim]This action cannot be undone.[/dim]")

        if not Confirm.ask("\nAre you sure you want to remove volumes?", default=False):
            console.print("\n[blue]→[/blue] Cancelled. Volumes will be preserved.")
        else:
            remove_volumes = True
            console.print("[yellow]✓[/yellow] Confirmed: volumes will be removed")

    # Step 4: Run docker compose down
    console.print(
        f"\n[cyan]→[/cyan] Rolling back '{project_name}' "
        f"({'removing volumes' if remove_volumes else 'preserving volumes'})..."
    )

    try:
        result = client.compose_down(project_name=project_name, remove_volumes=remove_volumes)

        if result["success"]:
            console.print("[green]✓[/green] Rollback completed")
        else:
            console.print("[red]✗[/red] Rollback failed")
            if result.get("stderr"):
                console.print(f"[dim]{result['stderr']}[/dim]")
            client.close()
            return

    except DockerClientError as e:
        console.print(f"\n[red]✗[/red] Rollback failed: {e}")
        console.print("[dim]Check the error above and try again.[/dim]")
        client.close()
        return

    # Calculate total time
    total_time = time.time() - start_time

    # Success summary
    console.print("\n")
    console.print(
        Panel(
            f"[bold green]🔄 Rollback complete![/bold green]\n\n"
            f"Completed in {total_time:.2f}s\n\n"
            f"[bold]Status:[/bold]\n"
            f"  • Containers: [green]stopped[/green]\n"
            f"  • Networks: [green]removed[/green]\n"
            f"  • Volumes: [{'red]removed[/red]' if remove_volumes else 'green]preserved (data safe)[/green]'}\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"  • Redeploy: [cyan]stackweaver deploy[/cyan]\n"
            f"  • Check logs: [cyan]docker logs <container>[/cyan]",
            title="Success",
            border_style="green",
        )
    )
    console.print("\n")

    # Close client
    client.close()
