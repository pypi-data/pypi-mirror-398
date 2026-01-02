"""
Database Isolation Strategy for StackWeaver.

Ensures each tool gets its own dedicated database instance
to prevent version conflicts and maintain separation.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class DatabaseService:
    """Represents a dedicated database service for a tool."""

    name: str  # e.g., "taiga-db"
    tool_name: str  # e.g., "taiga"
    db_type: str  # e.g., "postgres", "mysql", "mongodb"
    version: str  # e.g., "15-alpine"
    volume_name: str  # e.g., "taiga-db-data"
    mount_path: str  # e.g., "/var/lib/postgresql/data"
    env_vars: dict[str, str]  # Database-specific env vars

    @property
    def docker_image(self) -> str:
        """Get the full Docker image name."""
        return f"{self.db_type}:{self.version}"

    @property
    def container_name_suffix(self) -> str:
        """Get the container name suffix."""
        return self.name

    def to_service_dict(self, project_name: str) -> dict[str, Any]:
        """Convert to docker-compose service dictionary."""
        return {
            "name": self.name,
            "docker_image": self.docker_image,
            "ports": [],  # No host port exposure for isolation
            "env_vars": [{"key": k, "required": True} for k in self.env_vars.keys()],
            "volumes": [{"name": self.volume_name, "mount_path": self.mount_path}],
            "dependencies": [],
            "traefik_enabled": False,  # DBs don't need Traefik
            "healthcheck": self._get_healthcheck(),
        }

    def _get_healthcheck(self) -> dict[str, Any] | None:
        """Get database-specific healthcheck configuration."""
        if self.db_type == "postgres":
            return {
                "test": ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
                "start_period": "10s",
            }
        elif self.db_type == "mysql":
            return {
                "test": ["CMD", "mysqladmin", "ping", "-h", "localhost"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
                "start_period": "10s",
            }
        elif self.db_type == "mongodb":
            return {
                "test": ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
                "start_period": "10s",
            }
        elif self.db_type == "redis":
            return {
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
                "start_period": "10s",
            }
        return None


class IsolationStrategy:
    """Manages database isolation for tools in a stack."""

    # Default database versions
    DEFAULT_VERSIONS = {
        "postgres": "15-alpine",
        "mysql": "8.0",
        "mongodb": "7.0",
        "redis": "7.2-alpine",
        "mariadb": "11.1",
    }

    # Database mount paths
    MOUNT_PATHS = {
        "postgres": "/var/lib/postgresql/data",
        "mysql": "/var/lib/mysql",
        "mariadb": "/var/lib/mysql",
        "mongodb": "/data/db",
        "redis": "/data",
    }

    # Required environment variables per database type
    REQUIRED_ENV_VARS = {
        "postgres": {
            "POSTGRES_USER": "admin",
            "POSTGRES_PASSWORD": "",  # Will be generated
            "POSTGRES_DB": "appdb",
        },
        "mysql": {
            "MYSQL_ROOT_PASSWORD": "",  # Will be generated
            "MYSQL_DATABASE": "appdb",
            "MYSQL_USER": "admin",
            "MYSQL_PASSWORD": "",  # Will be generated
        },
        "mariadb": {
            "MYSQL_ROOT_PASSWORD": "",  # Will be generated
            "MYSQL_DATABASE": "appdb",
            "MYSQL_USER": "admin",
            "MYSQL_PASSWORD": "",  # Will be generated
        },
        "mongodb": {
            "MONGO_INITDB_ROOT_USERNAME": "admin",
            "MONGO_INITDB_ROOT_PASSWORD": "",  # Will be generated
            "MONGO_INITDB_DATABASE": "appdb",
        },
        "redis": {
            "REDIS_PASSWORD": "",  # Will be generated
        },
    }

    @staticmethod
    def create_database_service(
        tool_name: str,
        db_type: str,
        version: str | None = None,
    ) -> DatabaseService:
        """
        Create a dedicated database service for a tool.

        Args:
            tool_name: Name of the tool (e.g., "taiga")
            db_type: Database type (e.g., "postgres", "mysql")
            version: Optional database version (uses default if not provided)

        Returns:
            DatabaseService instance

        Raises:
            ValueError: If database type is not supported
        """
        db_type = db_type.lower()
        if db_type not in IsolationStrategy.DEFAULT_VERSIONS:
            raise ValueError(
                f"Unsupported database type: {db_type}. "
                f"Supported types: {', '.join(IsolationStrategy.DEFAULT_VERSIONS.keys())}"
            )

        # Normalize tool name to enforce naming convention
        normalized_tool_name = tool_name.lower().replace("_", "-")

        db_version = version or IsolationStrategy.DEFAULT_VERSIONS[db_type]
        db_name = f"{normalized_tool_name}-db"
        volume_name = f"{normalized_tool_name}-db-data"
        mount_path = IsolationStrategy.MOUNT_PATHS[db_type]
        env_vars = IsolationStrategy.REQUIRED_ENV_VARS[db_type].copy()

        return DatabaseService(
            name=db_name,
            tool_name=normalized_tool_name,
            db_type=db_type,
            version=db_version,
            volume_name=volume_name,
            mount_path=mount_path,
            env_vars=env_vars,
        )

    @staticmethod
    def get_connection_env_vars(db_service: DatabaseService) -> dict[str, str]:
        """
        Get environment variables for connecting to the database.

        These are the env vars that the main tool needs to connect to its DB.

        Args:
            db_service: The database service

        Returns:
            Dictionary of connection environment variables
        """
        db_type = db_service.db_type
        db_host = db_service.name

        if db_type == "postgres":
            return {
                "POSTGRES_HOST": db_host,
                "POSTGRES_PORT": "5432",
                "POSTGRES_USER": db_service.env_vars["POSTGRES_USER"],
                "POSTGRES_PASSWORD": db_service.env_vars["POSTGRES_PASSWORD"],
                "POSTGRES_DB": db_service.env_vars["POSTGRES_DB"],
            }
        elif db_type in ("mysql", "mariadb"):
            return {
                "MYSQL_HOST": db_host,
                "MYSQL_PORT": "3306",
                "MYSQL_USER": db_service.env_vars["MYSQL_USER"],
                "MYSQL_PASSWORD": db_service.env_vars["MYSQL_PASSWORD"],
                "MYSQL_DATABASE": db_service.env_vars["MYSQL_DATABASE"],
            }
        elif db_type == "mongodb":
            return {
                "MONGO_HOST": db_host,
                "MONGO_PORT": "27017",
                "MONGO_USER": db_service.env_vars["MONGO_INITDB_ROOT_USERNAME"],
                "MONGO_PASSWORD": db_service.env_vars["MONGO_INITDB_ROOT_PASSWORD"],
                "MONGO_DATABASE": db_service.env_vars["MONGO_INITDB_DATABASE"],
            }
        elif db_type == "redis":
            return {
                "REDIS_HOST": db_host,
                "REDIS_PORT": "6379",
                "REDIS_PASSWORD": db_service.env_vars["REDIS_PASSWORD"],
            }

        return {}

    @staticmethod
    def enforce_naming_convention(tool_name: str) -> str:
        """
        Enforce the naming convention for database services.

        Args:
            tool_name: Name of the tool

        Returns:
            Database service name following convention: {tool-name}-db
        """
        # Ensure lowercase and replace underscores with hyphens
        tool_name = tool_name.lower().replace("_", "-")
        return f"{tool_name}-db"

    @staticmethod
    def is_database_service(service_name: str) -> bool:
        """
        Check if a service name follows the database naming convention.

        Args:
            service_name: Name of the service

        Returns:
            True if this is a database service
        """
        return service_name.endswith("-db")
