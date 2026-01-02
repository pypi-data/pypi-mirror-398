"""
Deploy command implementation for StackWeaver CLI.

Handles Docker Compose stack deployment with health checking and URL display.
"""

import time
from pathlib import Path

import yaml
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from stackweaver.cli.ui_helpers import (
    EMOJI,
    console,
    show_phase,
    show_step,
    show_step_error,
    show_step_success,
    show_step_warning,
    show_task_list,
    with_spinner,
)
from stackweaver.core.errors import (
    ComposeFileNotFoundError,
    DockerNotRunningError,
    StackWeaverError,
)
from stackweaver.deployer.docker_client import DockerClient, DockerClientError


def _validate_secrets(env_file: Path) -> tuple[bool, list[str]]:
    """
    Validate secrets in .env file.

    Args:
        env_file: Path to .env file

    Returns:
        Tuple of (all_valid, warnings)
    """
    warnings: list[str] = []

    if not env_file.exists():
        return True, warnings  # No env file to validate

    # Read .env
    content = env_file.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Check for placeholders
    placeholder_count = 0
    weak_secrets = []

    for line in lines:
        # Skip comments and empty lines
        if line.strip().startswith("#") or not line.strip() or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Check for placeholders
        if "<generate-secure-secret" in value:
            placeholder_count += 1
            continue

        # Check secret strength for password/secret fields
        if any(
            secret_key in key.upper()
            for secret_key in ["PASSWORD", "SECRET", "KEY", "TOKEN", "PASS"]
        ):
            # Check minimum length
            if len(value) < 16:
                weak_secrets.append(f"{key} (too short: {len(value)} chars)")
            elif len(value) < 32:
                warnings.append(f"{key} is weak (< 32 chars)")

    # Build warnings
    if placeholder_count > 0:
        warnings.append(
            f"{placeholder_count} secrets not generated (run: stackweaver secrets generate)"
        )

    if weak_secrets:
        for weak in weak_secrets:
            warnings.append(f"Weak secret: {weak}")

    return len(weak_secrets) == 0, warnings


def _analyze_compose_file(compose_file: Path) -> dict:
    """
    Analyze a docker-compose.yml file and extract deployment information.

    Args:
        compose_file: Path to docker-compose.yml

    Returns:
        Dictionary containing images, services, networks, volumes
    """
    try:
        with open(compose_file, encoding="utf-8") as f:
            compose_data = yaml.safe_load(f)

        images = []
        services = []
        networks = []
        volumes = []

        # Extract services and images
        if "services" in compose_data:
            for service_name, service_config in compose_data["services"].items():
                services.append(service_name)
                if "image" in service_config:
                    images.append(service_config["image"])

        # Extract networks
        if "networks" in compose_data:
            networks = list(compose_data["networks"].keys())

        # Extract volumes
        if "volumes" in compose_data:
            volumes = list(compose_data["volumes"].keys())

        return {
            "images": images,
            "services": services,
            "networks": networks,
            "volumes": volumes,
        }

    except Exception as e:
        return {
            "images": [],
            "services": [],
            "networks": [],
            "volumes": [],
            "error": str(e),
        }


