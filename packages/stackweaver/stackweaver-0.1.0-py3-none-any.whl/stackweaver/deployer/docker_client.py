"""
Docker client wrapper for StackWeaver deployment.

Provides a high-level interface to Docker SDK for container management.
"""

import time
from pathlib import Path
from typing import Any

import docker
from docker.errors import DockerException
from docker.models.containers import Container


class DockerClientError(Exception):
    """Custom exception for Docker client errors."""

    pass


class DockerClient:
    """
    Wrapper around Docker SDK for StackWeaver deployments.

    Handles Docker daemon connectivity, container management, and health checks.
    """

    def __init__(self) -> None:
        """Initialize Docker client."""
        self.client: docker.DockerClient | None = None

    def connect(self) -> bool:
        """
        Connect to Docker daemon.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            return True
        except DockerException:
            self.client = None
            return False

    def is_running(self) -> bool:
        """
        Check if Docker daemon is running.

        Returns:
            True if Docker is running and accessible
        """
        if not self.client:
            return self.connect()

        try:
            self.client.ping()
            return True
        except DockerException:
            return False

    def get_docker_info(self) -> dict[str, Any]:
        """
        Get Docker daemon information.

        Returns:
            Dictionary with Docker version and system info

        Raises:
            DockerClientError: If Docker is not running
        """
        if not self.is_running():
            raise DockerClientError("Docker is not running")

        assert self.client is not None
        info = self.client.info()
        version = self.client.version()

        return {
            "server_version": version.get("Version", "unknown"),
            "api_version": version.get("ApiVersion", "unknown"),
            "os": info.get("OperatingSystem", "unknown"),
            "architecture": info.get("Architecture", "unknown"),
            "cpus": info.get("NCPU", 0),
            "memory_gb": round(info.get("MemTotal", 0) / (1024**3), 2),
            "containers": {
                "running": info.get("ContainersRunning", 0),
                "paused": info.get("ContainersPaused", 0),
                "stopped": info.get("ContainersStopped", 0),
            },
        }

    def compose_up(
        self,
        compose_file: Path,
        env_file: Path | None = None,
        project_name: str = "stackweaver",
        force_recreate: bool = False,
    ) -> dict[str, Any]:
        """
        Run docker compose up -d.

        Args:
            compose_file: Path to docker-compose.yml
            env_file: Optional path to .env file
            project_name: Docker Compose project name
            force_recreate: If True, recreate all containers even if config unchanged

        Returns:
            Dictionary with deployment results

        Raises:
            DockerClientError: If Docker is not running or deployment fails
        """
        if not self.is_running():
            raise DockerClientError("Docker is not running")

        if not compose_file.exists():
            raise DockerClientError(f"Compose file not found: {compose_file}")

        if env_file and not env_file.exists():
            raise DockerClientError(f"Env file not found: {env_file}")

        try:
            import subprocess

            # Build docker compose command
            cmd = ["docker", "compose", "-f", str(compose_file), "-p", project_name]

            if env_file:
                cmd.extend(["--env-file", str(env_file)])

            cmd.extend(["up", "-d"])

            if force_recreate:
                cmd.append("--force-recreate")

            # Run docker compose up
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, cwd=compose_file.parent
            )

            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.CalledProcessError as e:
            raise DockerClientError(
                f"Docker Compose failed:\n{e.stderr if e.stderr else e.stdout}"
            ) from e
        except Exception as e:
            raise DockerClientError(f"Unexpected error during deployment: {e}") from e

    def get_containers(self, project_name: str = "stackweaver") -> list[Container]:
        """
        Get all containers for a Docker Compose project.

        Args:
            project_name: Docker Compose project name

        Returns:
            List of Container objects

        Raises:
            DockerClientError: If Docker is not running
        """
        if not self.is_running():
            raise DockerClientError("Docker is not running")

        assert self.client is not None

        try:
            # Filter containers by project label
            containers = self.client.containers.list(
                filters={"label": f"com.docker.compose.project={project_name}"}, all=True
            )
            return containers  # type: ignore[no-any-return]
        except DockerException as e:
            raise DockerClientError(f"Failed to list containers: {e}") from e

    def is_stack_deployed(self, project_name: str = "stackweaver") -> bool:
        """
        Check if a stack is already deployed (has running or existing containers).

        Args:
            project_name: Docker Compose project name

        Returns:
            True if stack has containers, False otherwise

        Raises:
            DockerClientError: If Docker is not running
        """
        try:
            containers = self.get_containers(project_name)
            return len(containers) > 0
        except DockerClientError:
            return False

    def wait_for_healthy(
        self, project_name: str = "stackweaver", timeout: int = 120, check_interval: int = 2
    ) -> dict[str, Any]:
        """
        Wait for all containers to become healthy or running.

        Args:
            project_name: Docker Compose project name
            timeout: Maximum time to wait (seconds)
            check_interval: Time between health checks (seconds)

        Returns:
            Dictionary with container statuses

        Raises:
            DockerClientError: If timeout is reached or containers fail
        """
        if not self.is_running():
            raise DockerClientError("Docker is not running")

        start_time = time.time()
        containers_status: dict[str, dict[str, Any]] = {}

        while time.time() - start_time < timeout:
            containers = self.get_containers(project_name)

            if not containers:
                raise DockerClientError(f"No containers found for project: {project_name}")

            all_ready = True
            containers_status = {}

            for container in containers:
                container.reload()  # Refresh container state

                name = container.name
                status = container.status
                health = container.attrs.get("State", {}).get("Health", {}).get("Status", "none")

                containers_status[name] = {
                    "status": status,
                    "health": health,
                    "id": container.short_id,
                }

                # Check if container is ready
                if status == "exited" or status == "dead":
                    raise DockerClientError(f"Container {name} failed to start (status: {status})")

                # Container is ready if:
                # 1. Status is "running" AND
                # 2. Either no healthcheck configured (health="none") OR health="healthy"
                if status != "running":
                    all_ready = False
                elif health != "none" and health != "healthy":
                    all_ready = False

            if all_ready:
                return {
                    "success": True,
                    "elapsed_time": round(time.time() - start_time, 2),
                    "containers": containers_status,
                }

            time.sleep(check_interval)

        # Timeout reached
        raise DockerClientError(
            f"Timeout waiting for containers (>{timeout}s). " f"Status: {containers_status}"
        )

    def compose_down(
        self, project_name: str = "stackweaver", remove_volumes: bool = False
    ) -> dict[str, Any]:
        """
        Run docker compose down (stop and remove containers).

        Args:
            project_name: Docker Compose project name
            remove_volumes: If True, also remove volumes (data loss!)

        Returns:
            Dictionary with operation results

        Raises:
            DockerClientError: If Docker is not running or operation fails
        """
        if not self.is_running():
            raise DockerClientError("Docker is not running")

        try:
            import subprocess

            # Run docker compose down
            cmd = ["docker", "compose", "-p", project_name, "down"]

            if remove_volumes:
                cmd.append("--volumes")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.CalledProcessError as e:
            raise DockerClientError(
                f"Docker Compose down failed:\n{e.stderr if e.stderr else e.stdout}"
            ) from e
        except Exception as e:
            raise DockerClientError(f"Unexpected error during shutdown: {e}") from e

    def compose_stop(
        self,
        compose_file: Path,
        project_name: str = "stackweaver",
    ) -> dict[str, Any]:
        """
        Stop containers without removing them.

        Args:
            compose_file: Path to docker-compose.yml
            project_name: Docker Compose project name

        Returns:
            Dictionary with operation results
        """
        if not self.is_running():
            raise DockerClientError("Docker is not running")

        try:
            import subprocess

            cmd = [
                "docker",
                "compose",
                "-f",
                str(compose_file),
                "-p",
                project_name,
                "stop",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr if e.stderr else e.stdout,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def compose_start(
        self,
        compose_file: Path,
        project_name: str = "stackweaver",
    ) -> dict[str, Any]:
        """
        Start stopped containers.

        Args:
            compose_file: Path to docker-compose.yml
            project_name: Docker Compose project name

        Returns:
            Dictionary with operation results
        """
        if not self.is_running():
            raise DockerClientError("Docker is not running")

        try:
            import subprocess

            cmd = [
                "docker",
                "compose",
                "-f",
                str(compose_file),
                "-p",
                project_name,
                "start",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr if e.stderr else e.stdout,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_logs(
        self,
        compose_file: Path,
        project_name: str = "stackweaver",
        service: str | None = None,
        follow: bool = False,
        tail: int = 100,
    ) -> str:
        """
        Get container logs.

        Args:
            compose_file: Path to docker-compose.yml
            project_name: Docker Compose project name
            service: Specific service name (all services if None)
            follow: Follow log output
            tail: Number of lines to show

        Returns:
            Log output as string
        """
        if not self.is_running():
            raise DockerClientError("Docker is not running")

        try:
            import subprocess

            cmd = [
                "docker",
                "compose",
                "-f",
                str(compose_file),
                "-p",
                project_name,
                "logs",
                "--tail",
                str(tail),
            ]

            if follow:
                cmd.append("--follow")

            if service:
                cmd.append(service)

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return result.stdout

        except subprocess.CalledProcessError as e:
            raise DockerClientError(
                f"Failed to get logs:\n{e.stderr if e.stderr else e.stdout}"
            ) from e
        except Exception as e:
            raise DockerClientError(f"Unexpected error getting logs: {e}") from e

    def close(self) -> None:
        """Close Docker client connection."""
        if self.client:
            self.client.close()
            self.client = None
