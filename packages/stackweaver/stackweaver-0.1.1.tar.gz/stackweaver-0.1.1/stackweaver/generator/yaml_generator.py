"""
YAML Generator for StackWeaver.

Orchestrates the complete pipeline for generating valid docker-compose.yml files.
"""

from datetime import UTC
from pathlib import Path
from typing import Any

from stackweaver.generator.isolation import IsolationStrategy
from stackweaver.generator.secrets import SecretGenerator
from stackweaver.generator.validators import TemplateValidator
from stackweaver.generator.volumes import VolumeManager
from stackweaver.search.schemas import ToolSchema


class YAMLGenerationError(Exception):
    """Raised when YAML generation fails."""

    pass


class YAMLGenerator:
    """
    Orchestrates YAML generation with full validation pipeline.

    Implements ADR-004 three-stage validation to guarantee 100% valid output.
    """

    def __init__(
        self,
        template_dir: Path | str | None = None,
        skip_compose_validation: bool = False,
    ) -> None:
        """
        Initialize YAML generator.

        Args:
            template_dir: Directory containing Jinja2 templates
                         (defaults to stackweaver/generator/templates)
            skip_compose_validation: Skip Stage 3 Docker Compose validation
                                    (useful when Docker is not available)
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = Path(template_dir)
        self.skip_compose_validation = skip_compose_validation

        # Initialize components
        self.validator = TemplateValidator(self.template_dir)
        self.volume_manager = VolumeManager()
        self.secret_generator = SecretGenerator()
        self.isolation_strategy = IsolationStrategy()

    def generate(
        self,
        tools: list[ToolSchema],
        project_name: str = "stackweaver",
        traefik_enabled: bool = True,
        traefik_domain: str = "localhost",
        https_enabled: bool = False,
        letsencrypt_email: str = "",
    ) -> str:
        """
        Generate a validated docker-compose.yml file.

        This method runs the complete validation pipeline (ADR-004):
        - Stage 1: Pre-render validation (variable presence)
        - Stage 2: YAML syntax validation
        - Stage 3: Docker Compose schema validation (optional)

        Args:
            tools: List of tools to include in the stack
            project_name: Name of the Docker Compose project
            traefik_enabled: Enable Traefik reverse proxy
            traefik_domain: Domain for Traefik routing
            https_enabled: Enable HTTPS with Let's Encrypt
            letsencrypt_email: Email for Let's Encrypt notifications

        Returns:
            Valid docker-compose.yml content as string

        Raises:
            YAMLGenerationError: If generation or validation fails
        """
        try:
            # Build context for template rendering
            context = self._build_context(
                tools=tools,
                project_name=project_name,
                traefik_enabled=traefik_enabled,
                traefik_domain=traefik_domain,
                https_enabled=https_enabled,
                letsencrypt_email=letsencrypt_email,
            )

            # Validate and render template with full pipeline
            validation_result = self.validator.validate_all(
                "docker-compose.j2",
                context,
                skip_compose_validation=self.skip_compose_validation,
            )

            if not validation_result.is_valid:
                error_msg = "\n".join(validation_result.errors)
                raise YAMLGenerationError(f"YAML generation failed validation:\n{error_msg}")

            # Render the template
            from jinja2 import Environment, FileSystemLoader

            env = Environment(loader=FileSystemLoader(str(self.template_dir)), autoescape=False)
            template = env.get_template("docker-compose.j2")
            rendered_yaml: str = template.render(context)

            return rendered_yaml

        except Exception as e:
            if isinstance(e, YAMLGenerationError):
                raise
            raise YAMLGenerationError(f"Failed to generate YAML: {e}") from e

    def generate_env(
        self,
        tools: list[ToolSchema],
        output_path: Path | str | None = None,
    ) -> str:
        """
        Generate .env file with secrets for the stack.

        Args:
            tools: List of tools to generate secrets for
            output_path: Optional path to write .env file

        Returns:
            .env file content as string
        """
        # Clear any existing secrets
        self.secret_generator.clear()

        # Generate secrets for each tool
        for tool in tools:
            if tool.env_vars:
                for env_var in tool.env_vars:
                    # Only generate secrets for password/key type variables
                    if any(
                        keyword in env_var.key.lower()
                        for keyword in ["password", "secret", "key", "token"]
                    ):
                        self.secret_generator.add_secret(
                            env_var.key,
                            description=env_var.description or f"Secret for {tool.name}",
                        )

        # Write to file if path provided
        if output_path:
            self.secret_generator.generate_env_file(output_path)

        # Return content as string
        lines = [self.secret_generator.ENV_FILE_HEADER]

        for secret in self.secret_generator.get_all_secrets().values():
            if secret.description:
                lines.append(f"# {secret.description}")
            lines.append(f"{secret.key}={secret.value}")

        return "\n".join(lines) + "\n"

    def _build_context(
        self,
        tools: list[ToolSchema],
        project_name: str,
        traefik_enabled: bool,
        traefik_domain: str,
        https_enabled: bool,
        letsencrypt_email: str,
    ) -> dict[str, Any]:
        """
        Build template rendering context.

        Args:
            tools: List of tools to include
            project_name: Project name
            traefik_enabled: Enable Traefik
            traefik_domain: Traefik domain
            https_enabled: Enable HTTPS
            letsencrypt_email: Let's Encrypt email

        Returns:
            Context dictionary for template rendering
        """
        from datetime import datetime

        # Convert tools to services
        services = []
        volumes = []

        for tool in tools:
            # Create service definition
            service: dict[str, Any] = {
                "name": tool.name.lower().replace(" ", "-"),
                "docker_image": tool.docker_image,
                "ports": tool.ports or [],
                "env_vars": tool.env_vars or [],
                "volumes": [],
                "traefik_enabled": traefik_enabled,
                "healthcheck": None,
                "dependencies": [],
            }

            # Add volumes for the service
            if tool.volumes:
                for volume in tool.volumes:
                    # Register volume with manager
                    vol_mount = self.volume_manager.create_service_volume(
                        str(service["name"]), volume.mount_path
                    )
                    volumes_list = service.get("volumes", [])
                    volumes_list.append(
                        {
                            "name": vol_mount.volume_name,
                            "mount_path": vol_mount.mount_path,
                        }
                    )
                    service["volumes"] = volumes_list

            services.append(service)

        # Get registered volumes
        for volume_name, volume_def in self.volume_manager.get_all_volumes().items():
            volumes.append(
                {
                    "name": volume_name,
                    "driver": volume_def.driver,
                    "driver_opts": volume_def.driver_opts,
                }
            )

        # Build context
        context = {
            "project_name": project_name,
            "generation_date": datetime.now(UTC).isoformat(),
            "services": services,
            "volumes": volumes,
            "traefik_enabled": traefik_enabled,
            "traefik_domain": traefik_domain,
            "https_enabled": https_enabled,
            "letsencrypt_email": letsencrypt_email,
            "custom_domain": traefik_domain != "localhost",
        }

        return context
