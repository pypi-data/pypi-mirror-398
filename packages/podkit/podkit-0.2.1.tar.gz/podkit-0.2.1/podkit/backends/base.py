"""Abstract base interface for container runtime backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from podkit.core.models import ContainerConfig, ContainerStatus, ProcessResult


class BackendInterface(ABC):
    """
    Abstract interface for container runtime backends.

    This abstraction allows the library to work with different container runtimes
    (Docker, Kubernetes, etc.) without changing business logic.

    Design principle: All container lifecycle operations go through this interface.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Initialize connection to the backend.

        Raises:
            RuntimeError: If connection fails.
        """
        ...

    @abstractmethod
    def create_workload(
        self,
        name: str,
        config: ContainerConfig,
        mounts: list[dict[str, Any]],
        **kwargs,
    ) -> str:
        """
        Create a workload unit (container, pod, etc.).

        Args:
            name: Unique workload name.
            config: Workload configuration.
            mounts: Volume mount specifications.
            **kwargs: Backend-specific options.

        Returns:
            Workload ID (container ID, pod name, etc.).

        Raises:
            RuntimeError: If creation fails.
        """
        ...

    @abstractmethod
    def start_workload(self, workload_id: str) -> None:
        """
        Start a workload.

        Args:
            workload_id: ID of the workload to start.

        Raises:
            RuntimeError: If start fails.
        """
        ...

    @abstractmethod
    def execute_command(
        self,
        workload_id: str,
        command: str | list[str],
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
        timeout: int | None = None,
        stream_callback: Any = None,
    ) -> ProcessResult:
        """
        Execute command in workload.

        Args:
            workload_id: ID of the workload.
            command: Command to execute (string or list of strings).
            working_dir: Working directory for command execution.
            environment: Environment variables for the command.
            timeout: Timeout in seconds.
            stream_callback: Optional callback for streaming output.

        Returns:
            ProcessResult with exit code and output.

        Raises:
            RuntimeError: If execution fails.
        """
        ...

    @abstractmethod
    def remove_workload(self, workload_id: str, force: bool = True) -> None:
        """
        Remove a workload.

        Args:
            workload_id: ID of the workload to remove.
            force: Force removal even if running.

        Raises:
            RuntimeError: If removal fails.
        """
        ...

    @abstractmethod
    def get_workload_status(self, workload_id: str) -> ContainerStatus:
        """
        Get workload status.

        Args:
            workload_id: ID of the workload.

        Returns:
            Current status.

        Raises:
            RuntimeError: If status check fails.
        """
        ...

    @abstractmethod
    def list_workloads(self, filters: dict[str, str] | None = None) -> list[dict]:
        """
        List workloads matching filters.

        Args:
            filters: Filter criteria (e.g., {"name": "prefix-*"}).

        Returns:
            List of workload information dicts.

        Raises:
            RuntimeError: If listing fails.
        """
        ...
