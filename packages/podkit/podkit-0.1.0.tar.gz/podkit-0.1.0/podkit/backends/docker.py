"""Docker implementation of the backend interface."""

import logging
from pathlib import Path
from typing import Any

import docker
from docker.errors import DockerException, ImageNotFound, NotFound

from podkit.backends.base import BackendInterface
from podkit.core.models import ContainerConfig, ContainerStatus, ProcessResult

logger = logging.getLogger("podkit")


class DockerBackend(BackendInterface):
    """Docker implementation of the backend interface."""

    def __init__(self):
        """Initialize Docker backend."""
        self.client = None

    def connect(self) -> None:
        """Initialize Docker client and verify connection."""
        try:
            self.client = docker.from_env()
            self.client.ping()
        except DockerException as e:
            raise RuntimeError(
                f"Docker is not running or not accessible: {e}.\n"
                "Tips: 1) Check that docker is running\n"
                "2) Check if '/var/run/docker.sock' socket is available"
            ) from e

    def _ensure_image_available(self, image_name: str) -> None:
        """Ensure Docker image is available locally, pull if necessary.

        Args:
            image_name: Name of the Docker image.

        Raises:
            RuntimeError: If image cannot be pulled.
        """
        try:
            # Check if image exists locally
            self.client.images.get(image_name)
            logger.debug(f"Image {image_name} found locally")
        except ImageNotFound:
            logger.warning(f"Image {image_name} not found locally, pulling...")
            try:
                self.client.images.pull(image_name)
                logger.info(f"Successfully pulled image: {image_name}")
            except DockerException as e:
                raise RuntimeError(
                    f"Image '{image_name}' not found locally and failed to pull: {e}\n"
                    f"Please pull it manually: docker pull {image_name}"
                ) from e

    def create_workload(
        self,
        name: str,
        config: ContainerConfig,
        mounts: list[dict[str, Any]],
        **kwargs,
    ) -> str:
        """
        Create a Docker container.

        Args:
            name: Container name.
            config: Container configuration.
            mounts: Volume mount specifications.
            **kwargs: Additional Docker-specific options (can include 'labels').

        Returns:
            Container ID.

        Raises:
            RuntimeError: If container creation fails.
        """
        try:
            self._ensure_image_available(config.image)

            create_params = {
                "image": config.image,
                "name": name,
                "detach": True,
                "mounts": mounts,
                "environment": config.environment,
                "working_dir": config.working_dir,
                "cpu_quota": int(config.cpu_limit * 100000),  # Docker uses CPU quota in microseconds
                "mem_limit": config.memory_limit,
                "user": config.user,
                **kwargs,
            }

            # Override entrypoint if specified (None means use image default)
            if config.entrypoint is not None:
                create_params["entrypoint"] = config.entrypoint
                # If entrypoint is empty list and no command specified, keep container alive with sleep
                if config.entrypoint == [] and "command" not in kwargs:
                    create_params["command"] = ["sleep", "infinity"]

            container = self.client.containers.create(**create_params)
            return container.id
        except DockerException as e:
            raise RuntimeError(f"Failed to create container: {e}") from e

    def start_workload(self, workload_id: str) -> None:
        """
        Start a Docker container.

        Args:
            workload_id: Container ID.

        Raises:
            RuntimeError: If container start fails.
        """
        try:
            container = self.client.containers.get(workload_id)
            container.start()
        except DockerException as e:
            raise RuntimeError(f"Failed to start container: {e}") from e

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
        Execute command in Docker container.

        Args:
            workload_id: Container ID.
            command: Command to execute.
            working_dir: Working directory.
            environment: Environment variables.
            timeout: Timeout in seconds (not implemented yet).
            stream_callback: Streaming callback (not implemented yet).

        Returns:
            ProcessResult with exit code and output.

        Raises:
            RuntimeError: If command execution fails.
        """
        try:
            container = self.client.containers.get(workload_id)

            exec_kwargs = {
                "cmd": command,
                "stdout": True,
                "stderr": True,
                "stdin": False,
            }

            if working_dir:
                exec_kwargs["workdir"] = str(working_dir)
            if environment:
                exec_kwargs["environment"] = environment

            # Execute the command
            result = container.exec_run(**exec_kwargs)

            return ProcessResult(
                exit_code=result.exit_code,
                stdout=result.output.decode("utf-8", errors="replace"),
                stderr="",  # Docker Python SDK doesn't separate stdout and stderr
            )
        except DockerException as e:
            raise RuntimeError(f"Failed to execute command: {e}") from e

    def remove_workload(self, workload_id: str, force: bool = True) -> None:
        """
        Remove a Docker container.

        Args:
            workload_id: Container ID.
            force: Force removal even if running.

        Raises:
            RuntimeError: If container removal fails.
        """
        try:
            container = self.client.containers.get(workload_id)
            if container.status == "running" and force:
                container.stop(timeout=1)
            container.remove()
        except NotFound:
            # Container already removed, that's fine
            pass
        except DockerException as e:
            raise RuntimeError(f"Failed to remove container: {e}") from e

    def get_workload_status(self, workload_id: str) -> ContainerStatus:
        """
        Get Docker container status.

        Args:
            workload_id: Container ID.

        Returns:
            Container status.
        """
        try:
            container = self.client.containers.get(workload_id)
            if container.status == "running":
                return ContainerStatus.RUNNING
            if container.status == "created":
                return ContainerStatus.CREATING
            return ContainerStatus.STOPPED
        except NotFound:
            return ContainerStatus.ERROR
        except DockerException:
            return ContainerStatus.ERROR

    def list_workloads(self, filters: dict[str, str] | None = None) -> list[dict]:
        """
        List Docker containers.

        Args:
            filters: Filter criteria.

        Returns:
            List of container information dicts.

        Raises:
            RuntimeError: If listing fails.
        """
        try:
            containers = self.client.containers.list(all=True, filters=filters or {})
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "created": c.attrs["Created"],
                }
                for c in containers
            ]
        except DockerException as e:
            raise RuntimeError(f"Failed to list containers: {e}") from e
