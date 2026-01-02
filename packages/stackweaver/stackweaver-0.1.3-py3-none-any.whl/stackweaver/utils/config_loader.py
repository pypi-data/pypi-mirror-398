"""
Configuration management for StackWeaver.

Loads and validates user configuration from ~/.stackweaver/config.yaml
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class UserConfig(BaseModel):
    """
    StackWeaver user configuration schema.

    Validates settings for LLM providers, Docker, and deployment.
    """

    # LLM Configuration
    llm_provider: str = Field(
        default="openai",
        description="LLM provider: openai, anthropic, ollama",
    )
    llm_model: str = Field(
        default="gpt-4o",
        description="LLM model identifier",
    )
    llm_api_key: str | None = Field(
        default=None,
        description="API key for cloud LLM providers",
    )
    llm_api_base: str | None = Field(
        default=None,
        description="Custom API base URL (e.g., for Ollama)",
    )
    llm_timeout: int = Field(
        default=5,
        description="LLM request timeout in seconds",
        ge=1,
        le=30,
    )

    # Docker Configuration
    docker_socket: str = Field(
        default="unix:///var/run/docker.sock",
        description="Docker socket URL",
    )

    # Deployment Configuration
    traefik_domain: str = Field(
        default="localhost",
        description="Base domain for Traefik reverse proxy",
    )

    # Search Configuration
    search_top_k: int = Field(
        default=3,
        description="Number of tool search results",
        ge=1,
        le=20,
    )
    use_llm_rerank: bool = Field(
        default=True,
        description="Enable LLM re-ranking for search",
    )

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Ensure LLM provider is supported."""
        valid_providers = {"openai", "anthropic", "ollama"}
        if v.lower() not in valid_providers:
            raise ValueError(f"llm_provider must be one of {valid_providers}, got '{v}'")
        return v.lower()

    def requires_api_key(self) -> bool:
        """Check if LLM provider requires API key."""
        # Ollama and local providers don't need API keys
        return self.llm_provider not in {"ollama"}

    def validate_llm_config(self) -> None:
        """
        Validate LLM configuration consistency.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.requires_api_key() and not self.llm_api_key:
            raise ValueError(
                f"llm_api_key required for '{self.llm_provider}' provider. "
                f"Set in ~/.stackweaver/config.yaml or via STACKWEAVER_LLM_API_KEY env var."
            )


def get_default_config_path() -> Path:
    """
    Get default configuration file path.

    Returns:
        Path to ~/.stackweaver/config.yaml
    """
    return Path.home() / ".stackweaver" / "config.yaml"


def create_default_config(config_path: Path) -> None:
    """
    Create default configuration file.

    Args:
        config_path: Path to create config file
    """
    default_config = {
        "# StackWeaver Configuration": None,
        "# LLM Provider Settings": None,
        "llm_provider": "openai",
        "llm_model": "gpt-4o",
        "llm_api_key": None,  # User must set this
        "llm_api_base": None,
        "llm_timeout": 5,
        "# Docker Settings": None,
        "docker_socket": "unix:///var/run/docker.sock",
        "# Deployment Settings": None,
        "traefik_domain": "localhost",
        "# Search Settings": None,
        "search_top_k": 3,
        "use_llm_rerank": True,
    }

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write config
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            default_config,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    logger.info(f"Created default config at {config_path}")


def load_config(config_path: Path | None = None, validate: bool = True) -> UserConfig:
    """
    Load and validate user configuration.

    Args:
        config_path: Path to config file (default: ~/.stackweaver/config.yaml)
        validate: Whether to validate LLM config (default: True)

    Returns:
        Validated UserConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if config_path is None:
        config_path = get_default_config_path()

    # Create default if not exists
    if not config_path.exists():
        logger.warning(f"Config not found at {config_path}, creating default")
        create_default_config(config_path)

    # Load YAML
    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}") from e
    except Exception as e:
        raise FileNotFoundError(f"Failed to read config from {config_path}: {e}") from e

    # Remove comment keys (starting with #)
    config_data: dict[str, Any] = {k: v for k, v in data.items() if not k.startswith("#")}

    # Validate with Pydantic
    try:
        config = UserConfig(**config_data)
    except Exception as e:
        raise ValueError(
            f"Invalid configuration in {config_path}: {e}\n"
            f"See config.yaml.example for reference."
        ) from e

    # Additional validation (optional for default config)
    if validate:
        try:
            config.validate_llm_config()
        except ValueError as e:
            raise ValueError(f"Configuration error: {e}") from e

    logger.info(f"Loaded config: provider={config.llm_provider}, model={config.llm_model}")

    return config


def save_config(config: UserConfig, config_path: Path | None = None) -> None:
    """
    Save configuration to file.

    Args:
        config: UserConfig instance
        config_path: Path to save config (default: ~/.stackweaver/config.yaml)
    """
    if config_path is None:
        config_path = get_default_config_path()

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict
    config_dict = config.model_dump(exclude_none=True)

    # Write YAML
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

    logger.info(f"Saved config to {config_path}")
