"""
Error handling and recovery for StackWeaver.

Provides structured error messages with:
- Problem description
- Likely cause
- Actionable fix
"""

from rich.console import Console
from rich.panel import Panel

console = Console()


class StackWeaverError(Exception):
    """Base exception for all StackWeaver errors."""

    def __init__(
        self,
        message: str,
        cause: str | None = None,
        fix: str | None = None,
        details: str | None = None,
    ) -> None:
        """
        Initialize a StackWeaver error.

        Args:
            message: Main error message (the problem)
            cause: Likely cause of the error
            fix: Suggested fix or action
            details: Additional technical details
        """
        self.message = message
        self.cause = cause
        self.fix = fix
        self.details = details
        super().__init__(message)

    def display(self) -> None:
        """Display the error with Rich formatting."""
        error_text = f"[bold red]❌ {self.message}[/bold red]"

        if self.cause:
            error_text += f"\n\n[yellow]Cause:[/yellow] {self.cause}"

        if self.fix:
            error_text += f"\n\n[green]Fix:[/green] {self.fix}"

        if self.details:
            error_text += f"\n\n[dim]Details:[/dim] {self.details}"

        console.print("\n")
        console.print(Panel(error_text, title="Error", border_style="red"))
        console.print("\n")


class DockerNotRunningError(StackWeaverError):
    """Docker daemon is not running."""

    def __init__(self) -> None:
        super().__init__(
            message="Docker is not running",
            cause="Docker Desktop is not started or Docker daemon is not accessible",
            fix="Start Docker Desktop and wait for it to fully initialize, then try again",
        )


class DockerConnectionError(StackWeaverError):
    """Cannot connect to Docker daemon."""

    def __init__(self, details: str | None = None) -> None:
        super().__init__(
            message="Cannot connect to Docker daemon",
            cause="Docker may not be running or you may lack permissions",
            fix="Check Docker status with 'docker ps' or restart Docker Desktop",
            details=details,
        )


class ImagePullError(StackWeaverError):
    """Failed to pull Docker image."""

    def __init__(self, image: str, details: str | None = None) -> None:
        super().__init__(
            message=f"Failed to pull image '{image}'",
            cause="Image may not exist, network issue, or authentication required",
            fix=f"Check image name spelling, verify internet connection, or try 'docker pull {image}' manually",
            details=details,
        )


class ContainerHealthCheckError(StackWeaverError):
    """Container failed health check."""

    def __init__(self, service: str, details: str | None = None) -> None:
        super().__init__(
            message=f"Service '{service}' is unhealthy",
            cause="Container is running but health check is failing",
            fix=f"Check logs with 'docker logs {service}' or review health check configuration",
            details=details,
        )


class ContainerStartError(StackWeaverError):
    """Container failed to start."""

    def __init__(self, service: str, details: str | None = None) -> None:
        super().__init__(
            message=f"Service '{service}' failed to start",
            cause="Container exited immediately after starting",
            fix=f"Check logs with 'docker logs {service}' for error messages",
            details=details,
        )


class PortInUseError(StackWeaverError):
    """Port is already in use."""

    def __init__(self, port: int, details: str | None = None) -> None:
        super().__init__(
            message=f"Port {port} is already in use",
            cause="Another service is using this port",
            fix="Stop conflicting services or change port mapping in docker-compose.yml",
            details=details,
        )


class DiskSpaceError(StackWeaverError):
    """Insufficient disk space."""

    def __init__(self, required_gb: int = 5, details: str | None = None) -> None:
        super().__init__(
            message="Insufficient disk space",
            cause=f"Docker needs at least {required_gb}GB free disk space",
            fix="Free up disk space by removing unused Docker images/volumes: 'docker system prune -a'",
            details=details,
        )


class ComposeFileNotFoundError(StackWeaverError):
    """docker-compose.yml not found."""

    def __init__(self, path: str) -> None:
        super().__init__(
            message=f"docker-compose.yml not found at {path}",
            cause="Stack has not been initialized or wrong directory",
            fix="Run 'stackweaver init' first to create your stack, or check you're in the right directory",
        )


class ComposeFileInvalidError(StackWeaverError):
    """docker-compose.yml is invalid."""

    def __init__(self, details: str | None = None) -> None:
        super().__init__(
            message="docker-compose.yml is invalid",
            cause="YAML syntax error or invalid Docker Compose schema",
            fix="Check YAML syntax with an online validator or review Docker Compose documentation",
            details=details,
        )


class StackNotFoundError(StackWeaverError):
    """Stack deployment not found."""

    def __init__(self, project_name: str) -> None:
        super().__init__(
            message=f"No deployment found for project '{project_name}'",
            cause="Stack has not been deployed or different project name was used",
            fix="Deploy the stack first with 'stackweaver deploy' or check project name",
        )


class NetworkError(StackWeaverError):
    """Network-related error."""

    def __init__(self, details: str | None = None) -> None:
        super().__init__(
            message="Network error during deployment",
            cause="Internet connection issue or Docker network problem",
            fix="Check internet connection and Docker network settings",
            details=details,
        )


class ValidationError(StackWeaverError):
    """Validation failed."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(
            message=f"Validation failed: {message}",
            cause="Configuration does not meet requirements",
            fix="Review error details and fix configuration",
            details=details,
        )


class TimeoutError(StackWeaverError):
    """Operation timed out."""

    def __init__(self, operation: str, timeout: int, details: str | None = None) -> None:
        super().__init__(
            message=f"{operation} timed out after {timeout}s",
            cause="Operation took longer than expected",
            fix="Check system resources, network, or increase timeout",
            details=details,
        )
