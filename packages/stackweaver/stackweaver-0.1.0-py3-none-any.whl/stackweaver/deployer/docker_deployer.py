"""
Docker Deployment Wrapper for StackWeaver.

This module provides a clean, high-level interface for Docker operations,
wrapping the lower-level DockerClient with deployment-focused methods.

The DockerDeployer handles:
- Stack deployment with progress tracking
- Health monitoring and status reporting
- Rollback operations
- Service URL generation
"""

import logging
from pathlib import Path
from typing import Any

from stackweaver.core.errors import DockerNotRunningError, StackWeaverError
from stackweaver.deployer.docker_client import DockerClient

logger = logging.getLogger(__name__)


class DeploymentResult:
    """Result of a deployment operation."""

    def __init__(
        self,
        success: bool,
        deployed_services: list[str],
        failed_services: list[str],
        access_urls: dict[str, str],
        error_message: str | None = None,
        deployment_time_ms: float | None = None,
    ):
        """
        Initialize deployment result.

        Args:
            success: Whether deployment fully succeeded
            deployed_services: List of successfully deployed service names
            failed_services: List of services that failed to deploy
            access_urls: Dictionary mapping service names to access URLs
            error_message: Error message if deployment failed
            deployment_time_ms: Time taken for deployment in milliseconds
        """
        self.success = success
        self.deployed_services = deployed_services
        self.failed_services = failed_services
        self.access_urls = access_urls
        self.error_message = error_message
        self.deployment_time_ms = deployment_time_ms


class StackStatus:
    """Status of a deployed stack."""

    def __init__(
        self,
        project_name: str,
        status: str,
        services: list[dict[str, Any]],
        networks: list[str],
        volumes: list[str],
    ):
        """
        Initialize stack status.

        Args:
            project_name: Docker Compose project name
            status: Overall status (running/stopped/partial)
            services: List of service status dicts
            networks: List of network names
            volumes: List of volume names
        """
        self.project_name = project_name
        self.status = status
        self.services = services
        self.networks = networks
        self.volumes = volumes


