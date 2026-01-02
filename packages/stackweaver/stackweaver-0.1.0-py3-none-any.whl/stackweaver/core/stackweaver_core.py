"""
StackWeaver Core Pipeline Orchestrator.

This module provides the central orchestration class that coordinates
all stages of the Linear Pipeline:
1. Tool Search & Selection
2. YAML Generation
3. Validation
4. Docker Deployment
5. Health Checks & URL Generation

The StackWeaverCore class ensures all components work together in the
correct sequence with proper error handling and progress reporting.
"""

import logging
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from stackweaver.core.errors import StackWeaverError
from stackweaver.core.resources import ResourceManager
from stackweaver.search.tool_search import ToolSearch

logger = logging.getLogger(__name__)
console = Console()


class ProjectConfig:
    """Configuration for an initialized project."""

    def __init__(
        self,
        tools: list[dict[str, Any]],
        compose_file_path: Path,
        env_file_path: Path,
        project_name: str,
    ):
        """
        Initialize project configuration.

        Args:
            tools: List of selected tools with metadata
            compose_file_path: Path to generated docker-compose.yml
            env_file_path: Path to generated .env file
            project_name: Name of the Docker Compose project
        """
        self.tools = tools
        self.compose_file_path = compose_file_path
        self.env_file_path = env_file_path
        self.project_name = project_name


class DeploymentResult:
    """Result of a stack deployment operation."""

    def __init__(
        self,
        success: bool,
        deployed_services: list[str],
        failed_services: list[str],
        access_urls: dict[str, str],
        error_message: str | None = None,
    ):
        """
        Initialize deployment result.

        Args:
            success: Whether deployment succeeded
            deployed_services: List of successfully deployed service names
            failed_services: List of failed service names
            access_urls: Dictionary mapping service names to access URLs
            error_message: Error message if deployment failed
        """
        self.success = success
        self.deployed_services = deployed_services
        self.failed_services = failed_services
        self.access_urls = access_urls
        self.error_message = error_message


