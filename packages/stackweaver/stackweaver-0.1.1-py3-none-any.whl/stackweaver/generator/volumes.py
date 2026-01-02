"""
Volume Management for StackWeaver.

Manages persistent volumes for services to ensure data survives container restarts.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VolumeDefinition:
    """Represents a Docker volume definition."""

    name: str  # Volume name (e.g., "taiga-data")
    driver: str = "local"  # Volume driver
    driver_opts: dict[str, str] = field(default_factory=dict)  # Driver options
    labels: dict[str, str] = field(default_factory=dict)  # Volume labels

    def to_dict(self) -> dict[str, Any]:
        """Convert to docker-compose volumes format."""
        result: dict[str, Any] = {"driver": self.driver}

        if self.driver_opts:
            result["driver_opts"] = self.driver_opts

        if self.labels:
            result["labels"] = self.labels

        return result


@dataclass
class VolumeMount:
    """Represents a volume mount in a service."""

    volume_name: str  # Name of the volume to mount
    mount_path: str  # Path inside container
    read_only: bool = False  # Whether mount is read-only

    def to_string(self) -> str:
        """Convert to docker-compose volume mount format."""
        mount_str = f"{self.volume_name}:{self.mount_path}"
        if self.read_only:
            mount_str += ":ro"
        return mount_str


class VolumeManager:
    """Manages volume definitions and mounts for a stack."""

    # Default naming convention
    DATA_SUFFIX = "-data"
    DB_SUFFIX = "-db-data"

    def __init__(self) -> None:
        """Initialize volume manager."""
        self._volumes: dict[str, VolumeDefinition] = {}

    def add_volume(self, definition: VolumeDefinition) -> None:
        """
        Add a volume definition to the manager.

        Args:
            definition: VolumeDefinition to add
        """
        self._volumes[definition.name] = definition

    def create_service_volume(
        self,
        service_name: str,
        mount_path: str,
        read_only: bool = False,
    ) -> VolumeMount:
        """
        Create a data volume for a service.

        Follows naming convention: {service-name}-data

        Args:
            service_name: Name of the service
            mount_path: Path to mount volume inside container
            read_only: Whether the mount should be read-only

        Returns:
            VolumeMount instance
        """
        volume_name = self.get_service_volume_name(service_name)

        # Ensure volume is registered
        if volume_name not in self._volumes:
            self.add_volume(VolumeDefinition(name=volume_name))

        return VolumeMount(volume_name=volume_name, mount_path=mount_path, read_only=read_only)

    def create_database_volume(
        self,
        tool_name: str,
        mount_path: str,
    ) -> VolumeMount:
        """
        Create a database volume for a tool.

        Follows naming convention: {tool-name}-db-data

        Args:
            tool_name: Name of the tool
            mount_path: Database data directory path

        Returns:
            VolumeMount instance
        """
        volume_name = self.get_database_volume_name(tool_name)

        # Ensure volume is registered
        if volume_name not in self._volumes:
            self.add_volume(VolumeDefinition(name=volume_name))

        return VolumeMount(volume_name=volume_name, mount_path=mount_path, read_only=False)

    @staticmethod
    def get_service_volume_name(service_name: str) -> str:
        """
        Get the volume name for a service following naming convention.

        Args:
            service_name: Name of the service

        Returns:
            Volume name: {service-name}-data
        """
        # Normalize service name
        normalized = service_name.lower().replace("_", "-")
        return f"{normalized}{VolumeManager.DATA_SUFFIX}"

    @staticmethod
    def get_database_volume_name(tool_name: str) -> str:
        """
        Get the database volume name for a tool following naming convention.

        Args:
            tool_name: Name of the tool

        Returns:
            Volume name: {tool-name}-db-data
        """
        # Normalize tool name
        normalized = tool_name.lower().replace("_", "-")
        return f"{normalized}{VolumeManager.DB_SUFFIX}"

    def get_all_volumes(self) -> dict[str, VolumeDefinition]:
        """
        Get all registered volumes.

        Returns:
            Dictionary of volume name to VolumeDefinition
        """
        return self._volumes.copy()

    def get_volumes_section(self) -> dict[str, Any]:
        """
        Get the docker-compose volumes section.

        Returns:
            Dictionary suitable for docker-compose.yml volumes section
        """
        return {name: vol.to_dict() for name, vol in self._volumes.items()}

    def has_volume(self, volume_name: str) -> bool:
        """
        Check if a volume is registered.

        Args:
            volume_name: Name of the volume

        Returns:
            True if volume exists
        """
        return volume_name in self._volumes

    def clear(self) -> None:
        """Clear all registered volumes."""
        self._volumes.clear()

    @staticmethod
    def validate_mount_path(mount_path: str) -> bool:
        """
        Validate that a mount path is absolute.

        Args:
            mount_path: Path to validate

        Returns:
            True if valid absolute path

        Raises:
            ValueError: If path is not absolute
        """
        if not mount_path.startswith("/"):
            raise ValueError(f"Mount path must be absolute: {mount_path}")
        return True

    @staticmethod
    def is_database_volume(volume_name: str) -> bool:
        """
        Check if a volume name follows database naming convention.

        Args:
            volume_name: Name of the volume

        Returns:
            True if this is a database volume
        """
        return volume_name.endswith(VolumeManager.DB_SUFFIX)

    @staticmethod
    def is_service_volume(volume_name: str) -> bool:
        """
        Check if a volume name follows service data naming convention.

        Args:
            volume_name: Name of the volume

        Returns:
            True if this is a service data volume
        """
        return volume_name.endswith(
            VolumeManager.DATA_SUFFIX
        ) and not VolumeManager.is_database_volume(volume_name)
