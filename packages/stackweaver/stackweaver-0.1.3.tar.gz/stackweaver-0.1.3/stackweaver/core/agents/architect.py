"""
Architect Agent Interface for StackWeaver.

The Architect is responsible for designing Docker stack configurations
from selected tools. This interface enables Phase 2 migration to LangGraph
agents while maintaining backward compatibility.

Phase 1: SimpleArchitect wraps YAMLGenerator
Phase 2: LangGraphArchitect will use agentic reasoning for stack design
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from stackweaver.generator.yaml_generator import YAMLGenerator
from stackweaver.search.schemas import ToolSchema

logger = logging.getLogger(__name__)


class StackConfig:
    """Configuration for a designed Docker stack."""

    def __init__(
        self,
        compose_yaml: str,
        env_content: str,
        services: list[str],
        networks: list[str],
        volumes: list[str],
    ):
        """
        Initialize stack configuration.

        Args:
            compose_yaml: Generated docker-compose.yml content
            env_content: Generated .env file content
            services: List of service names in the stack
            networks: List of network names
            volumes: List of volume names
        """
        self.compose_yaml = compose_yaml
        self.env_content = env_content
        self.services = services
        self.networks = networks
        self.volumes = volumes


class ArchitectAgent(ABC):
    """
    Abstract interface for stack architecture and design.

    The Architect agent is responsible for:
    - Designing Docker Compose configurations from tools
    - Ensuring proper service isolation and networking
    - Generating secure configurations with secrets
    - Validating stack architecture

    Implementations:
    - SimpleArchitect: Direct YAML generation (Phase 1)
    - LangGraphArchitect: Agentic design with reasoning (Phase 2)
    """

    @abstractmethod
    def design_stack(
        self,
        tools: list[ToolSchema],
        **kwargs: Any,
    ) -> StackConfig:
        """
        Design a Docker stack configuration from selected tools.

        Args:
            tools: List of tools to include in the stack
            **kwargs: Additional design parameters

        Returns:
            StackConfig with generated configuration files

        Raises:
            Exception: If design/generation fails
        """
        pass

    @abstractmethod
    def explain_design(
        self,
        stack_config: StackConfig,
    ) -> str:
        """
        Explain the design decisions made for the stack.

        Args:
            stack_config: The generated stack configuration

        Returns:
            Human-readable explanation of design choices

        Note:
            Phase 1: Template-based explanation
            Phase 2: LLM-generated contextual explanation with reasoning
        """
        pass

    @abstractmethod
    def validate_design(
        self,
        stack_config: StackConfig,
    ) -> tuple[bool, list[str]]:
        """
        Validate the stack design.

        Args:
            stack_config: The stack configuration to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass


