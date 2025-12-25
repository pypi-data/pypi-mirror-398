"""Base container manager for managing container lifecycle."""

import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import Any

import docker

from podkit.backends.base import BackendInterface
from podkit.core.models import ContainerConfig, ContainerStatus, ProcessResult
from podkit.utils.paths import (
    container_to_host_path,
    get_workspace_path,
    host_to_container_path,
)


class BaseContainerManager(ABC):
    """
    Base container manager that works with any backend.

    Projects extend this class and inject their chosen backend.
    """

    def __init__(
        self,
        backend: BackendInterface,
        container_prefix: str,
        workspace_base: Path,
    ):
        """
        Initialize container manager.

        Args:
            backend: Backend implementation (Docker, K8s, etc.).
            container_prefix: Prefix for container names (e.g., "sandbox", "biomni").
            workspace_base: Base workspace directory for all sessions.
        """
        self.backend = backend
        self.container_prefix = container_prefix
        self.workspace_base = Path(workspace_base)
        self.lock = Lock()
        self.containers: dict[str, str] = {}  # {workload_id: workload_name}

        # Connect to backend
        self.backend.connect()

    def create_container(
        self,
        user_id: str,
        session_id: str,
        config: ContainerConfig,
    ) -> tuple[str, str]:
        """
        Create a new container.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            config: Container configuration.

        Returns:
            Tuple of (container_id, container_name).

        Raises:
            RuntimeError: If container creation fails.
        """
        # Generate container name
        user_session_slug = "-".join(re.sub(r"[^a-z0-9]", "", _id.lower()) for _id in (session_id, user_id))
        container_name = f"{self.container_prefix}-{user_session_slug}-{uuid.uuid4().hex[:4]}"

        # Get project-specific mounts
        mounts = self.get_mounts(user_id, session_id, config)

        # Add labels for session recovery
        labels = {
            "podkit.user_id": user_id,
            "podkit.session_id": session_id,
            "podkit.manager": self.container_prefix,
        }

        # Create via backend with labels
        container_id = self.backend.create_workload(
            name=container_name,
            config=config,
            mounts=mounts,
            labels=labels,
        )

        with self.lock:
            self.containers[container_id] = container_name

        return container_id, container_name

    @abstractmethod
    def get_mounts(
        self,
        user_id: str,
        session_id: str,
        config: ContainerConfig,
    ) -> list[dict[str, Any]]:
        """
        Get volume mounts for container.

        Project-specific implementation (sandbox vs biomni have different needs).

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            config: Container configuration.

        Returns:
            List of mount specifications in Docker format.
        """
        ...

    def start_container(self, container_id: str) -> None:
        """
        Start a container.

        Args:
            container_id: ID of the container to start.

        Raises:
            RuntimeError: If container start fails.
        """
        self.backend.start_workload(container_id)

    def remove_container(self, container_id: str) -> None:
        """
        Remove a container.

        Args:
            container_id: ID of the container to remove.

        Raises:
            RuntimeError: If container removal fails.
        """
        with self.lock:
            self.backend.remove_workload(container_id)
            if container_id in self.containers:
                del self.containers[container_id]

    def execute_command(
        self,
        container_id: str,
        command: str | list[str],
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> ProcessResult:
        """
        Execute command in container.

        Args:
            container_id: ID of the container.
            command: Command to execute.
            working_dir: Working directory for command execution.
            environment: Environment variables.
            timeout: Timeout in seconds.

        Returns:
            ProcessResult with exit code and output.

        Raises:
            RuntimeError: If command execution fails.
        """
        return self.backend.execute_command(
            workload_id=container_id,
            command=command,
            working_dir=working_dir,
            environment=environment,
            timeout=timeout,
        )

    def get_container_status(self, container_id: str) -> ContainerStatus:
        """
        Get container status.

        Args:
            container_id: ID of the container.

        Returns:
            Current container status.
        """
        return self.backend.get_workload_status(container_id)

    def to_host_path(
        self,
        container_path: Path,
        user_id: str,
        session_id: str,
    ) -> Path:
        """
        Convert a container path to a host path.

        Args:
            container_path: Path inside the container.
            user_id: User identifier.
            session_id: Session identifier.

        Returns:
            Path on the host filesystem.

        Raises:
            ValueError: If path conversion fails.
        """
        workspace_path = get_workspace_path(self.workspace_base, user_id, session_id)
        return container_to_host_path(
            container_path=Path(container_path),
            workspace_base=workspace_path,
            container_workspace=Path("/workspace"),
        )

    def to_container_path(
        self,
        host_path: Path,
        user_id: str,
        session_id: str,
    ) -> Path:
        """
        Convert a host path to a container path.

        Args:
            host_path: Path on the host filesystem.
            user_id: User identifier.
            session_id: Session identifier.

        Returns:
            Path inside the container.

        Raises:
            ValueError: If path conversion fails.
        """
        workspace_path = get_workspace_path(self.workspace_base, user_id, session_id)
        return host_to_container_path(
            host_path=Path(host_path),
            workspace_base=workspace_path,
            container_workspace=Path("/workspace"),
        )

    def discover_existing_containers(self) -> list[dict[str, str]]:
        """Discover existing containers managed by this manager.

        Returns:
            List of dicts with keys: container_id, container_name, user_id, session_id
        """
        try:
            # List containers with our prefix and labels
            containers = self.backend.list_workloads(filters={"name": f"{self.container_prefix}-"})

            discovered = []
            for container_info in containers:
                container_id = container_info["id"]

                # Get full container details to access labels

                client = docker.from_env()
                container = client.containers.get(container_id)
                labels = container.labels

                # Extract user_id and session_id from labels
                user_id = labels.get("podkit.user_id")
                session_id = labels.get("podkit.session_id")

                if user_id and session_id:
                    discovered.append(
                        {
                            "container_id": container_id,
                            "container_name": container_info["name"],
                            "user_id": user_id,
                            "session_id": session_id,
                        }
                    )

            return discovered
        except Exception:  # pylint: disable=broad-except
            # If discovery fails, return empty list
            return []

    def cleanup_all(self) -> None:
        """Clean up all tracked containers."""
        with self.lock:
            container_ids = list(self.containers.keys())

        for container_id in container_ids:
            try:
                self.remove_container(container_id)
            except Exception:  # pylint: disable=broad-except
                # Continue cleanup even if one fails
                pass


class TestContainerManager(BaseContainerManager):
    """
    Test implementation of container manager.

    This is used for integration tests and provides a simple mount strategy.
    """

    def __init__(
        self,
        backend: BackendInterface,
        container_prefix: str,
        workspace_base: Path,
        workspace_base_host: Path | None = None,
    ):
        """
        Initialize test container manager.

        Args:
            backend: Backend implementation.
            container_prefix: Prefix for container names.
            workspace_base: Workspace path inside test runner container.
            workspace_base_host: Actual host path that Docker can access (for nested containers).
        """
        super().__init__(backend, container_prefix, workspace_base)
        # For nested Docker containers, we need the actual host path
        self.workspace_base_host = workspace_base_host or workspace_base

    def get_mounts(
        self,
        user_id: str,
        session_id: str,
        config: ContainerConfig,
    ) -> list[dict[str, Any]]:
        """
        Get volume mounts for test containers.

        Creates a workspace mount for the user's session.

        Note: For nested Docker containers, we need to use paths that Docker
        on the host can access. The workspace_base path is already accessible
        to Docker since it's mounted in the test runner container.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            config: Container configuration.

        Returns:
            List of mount specifications.
        """
        workspace_path = get_workspace_path(self.workspace_base, user_id, session_id)

        workspace_path.mkdir(parents=True, exist_ok=True)

        # For Docker mounts, we need to use the host path
        # Calculate the relative path from workspace_base
        relative_path = workspace_path.relative_to(self.workspace_base)

        # Construct the host path that Docker can access
        host_workspace_path = self.workspace_base_host / relative_path

        # Create mount specification using the actual host path
        mount = {
            "Type": "bind",
            "Source": str(host_workspace_path),
            "Target": "/workspace",
        }

        return [mount]