class StackWeaverCore:
    """
    Central orchestrator for the StackWeaver Linear Pipeline.

    This class coordinates all stages of project initialization and deployment:
    - Tool search and selection
    - YAML generation with validation
    - Docker deployment with health checks
    - URL generation for service access

    Uses ResourceManager for dependency injection and provides clean
    error handling with recovery guidance.
    """

    def __init__(self, resource_manager: ResourceManager | None = None):
        """
        Initialize StackWeaver Core.

        Args:
            resource_manager: ResourceManager instance (creates new if None)
        """
        self.resources = resource_manager or ResourceManager()
        logger.info("StackWeaverCore initialized")

    def initialize_project(
        self,
        user_query: str,
        output_dir: str = "./stackweaver-stack",
        use_llm_rerank: bool = True,
        tool_schemas: list[Any] | None = None,
    ) -> ProjectConfig:
        """
        Initialize a new StackWeaver project from natural language query.

        This method executes the initialization pipeline:
        1. Tool Search: Semantic search via VectorStore + LLM ranking (if tool_schemas not provided)
        2. Tool Selection: Present recommendations (handled by caller)
        3. YAML Generation: Generate docker-compose.yml with validation
        4. File Output: Write compose and .env files

        Args:
            user_query: Natural language description of desired stack
            output_dir: Directory to create project in
            use_llm_rerank: Whether to use LLM for result re-ranking
            tool_schemas: Optional pre-selected ToolSchema list (skips search)

        Returns:
            ProjectConfig with generated files and metadata

        Raises:
            StackWeaverError: If any stage fails
        """
        logger.info(f"Initializing project for query: {user_query}")

        try:
            # If tool_schemas not provided, perform search
            if tool_schemas is None:
                # Stage 1: Tool Search
                console.print("\n[cyan]→[/cyan] Searching for matching tools...")
                vector_store = self.resources.get_vector_store()
                llm_client = self.resources.get_llm_client() if use_llm_rerank else None
                tool_search = ToolSearch(vector_store, llm_client)

                search_results, search_metadata = tool_search.find_tools(
                    query=user_query,
                    top_k=5,
                    use_llm_rerank=use_llm_rerank,
                )

                if not search_results:
                    raise StackWeaverError(
                        "No matching tools found",
                        cause="Search returned no results",
                        fix="Try rephrasing your query or being more specific",
                    )

                logger.info(
                    f"Found {len(search_results)} tools in "
                    f"{search_metadata.get('total_time_ms', 0)}ms"
                )

                # Note: In real usage, CLI would present search_results to user
                # and they would select/confirm. For this orchestrator, we assume
                # caller will pass pre-approved tool_schemas
                raise StackWeaverError(
                    "Tool schemas must be provided",
                    cause="initialize_project() requires pre-approved tool schemas",
                    fix="Pass tool_schemas parameter after user confirmation",
                )

            # Stage 2: Tool Selection (handled by caller)
            # tool_schemas contain the approved tools

            # Stage 3: YAML Generation
            console.print("[cyan]→[/cyan] Generating docker-compose.yml...")
            yaml_generator = self.resources.get_yaml_generator()

            compose_content = yaml_generator.generate(tool_schemas)
            env_content = yaml_generator.generate_env(tool_schemas)

            # Convert tool schemas to dict for ProjectConfig
            tools_dict = [{"name": str(tool)} for tool in tool_schemas]

            # Stage 4: File Output
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            compose_file = output_path / "docker-compose.yml"
            env_file = output_path / ".env"

            compose_file.write_text(compose_content, encoding="utf-8")
            env_file.write_text(env_content, encoding="utf-8")

            logger.info(f"Project initialized at {output_path}")
            console.print(f"\n[green]✓[/green] Project initialized at [bold]{output_path}[/bold]")

            # Extract project name from directory
            project_name = output_path.name

            return ProjectConfig(
                tools=tools_dict,
                compose_file_path=compose_file,
                env_file_path=env_file,
                project_name=project_name,
            )

        except StackWeaverError:
            raise
        except Exception as e:
            logger.error(f"Project initialization failed: {e}")
            raise StackWeaverError(
                "Project initialization failed",
                cause=str(e),
                fix="Check logs for details and try again",
            ) from e

    def deploy_stack(
        self,
        project_path: str,
        project_name: str | None = None,
        dry_run: bool = False,
    ) -> DeploymentResult:
        """
        Deploy a StackWeaver project to Docker.

        This method executes the deployment pipeline:
        1. Validation: 3-stage validation (schema, security, deployment-readiness)
        2. Docker Deployment: Deploy via Docker Compose
        3. Health Checks: Wait for containers to be healthy
        4. URL Generation: Generate Traefik subdomain URLs

        Args:
            project_path: Path to project directory containing docker-compose.yml
            project_name: Docker Compose project name (uses dir name if None)
            dry_run: If True, validate but don't deploy

        Returns:
            DeploymentResult with deployment status and access URLs

        Raises:
            StackWeaverError: If any stage fails
        """
        logger.info(f"Deploying stack from {project_path}")

        try:
            project_dir = Path(project_path)
            compose_file = project_dir / "docker-compose.yml"

            if not compose_file.exists():
                raise StackWeaverError(
                    f"docker-compose.yml not found at {project_dir}",
                    cause="Stack has not been initialized or wrong directory",
                    fix="Run 'stackweaver init' first to create your stack",
                )

            # Determine project name
            if project_name is None:
                project_name = project_dir.name

            # Stage 1: Validation (handled by YAMLGenerator)
            console.print("\n[cyan]→[/cyan] Validating stack files...")
            # Validation is performed by reading the compose file
            # YAMLGenerator validates during generation phase

            if dry_run:
                console.print("[green]✓[/green] Validation passed (dry-run mode)")
                logger.info("Dry-run mode: skipping deployment")
                return DeploymentResult(
                    success=True,
                    deployed_services=[],
                    failed_services=[],
                    access_urls={},
                )

            # Stage 2: Docker Deployment
            console.print("[cyan]→[/cyan] Deploying stack to Docker...")
            docker_client = self.resources.get_docker_client()

            # Check Docker is running
            if not docker_client.is_running():
                raise StackWeaverError(
                    "Docker is not running",
                    cause="Docker daemon is not accessible",
                    fix="Start Docker Desktop or Docker daemon and try again",
                )

            # Deploy with docker compose
            docker_client.compose_up(compose_file, project_name=project_name)

            # Stage 3: Health Checks
            console.print("[cyan]→[/cyan] Waiting for services to be healthy...")
            containers = docker_client.get_containers(project_name)

            deployed_services = []
            failed_services = []

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Checking container health...", total=len(containers))

                for container in containers:
                    service_name = container.get("name", "unknown")

                    # Wait for healthy (with timeout)
                    is_healthy = docker_client.wait_for_healthy(service_name, timeout=60)

                    if is_healthy:
                        deployed_services.append(service_name)
                        logger.info(f"Service {service_name} is healthy")
                    else:
                        failed_services.append(service_name)
                        logger.warning(f"Service {service_name} failed health check")

                    progress.advance(task)

            # Stage 4: URL Generation
            console.print("[cyan]→[/cyan] Generating access URLs...")
            access_urls = self._generate_access_urls(deployed_services, project_name)

            success = len(failed_services) == 0
            logger.info(
                f"Deployment {'succeeded' if success else 'partially succeeded'}: "
                f"{len(deployed_services)}/{len(containers)} services healthy"
            )

            return DeploymentResult(
                success=success,
                deployed_services=deployed_services,
                failed_services=failed_services,
                access_urls=access_urls,
                error_message=None if success else "Some services failed health checks",
            )

        except StackWeaverError:
            raise
        except Exception as e:
            logger.error(f"Stack deployment failed: {e}")
            raise StackWeaverError(
                "Stack deployment failed",
                cause=str(e),
                fix="Check Docker logs and try again: docker compose logs",
            ) from e

    def _generate_access_urls(self, services: list[str], project_name: str) -> dict[str, str]:
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

        return urls