class DockerDeployer:
    """
    High-level Docker deployment wrapper.

    This class provides a clean interface for Docker operations,
    wrapping the lower-level DockerClient with deployment-focused
    methods and proper error handling.

    Example:
        >>> deployer = DockerDeployer()
        >>> result = deployer.deploy(
        ...     compose_file="./stack/docker-compose.yml",
        ...     env_file="./stack/.env",
        ...     project_name="my-stack"
        ... )
        >>> if result.success:
        ...     print(f"Deployed: {result.deployed_services}")
        ...     print(f"URLs: {result.access_urls}")
    """

    def __init__(self, docker_client: DockerClient | None = None):
        """
        Initialize DockerDeployer.

        Args:
            docker_client: Optional DockerClient instance (creates new if None)
        """
        self.client = docker_client or DockerClient()
        logger.info("DockerDeployer initialized")

    def deploy(
        self,
        compose_file: str | Path,
        env_file: str | Path | None = None,
        project_name: str = "stackweaver",
        force_recreate: bool = False,
    ) -> DeploymentResult:
        """
        Deploy a Docker stack.

        Args:
            compose_file: Path to docker-compose.yml
            env_file: Optional path to .env file
            project_name: Docker Compose project name
            force_recreate: If True, recreate all containers

        Returns:
            DeploymentResult with deployment status and URLs

        Raises:
            DockerNotRunningError: If Docker daemon is not running
            StackWeaverError: If deployment fails
        """
        import time

        start_time = time.time()
        logger.info(f"Deploying stack '{project_name}' from {compose_file}")

        # Convert to Path objects
        compose_path = Path(compose_file)
        env_path = Path(env_file) if env_file else None

        # Check Docker is running
        if not self.client.is_running():
            raise DockerNotRunningError()

        try:
            # Deploy with docker compose
            self.client.compose_up(
                compose_file=compose_path,
                env_file=env_path,
                project_name=project_name,
                force_recreate=force_recreate,
            )

            # Get deployed containers
            containers = self.client.get_containers(project_name)

            deployed_services = []
            failed_services = []

            # Check health of each service
            for container in containers:
                service_name = container.get("name", "unknown")

                # Wait for healthy with timeout
                is_healthy = self.client.wait_for_healthy(service_name, timeout=60)

                if is_healthy:
                    deployed_services.append(service_name)
                    logger.info(f"Service {service_name} deployed successfully")
                else:
                    failed_services.append(service_name)
                    logger.warning(f"Service {service_name} failed health check")

            # Generate access URLs
            access_urls = self._generate_urls(deployed_services, project_name)

            deployment_time = (time.time() - start_time) * 1000
            success = len(failed_services) == 0

            logger.info(
                f"Deployment completed in {deployment_time:.0f}ms: "
                f"{len(deployed_services)}/{len(containers)} services healthy"
            )

            return DeploymentResult(
                success=success,
                deployed_services=deployed_services,
                failed_services=failed_services,
                access_urls=access_urls,
                error_message=None if success else "Some services failed health checks",
                deployment_time_ms=deployment_time,
            )

        except DockerNotRunningError:
            raise
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise StackWeaverError(
                "Stack deployment failed",
                cause=str(e),
                fix="Check Docker logs: docker compose logs",
            ) from e

    def rollback(
        self,
        project_name: str,
        remove_volumes: bool = False,
    ) -> None:
        """
        Rollback a deployment by stopping and removing containers.

        Args:
            project_name: Docker Compose project name to rollback
            remove_volumes: If True, also remove volumes (DELETE DATA)

        Raises:
            StackWeaverError: If rollback fails
        """
        logger.info(f"Rolling back stack '{project_name}' (remove_volumes={remove_volumes})")

        try:
            self.client.compose_down(project_name, remove_volumes=remove_volumes)
            if remove_volumes:
                logger.warning(f"Stack '{project_name}' removed with volumes (data deleted)")
            else:
                logger.info(f"Stack '{project_name}' stopped (volumes preserved)")

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise StackWeaverError(
                "Stack rollback failed",
                cause=str(e),
                fix="Try manual cleanup: docker compose down",
            ) from e

    def get_status(
        self,
        project_name: str,
    ) -> StackStatus:
        """
        Get current status of a deployed stack.

        Args:
            project_name: Docker Compose project name

        Returns:
            StackStatus with current state of all components

        Raises:
            StackWeaverError: If status check fails
        """
        logger.info(f"Getting status for stack '{project_name}'")

        try:
            # Check if stack is deployed
            is_deployed = self.client.is_stack_deployed(project_name)

            if not is_deployed:
                return StackStatus(
                    project_name=project_name,
                    status="stopped",
                    services=[],
                    networks=[],
                    volumes=[],
                )

            # Get container status
            containers = self.client.get_containers(project_name)

            services = []
            for container in containers:
                services.append(
                    {
                        "name": container.get("name", "unknown"),
                        "status": container.get("status", "unknown"),
                        "health": container.get("health", "unknown"),
                    }
                )

            # Determine overall status
            if all(s["status"] == "running" for s in services):
                overall_status = "running"
            elif any(s["status"] == "running" for s in services):
                overall_status = "partial"
            else:
                overall_status = "stopped"

            return StackStatus(
                project_name=project_name,
                status=overall_status,
                services=services,
                networks=["stackweaver-network", "traefik-public"],
                volumes=[f"{s['name']}-data" for s in services],
            )

        except Exception as e:
            logger.error(f"Status check failed: {e}")
            raise StackWeaverError(
                "Failed to get stack status",
                cause=str(e),
                fix="Check Docker is running: docker ps",
            ) from e

    def wait_for_health(
        self,
        service: str,
        timeout: int = 60,
    ) -> bool:
        """
        Wait for a service to become healthy.

        Args:
            service: Service name to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            True if service became healthy, False if timeout

        Raises:
            StackWeaverError: If health check fails
        """
        logger.info(f"Waiting for service '{service}' to be healthy (timeout={timeout}s)")

        try:
            result = self.client.wait_for_healthy(service, timeout)
            is_healthy: bool = (
                result.get("healthy", False) if isinstance(result, dict) else bool(result)
            )

            if is_healthy:
                logger.info(f"Service '{service}' is healthy")
            else:
                logger.warning(f"Service '{service}' health check timed out")

            return is_healthy

        except Exception as e:
            logger.error(f"Health check failed for '{service}': {e}")
            raise StackWeaverError(
                f"Health check failed for service '{service}'",
                cause=str(e),
                fix=f"Check service logs: docker logs {service}",
            ) from e

    def _generate_urls(
        self,
        services: list[str],
        project_name: str,
    ) -> dict[str, str]:
        """
        Generate Traefik subdomain URLs for services.

        Args:
            services: List of service names
            project_name: Docker Compose project name

        Returns:
            Dictionary mapping service names to access URLs
        """
        urls = {}
        for service in services:
            # Generate subdomain: service.localhost
            subdomain = service.lower().replace("_", "-")
            urls[service] = f"http://{subdomain}.localhost"

        logger.debug(f"Generated {len(urls)} access URLs")
        return urls