def _wait_for_healthy_with_progress(
    client: DockerClient, project_name: str = "stackweaver", timeout: int = 120
) -> dict:
    """
    Wait for containers to be healthy with real-time progress display.

    Args:
        client: Docker client instance
        project_name: Docker Compose project name
        timeout: Maximum time to wait (seconds)

    Returns:
        Dictionary with container statuses

    Raises:
        DockerClientError: If timeout is reached or containers fail
    """
    import time

    start_time = time.time()
    check_interval = 0.5  # 500ms updates

    # Create progress display
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )

    # Get initial containers
    containers = client.get_containers(project_name)
    if not containers:
        raise DockerClientError(f"No containers found for project: {project_name}")

    # Create tasks for each container
    container_tasks: dict[str, TaskID] = {}
    with progress:
        # Add overall progress task
        overall_task = progress.add_task(
            f"[cyan]Deploying {project_name}...", total=len(containers)
        )

        # Add task for each container
        for container in containers:
            task_id = progress.add_task(f"  [{container.name}] Starting...", total=100, start=False)
            container_tasks[container.name] = task_id

        # Monitor containers until all are ready or timeout
        ready_count = 0
        while time.time() - start_time < timeout:
            containers = client.get_containers(project_name)
            containers_status = {}
            ready_count = 0

            for container in containers:
                container.reload()

                name = container.name
                status = container.status
                health = container.attrs.get("State", {}).get("Health", {}).get("Status", "none")

                containers_status[name] = {
                    "status": status,
                    "health": health,
                    "id": container.short_id,
                }

                # Check if container failed
                if status == "exited" or status == "dead":
                    progress.update(
                        container_tasks[name],
                        description=f"  [{EMOJI['cross']}] {name} [red](failed)[/red]",
                        completed=100,
                    )
                    raise DockerClientError(f"Container {name} failed to start (status: {status})")

                # Check if container is ready
                if status == "running":
                    if health == "none" or health == "healthy":
                        ready_count += 1
                        progress.update(
                            container_tasks[name],
                            description=f"  [{EMOJI['check']}] {name} [green]({health if health != 'none' else 'running'})[/green]",
                            completed=100,
                        )
                    elif health == "starting":
                        progress.update(
                            container_tasks[name],
                            description=f"  [↻] {name} [yellow](starting...)[/yellow]",
                            completed=50,
                        )
                    elif health == "unhealthy":
                        progress.update(
                            container_tasks[name],
                            description=f"  [{EMOJI['warning']}] {name} [yellow](unhealthy)[/yellow]",
                            completed=75,
                        )
                elif status == "created" or status == "restarting":
                    progress.update(
                        container_tasks[name],
                        description=f"  [ ] {name} [dim](waiting...)[/dim]",
                        completed=10,
                    )

            # Update overall progress
            progress.update(overall_task, completed=ready_count)

            # Check if all containers are ready
            if ready_count == len(containers):
                return {
                    "success": True,
                    "elapsed_time": round(time.time() - start_time, 2),
                    "containers": containers_status,
                }

            time.sleep(check_interval)

    # Timeout reached
    raise DockerClientError(
        f"Timeout waiting for containers (>{timeout}s). " f"Ready: {ready_count}/{len(containers)}"
    )