class SimpleArchitect(ArchitectAgent):
    """
    Phase 1 implementation of ArchitectAgent.

    Wraps existing YAMLGenerator functionality in the ArchitectAgent
    interface. This provides a clean abstraction layer for Phase 2
    migration to LangGraph.

    Example:
        >>> architect = SimpleArchitect(yaml_generator)
        >>> stack = architect.design_stack([tool1, tool2])
        >>> print(architect.explain_design(stack))
    """

    def __init__(self, yaml_generator: YAMLGenerator):
        """
        Initialize SimpleArchitect with YAML generator.

        Args:
            yaml_generator: YAMLGenerator instance for stack generation
        """
        self.yaml_generator = yaml_generator
        logger.info("SimpleArchitect initialized")

    def design_stack(
        self,
        tools: list[ToolSchema],
        **kwargs: Any,
    ) -> StackConfig:
        """
        Design stack using YAMLGenerator.

        Args:
            tools: List of tools to include in the stack
            **kwargs: Additional parameters (currently unused)

        Returns:
            StackConfig with generated files and metadata
        """
        logger.info(f"Architect designing stack with {len(tools)} tools")

        # Generate compose and env files
        compose_yaml = self.yaml_generator.generate(tools)
        env_content = self.yaml_generator.generate_env(tools)

        # Extract metadata from generated YAML
        services = [tool.name.lower().replace(" ", "-") for tool in tools]
        networks = ["stackweaver-network", "traefik-public"]
        volumes = [f"{service}-data" for service in services]

        logger.info(
            f"Stack designed: {len(services)} services, "
            f"{len(networks)} networks, {len(volumes)} volumes"
        )

        return StackConfig(
            compose_yaml=compose_yaml,
            env_content=env_content,
            services=services,
            networks=networks,
            volumes=volumes,
        )

    def explain_design(
        self,
        stack_config: StackConfig,
    ) -> str:
        """
        Provide template-based explanation of design.

        Args:
            stack_config: The generated stack configuration

        Returns:
            Explanation of design decisions

        Note:
            Phase 2 will use LLM for contextual explanations
        """
        explanation = (
            f"Stack Design Summary:\n"
            f"- Services: {len(stack_config.services)} ({', '.join(stack_config.services)})\n"
            f"- Networks: {len(stack_config.networks)} (isolated + Traefik public)\n"
            f"- Volumes: {len(stack_config.volumes)} (persistent data storage)\n"
            f"\n"
            f"Design Decisions:\n"
            f"- Each service has isolated database (if required)\n"
            f"- Traefik reverse proxy for subdomain routing\n"
            f"- Secrets generated using CSPRNG\n"
            f"- All services on shared network for inter-service communication\n"
            f"- Persistent volumes for data durability"
        )

        return explanation

    def validate_design(
        self,
        stack_config: StackConfig,
    ) -> tuple[bool, list[str]]:
        """
        Validate stack design.

        Args:
            stack_config: The stack configuration to validate

        Returns:
            Tuple of (is_valid, error_messages)

        Note:
            Phase 1: Basic validation
            Phase 2: Advanced validation with LLM reasoning
        """
        errors = []

        # Check for services
        if not stack_config.services:
            errors.append("Stack must have at least one service")

        # Check for compose content
        if not stack_config.compose_yaml:
            errors.append("Compose YAML is empty")

        if not stack_config.compose_yaml.startswith("version:"):
            errors.append("Compose YAML must start with version declaration")

        # Check for env content
        if not stack_config.env_content:
            errors.append("Environment file is empty")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("Stack design validation passed")
        else:
            logger.warning(f"Stack design validation failed: {errors}")

        return is_valid, errors


# Phase 2 placeholder
class LangGraphArchitect(ArchitectAgent):
    """
    Phase 2 implementation using LangGraph agents.

    This will use agentic reasoning for:
    - Intelligent service placement and sizing
    - Automatic dependency resolution
    - Security best practices enforcement
    - Performance optimization suggestions
    - Interactive design refinement

    Example (Phase 2):
        >>> architect = LangGraphArchitect(graph, tools)
        >>> stack = architect.design_stack([tool1, tool2])
        >>> # Agent will reason about optimal architecture,
        >>> # suggest improvements, and explain trade-offs
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """Phase 2 implementation - not yet available."""
        raise NotImplementedError(
            "LangGraphArchitect is planned for Phase 2. "
            "Use SimpleArchitect for current functionality."
        )

    def design_stack(
        self,
        tools: list[ToolSchema],
        **kwargs: Any,
    ) -> StackConfig:
        """Phase 2 implementation."""
        raise NotImplementedError("Phase 2 not yet implemented")

    def explain_design(
        self,
        stack_config: StackConfig,
    ) -> str:
        """Phase 2 implementation."""
        raise NotImplementedError("Phase 2 not yet implemented")

    def validate_design(
        self,
        stack_config: StackConfig,
    ) -> tuple[bool, list[str]]:
        """Phase 2 implementation."""
        raise NotImplementedError("Phase 2 not yet implemented")
