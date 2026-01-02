"""
Resource Manager for StackWeaver.

Provides centralized dependency injection with singleton pattern
and lazy initialization for all major components.
"""

from stackweaver.core.errors import StackWeaverError
from stackweaver.deployer.docker_client import DockerClient
from stackweaver.generator.yaml_generator import YAMLGenerator
from stackweaver.search.llm_ranker import LLMRanker, LLMRankerConfig
from stackweaver.search.vector_store import VectorStore
from stackweaver.utils.config_loader import UserConfig, load_config


class ResourceManagerError(StackWeaverError):
    """Error in resource manager."""

    def __init__(self, resource: str, details: str | None = None) -> None:
        super().__init__(
            message=f"Failed to initialize {resource}",
            cause="Resource initialization error",
            fix=f"Check {resource} configuration and dependencies",
            details=details,
        )


class ResourceManager:
    """
    Singleton resource manager for centralized dependency injection.

    Provides lazy initialization of all major components:
    - Configuration
    - Vector Store
    - LLM Client
    - YAML Generator
    - Docker Client

    Example:
        rm = ResourceManager.get_instance()
        config = rm.get_config()
        vector_store = rm.get_vector_store()
    """

    _instance: "ResourceManager | None" = None
    _initialized: bool = False

    def __init__(self) -> None:
        """Private constructor. Use get_instance() instead."""
        if ResourceManager._initialized:
            raise RuntimeError(
                "ResourceManager is a singleton. Use ResourceManager.get_instance() instead."
            )

        # Lazy-loaded resources
        self._config: UserConfig | None = None
        self._vector_store: VectorStore | None = None
        self._llm_client: LLMRanker | None = None
        self._yaml_generator: YAMLGenerator | None = None
        self._docker_client: DockerClient | None = None

        ResourceManager._initialized = True

    @classmethod
    def get_instance(cls) -> "ResourceManager":
        """
        Get the singleton instance of ResourceManager.

        Returns:
            The ResourceManager singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance (useful for testing).

        This clears all cached resources and allows creating a new instance.
        """
        cls._instance = None
        cls._initialized = False

    def get_config(self) -> UserConfig:
        """
        Get the user configuration instance.

        Returns:
            UserConfig instance

        Raises:
            ResourceManagerError: If initialization fails
        """
        if self._config is None:
            try:
                self._config = load_config(validate=False)
            except Exception as e:
                raise ResourceManagerError("UserConfig", details=str(e)) from e
        return self._config

    def get_vector_store(self) -> VectorStore:
        """
        Get the vector store instance.

        Returns:
            VectorStore instance

        Raises:
            ResourceManagerError: If initialization fails
        """
        if self._vector_store is None:
            try:
                self._vector_store = VectorStore()
            except Exception as e:
                raise ResourceManagerError("VectorStore", details=str(e)) from e
        return self._vector_store

    def get_llm_client(self) -> LLMRanker:
        """
        Get the LLM client instance.

        Returns:
            LLMRanker instance

        Raises:
            ResourceManagerError: If initialization fails
        """
        if self._llm_client is None:
            try:
                config = LLMRankerConfig()
                self._llm_client = LLMRanker(config)
            except Exception as e:
                raise ResourceManagerError("LLMRanker", details=str(e)) from e
        return self._llm_client

    def get_yaml_generator(self) -> YAMLGenerator:
        """
        Get the YAML generator instance.

        Returns:
            YAMLGenerator instance

        Raises:
            ResourceManagerError: If initialization fails
        """
        if self._yaml_generator is None:
            try:
                self._yaml_generator = YAMLGenerator()
            except Exception as e:
                raise ResourceManagerError("YAMLGenerator", details=str(e)) from e
        return self._yaml_generator

    def get_docker_client(self) -> DockerClient:
        """
        Get the Docker client instance.

        Returns:
            DockerClient instance

        Raises:
            ResourceManagerError: If initialization fails
        """
        if self._docker_client is None:
            try:
                self._docker_client = DockerClient()
            except Exception as e:
                raise ResourceManagerError("DockerClient", details=str(e)) from e
        return self._docker_client

    def close_all(self) -> None:
        """
        Close all resources that require cleanup.

        This should be called when shutting down the application.
        """
        if self._docker_client is not None:
            try:
                self._docker_client.close()
            except Exception:
                pass  # Ignore errors during cleanup

        # Clear all resources
        self._config = None
        self._vector_store = None
        self._llm_client = None
        self._yaml_generator = None
        self._docker_client = None