def deploy_command(
    stack_dir: str = "./stackweaver-stack", project_name: str | None = None, dry_run: bool = False
) -> None:
    """
    Deploy a StackWeaver stack using Docker Compose.

    Args:
        stack_dir: Directory containing docker-compose.yml and .env
        project_name: Optional project name (defaults to directory name)
        dry_run: If True, preview deployment without executing Docker commands
    """
    start_time = time.time()

    # Show banner
    console.print("\n")

    if dry_run:
        console.print(
            Panel(
                f"[bold blue]{EMOJI['search']} StackWeaver Dry-Run Mode[/bold blue]\n"
                "Previewing deployment (no actual changes)...",
                border_style="blue",
            )
        )
    else:
        console.print(
            Panel(
                "[bold cyan]StackWeaver Deploy[/bold cyan]\n"
                "Deploying your stack with Docker Compose...",
                border_style="cyan",
            )
        )

    # Resolve paths
    stack_path = Path(stack_dir).resolve()
    compose_file = stack_path / "docker-compose.yml"
    env_file = stack_path / ".env"

    # Determine project name
    if not project_name:
        project_name = stack_path.name

    # Phase 1: Validation
    show_phase(1, 3, "Validation")

    # Show initial tasks
    show_task_list(
        [
            ("Validate files", "running"),
            ("Check secrets", "pending"),
            ("Check Docker", "pending"),
            ("Analyze stack", "pending"),
        ]
    )

    # Step 1: Validate files exist
    with with_spinner("Validating stack files"):
        if not compose_file.exists():
            compose_error = ComposeFileNotFoundError(str(stack_path))
            compose_error.display()
            return

        if not env_file.exists():
            console.print(
                f"\n[yellow]{EMOJI['warning']}[/yellow] .env file not found in {stack_path}"
            )
            console.print("[dim]Continuing without environment file...[/dim]")
            env_file_to_use = None
        else:
            env_file_to_use = env_file

    show_step_success("Stack files validated")

    # Step 2: Validate secrets
    show_task_list(
        [
            ("Validate files", "done"),
            ("Check secrets", "running"),
            ("Check Docker", "pending"),
            ("Analyze stack", "pending"),
        ]
    )

    with with_spinner("Validating secrets"):
        secrets_valid, secret_warnings = _validate_secrets(env_file)

    if secret_warnings:
        for warning in secret_warnings:
            show_step_warning(warning)

        if not secrets_valid:
            console.print(
                f"\n[red]{EMOJI['error']}[/red] Deployment blocked: weak or missing secrets"
            )
            console.print(
                f"[dim]{EMOJI['info']} Run: [cyan]stackweaver secrets generate[/cyan][/dim]\n"
            )
            return
        else:
            console.print(
                f"[dim]{EMOJI['info']} Tip: Run [cyan]stackweaver secrets generate[/cyan] for stronger secrets[/dim]"
            )
    else:
        show_step_success("Secrets validated")

    show_task_list(
        [
            ("Validate files", "done"),
            ("Check secrets", "done"),
            ("Check Docker", "pending"),
            ("Analyze stack", "pending"),
        ]
    )

    # DRY-RUN MODE: Analyze and preview deployment
    if dry_run:
        # Update task list
        show_task_list(
            [
                ("Validate files", "done"),
                ("Check secrets", "done"),
                ("Check Docker", "done"),
                ("Analyze stack", "running"),
            ]
        )

        with with_spinner("Analyzing docker-compose.yml", "Analysis complete!"):
            analysis = _analyze_compose_file(compose_file)

        if "error" in analysis:
            console.print(
                f"\n[red]{EMOJI['cross']}[/red] Failed to parse docker-compose.yml: {analysis['error']}"
            )
            return

        show_task_list(
            [
                ("Validate files", "done"),
                ("Check secrets", "done"),
                ("Check Docker", "done"),
                ("Analyze stack", "done"),
            ]
        )

        # Display dry-run plan
        console.print("\n")
        console.print(
            Panel(
                f"[bold blue]{EMOJI['search']} Dry-Run Preview - No actual deployment[/bold blue]",
                border_style="blue",
            )
        )

        console.print("\n[bold]Would perform:[/bold]")

        # Images
        if analysis["images"]:
            console.print("\n  [cyan]1. Pull images:[/cyan]")
            for image in analysis["images"]:
                console.print(f"     • {image}")

        # Services/Containers
        if analysis["services"]:
            console.print("\n  [cyan]2. Create containers:[/cyan]")
            for service in analysis["services"]:
                console.print(f"     • {service}")

        # Networks
        if analysis["networks"]:
            console.print("\n  [cyan]3. Create networks:[/cyan]")
            for network in analysis["networks"]:
                console.print(f"     • {network}")
        else:
            console.print("\n  [cyan]3. Create networks:[/cyan]")
            console.print(f"     • {project_name}_default")

        # Volumes
        if analysis["volumes"]:
            console.print("\n  [cyan]4. Create volumes:[/cyan]")
            for volume in analysis["volumes"]:
                console.print(f"     • {volume}")

        # Estimated time
        num_services = len(analysis["services"])
        estimated_time = 15 + (num_services * 15)  # Base 15s + 15s per service
        console.print(f"\n[bold]Estimated deployment time:[/bold] ~{estimated_time} seconds")

        # Success message
        total_time = time.time() - start_time
        console.print("\n")
        console.print(
            Panel(
                f"[bold green]{EMOJI['success']} Dry-run completed![/bold green]\n\n"
                f"Analysis time: {total_time:.2f}s\n"
                f"Project: {project_name}\n\n"
                f"[bold]To deploy for real:[/bold]\n"
                f"  [cyan]stackweaver deploy[/cyan]",
                title="Dry-Run Complete",
                border_style="green",
            )
        )
        console.print("\n")
        return

    # Step 2: Check Docker is running
    show_step("Checking Docker daemon")

    client = DockerClient()
    if not client.is_running():
        docker_error = DockerNotRunningError()
        docker_error.display()
        return

    try:
        docker_info = client.get_docker_info()
        console.print(
            f"[green]{EMOJI['check']}[/green] Docker {docker_info['server_version']} is running"
        )
    except DockerClientError as e:
        info_error = StackWeaverError(
            message="Failed to get Docker information",
            cause="Docker daemon may be starting or experiencing issues",
            fix="Wait a moment and try again, or restart Docker Desktop",
            details=str(e),
        )
        info_error.display()
        return

    # Step 3: Check if stack is already deployed (Idempotency)
    show_step("Checking for existing deployment")

    force_recreate = False

    if client.is_stack_deployed(project_name):
        console.print(f"[yellow]{EMOJI['warning']}[/yellow] Stack is already deployed")

        # Display interactive prompt
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("  [1] Skip     - Exit without changes")
        console.print("  [2] Update   - Update changed services only (default)")
        console.print("  [3] Recreate - Force recreate all containers")

        choice = Prompt.ask(
            "\nSelect an option",
            choices=["1", "2", "3"],
            default="2",
            show_choices=False,
            show_default=True,
        )

        if choice == "1":
            # Skip deployment
            console.print(
                f"\n[blue]{EMOJI['arrow']}[/blue] Skipping deployment - stack already running"
            )
            console.print(
                Panel(
                    "[bold cyan]Stack already running[/bold cyan]\n\n"
                    f"Project: {project_name}\n\n"
                    f"[bold]Manage your stack:[/bold]\n"
                    f"  • View status: [cyan]docker compose -p {project_name} ps[/cyan]\n"
                    f"  • View logs:   [cyan]docker compose -p {project_name} logs -f[/cyan]\n"
                    f"  • Stop stack:  [cyan]docker compose -p {project_name} down[/cyan]",
                    title="Info",
                    border_style="blue",
                )
            )
            console.print("\n")
            client.close()
            return
        elif choice == "2":
            # Update (default behavior, just run compose up)
            console.print(f"[green]{EMOJI['check']}[/green] Will update changed services only")
        elif choice == "3":
            # Force recreate
            console.print(f"[green]{EMOJI['check']}[/green] Will force recreate all containers")
            force_recreate = True
    else:
        show_step_success("No existing deployment found")

    # Step 4: Deploy with docker compose up -d
    show_step(f"Deploying project '{project_name}'")

    try:
        result = client.compose_up(
            compose_file=compose_file,
            env_file=env_file_to_use,
            project_name=project_name,
            force_recreate=force_recreate,
        )

        if result["success"]:
            show_step_success("Docker Compose up completed")
        else:
            show_step_error("Docker Compose up failed")
            if result.get("stderr"):
                console.print(f"[dim]{result['stderr']}[/dim]")
            return

    except DockerClientError as e:
        console.print(f"\n[red]{EMOJI['cross']}[/red] Deployment failed: {e}")
        console.print("[dim]Check the error above and your docker-compose.yml configuration.[/dim]")
        return

    # Step 5: Wait for containers to be healthy with progress display
    show_step("Waiting for containers to be ready")

    try:
        health_result = _wait_for_healthy_with_progress(
            client, project_name=project_name, timeout=120
        )

        if health_result["success"]:
            elapsed = health_result["elapsed_time"]
            console.print(f"[green]{EMOJI['check']}[/green] All containers ready in {elapsed}s")
        else:
            console.print("[yellow]⚠[/yellow] Some containers may not be fully ready")

    except DockerClientError as e:
        console.print(f"\n[yellow]⚠[/yellow] Health check warning: {e}")
        console.print("[dim]Containers are starting but may not be fully ready yet.[/dim]")
        health_result = {"containers": {}}

    # Step 6: Display access URLs
    show_step("Generating access URLs")

    try:
        containers = client.get_containers(project_name)

        if not containers:
            console.print("[yellow]⚠[/yellow] No containers found")
        else:
            # Build URL table
            table = Table(
                title="[bold green]✓ Services Deployed Successfully![/bold green]",
                show_header=True,
                header_style="bold cyan",
                border_style="green",
            )

            table.add_column("Service", style="cyan", no_wrap=True)
            table.add_column("Status", style="green")
            table.add_column("Access URL", style="yellow")

            for container in containers:
                container.reload()

                # Extract service name from container name
                # Format: project_name-service_name-1
                parts = container.name.split("-")
                if len(parts) >= 2:
                    service_name = "-".join(parts[1:-1]) if len(parts) > 2 else parts[1]
                else:
                    service_name = container.name

                # Get status
                status = container.status
                health = container.attrs.get("State", {}).get("Health", {}).get("Status", "none")

                if status == "running":
                    if health == "healthy":
                        status_display = "✓ Healthy"
                    elif health == "none":
                        status_display = f"{EMOJI['check']} Running"
                    else:
                        status_display = f"* {health.capitalize()}"
                else:
                    status_display = f"{EMOJI['cross']} {status.capitalize()}"

                # Generate URL (subdomain routing via Traefik)
                # Check if service has Traefik labels
                labels = container.labels
                if "traefik.enable" in labels and labels["traefik.enable"] == "true":
                    # Extract subdomain from Traefik rule
                    rule = labels.get(f"traefik.http.routers.{service_name}.rule", "")
                    if "Host" in rule:
                        # Parse Host(`service.localhost`) format
                        import re

                        match = re.search(r"Host\(`([^`]+)`\)", rule)
                        if match:
                            url = f"http://{match.group(1)}"
                        else:
                            url = f"http://{service_name}.localhost"
                    else:
                        url = f"http://{service_name}.localhost"
                else:
                    # No Traefik, show port mapping if available
                    ports = container.ports
                    if ports:
                        # Get first port mapping
                        for _, port_mapping in ports.items():
                            if port_mapping:
                                host_port = port_mapping[0]["HostPort"]
                                url = f"http://localhost:{host_port}"
                                break
                        else:
                            url = "(no public port)"
                    else:
                        url = "(internal only)"

                table.add_row(service_name, status_display, url)

            console.print("\n")
            console.print(table)

    except DockerClientError as e:
        console.print(f"\n[yellow]⚠[/yellow] Could not retrieve container info: {e}")

    # Calculate total time
    total_time = time.time() - start_time

    # Success summary
    console.print("\n")
    console.print(
        Panel(
            f"[bold green]✓ Deployment complete![/bold green]\n\n"
            f"Total time: {total_time:.2f}s\n"
            f"Project: {project_name}\n\n"
            f"[bold]Manage your stack:[/bold]\n"
            f"  • View logs:  [cyan]docker compose -p {project_name} logs -f[/cyan]\n"
            f"  • Stop stack: [cyan]docker compose -p {project_name} down[/cyan]\n"
            f"  • Restart:    [cyan]stackweaver deploy[/cyan]",
            title="Success",
            border_style="green",
        )
    )
    console.print("\n")

    # Close client
    client.close()
