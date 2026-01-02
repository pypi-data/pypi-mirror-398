"""
State management for StackWeaver deployments.

Persists deployment state to disk for tracking across CLI invocations.
State is stored in .stackweaver/state.json in the stack directory.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from stackweaver.core.errors import StackWeaverError


class StackStatus(str, Enum):
    """Deployment status of a stack."""

    RUNNING = "running"
    STOPPED = "stopped"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class DeploymentState(BaseModel):
    """
    Deployment state schema.

    Tracks the current state of a deployed stack.
    """

    model_config = ConfigDict(use_enum_values=True)

    deployed_services: list[str] = Field(
        default_factory=list,
        description="List of service names that were deployed",
    )
    deployment_time: str = Field(
        description="Deployment timestamp in ISO 8601 format",
    )
    docker_compose_path: str = Field(
        description="Path to docker-compose.yml file",
    )
    stack_status: StackStatus = Field(
        default=StackStatus.UNKNOWN,
        description="Current status of the stack",
    )
    project_name: str = Field(
        description="Docker Compose project name",
    )
    stack_directory: str = Field(
        description="Directory containing the stack",
    )


class StateManagerError(StackWeaverError):
    """Error in state management."""

    def __init__(self, operation: str, details: str | None = None) -> None:
        super().__init__(
            message=f"State {operation} failed",
            cause="State file may be corrupted or inaccessible",
            fix="Check state file permissions or clear state with 'stackweaver rollback'",
            details=details,
        )


class StateManager:
    """
    Manages deployment state persistence.

    Saves and loads deployment state to/from .stackweaver/state.json
    in the stack directory.

    Example:
        state_manager = StateManager(stack_dir)
        state_manager.save_state(
            deployed_services=["espocrm", "postgres"],
            docker_compose_path="/path/to/docker-compose.yml",
            stack_status=StackStatus.RUNNING,
            project_name="my-stack"
        )
        state = state_manager.load_state()
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Initialize StateManager.

        Args:
            stack_dir: Directory containing the stack
        """
        self.stack_dir = stack_dir.resolve()
        self.state_dir = self.stack_dir / ".stackweaver"
        self.state_file = self.state_dir / "state.json"

    def _ensure_state_dir(self) -> None:
        """Create state directory if it doesn't exist."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_state(
        self,
        deployed_services: list[str],
        docker_compose_path: str,
        stack_status: StackStatus,
        project_name: str,
    ) -> None:
        """
        Save deployment state to disk.

        Args:
            deployed_services: List of service names deployed
            docker_compose_path: Path to docker-compose.yml
            stack_status: Current status of the stack
            project_name: Docker Compose project name

        Raises:
            StateManagerError: If state cannot be saved
        """
        try:
            self._ensure_state_dir()

            from datetime import UTC

            state = DeploymentState(
                deployed_services=deployed_services,
                deployment_time=datetime.now(UTC).isoformat(),
                docker_compose_path=docker_compose_path,
                stack_status=stack_status,
                project_name=project_name,
                stack_directory=str(self.stack_dir),
            )

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state.model_dump(), f, indent=2)

        except Exception as e:
            raise StateManagerError("save", details=str(e)) from e

    def load_state(self) -> DeploymentState | None:
        """
        Load deployment state from disk.

        Returns:
            DeploymentState if state file exists and is valid, None otherwise

        Raises:
            StateManagerError: If state file is corrupted
        """
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, encoding="utf-8") as f:
                data = json.load(f)

            return DeploymentState(**data)

        except json.JSONDecodeError as e:
            raise StateManagerError("load", details=f"Invalid JSON: {e}") from e
        except Exception as e:
            raise StateManagerError("load", details=str(e)) from e

    def clear_state(self) -> None:
        """
        Clear deployment state.

        Removes the state file if it exists.
        """
        if self.state_file.exists():
            try:
                self.state_file.unlink()
            except Exception as e:
                raise StateManagerError("clear", details=str(e)) from e

    def update_status(self, new_status: StackStatus) -> None:
        """
        Update the stack status in existing state.

        Args:
            new_status: New status to set

        Raises:
            StateManagerError: If state doesn't exist or cannot be updated
        """
        state = self.load_state()
        if state is None:
            raise StateManagerError(
                "update",
                details="No state file found. Deploy stack first.",
            )

        try:
            state.stack_status = new_status
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state.model_dump(), f, indent=2)

        except Exception as e:
            raise StateManagerError("update", details=str(e)) from e

    def has_state(self) -> bool:
        """
        Check if state file exists.

        Returns:
            True if state file exists, False otherwise
        """
        return self.state_file.exists()

    def get_state_file_path(self) -> Path:
        """
        Get the path to the state file.

        Returns:
            Path to state.json
        """
        return self.state_file
